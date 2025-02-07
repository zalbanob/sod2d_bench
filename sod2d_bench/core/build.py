import os
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import run_after, run_before, sanity_function, parameter
from reframe.core.exceptions import SanityError
from sod2d_bench.core.base_params import Sod2dBaseParams

@rfm.simple_test
class Sod2dBuildTest(rfm.CompileOnlyRegressionTest):
    branch     = parameter(['master', 'bsc-epicure-opt'])
    precision  = parameter(['single'])  # 'double'
    p_order    = parameter([3])  # 3, 4, 5

    use_gpu    = parameter([True, False])
    build_type = parameter(['main', 'tools'])
    
    # Precision parameters with validation
    rp     = parameter([4])   # 4=single, 8=double
    rp_vtk = parameter([8])
    rp_avg = parameter([8])

    valid_prog_environs = ['builtin']
    valid_systems       = ['*']
    build_system        = 'CMake'
    sourcesdir          = None

    @run_after('init')
    def setup_build_config(self):
        # Disable invalid GPU+tools combinations
        if self.use_gpu and self.build_type == 'tools':
            self.valid_prog_environs = []

    @run_before('compile')
    def configure_build(self):
        # Retrieve the compiler settings from the environment, with defaults.
        c_compiler = os.environ.get("CC", "nvc")
        cuda_compiler = os.environ.get("CMAKE_CUDA_COMPILER", "nvcc")

        # Base configuration options.
        config_opts = [
            f'-D__PORDER__={self.p_order}',
            f'-D__RP__={self.rp}',
            f'-D__RP_VTK__={self.rp_vtk}',
            f'-D__RP_AVG__={self.rp_avg}',
            '-DTOOL_MESHPART=ON',
            f'-DCMAKE_C_COMPILER={c_compiler}',
            f'-DCMAKE_CUDA_COMPILER={cuda_compiler}'
        ]

        if self.build_type == 'main':
            config_opts += [
                f'-DUSE_GPU={"ON" if self.use_gpu else "OFF"}',
                '-DTOOL_MESHPART=ON' if not self.use_gpu else '-DTOOL_MESHPART=OFF'
            ]
        elif self.build_type == 'tools':
            config_opts += [
                '-DUSE_GPU=OFF',
                '-DTOOL_MESHPART=ON'
            ]

        self.build_system.config_opts = config_opts

    @run_before('compile')
    def clone_repo(self):
        # Clone the repository and update its submodules
        clone_cmd = f'git clone -b {self.branch} --depth=1 https://gitlab.com/bsc_sod2d/sod2d_gitlab'
        update_cmd = 'cd sod2d_gitlab && git submodule update --init --recursive'
        self.prebuild_cmds = [clone_cmd, update_cmd]

        # Set the sources directory to the cloned repository
        self.sourcesdir = os.path.join(self.stagedir, 'sod2d_gitlab')
        os.makedirs(self.sourcesdir, exist_ok=True)

    @run_before('compile')
    def set_build_directory(self):
        # Create a separate build directory for the out-of-source build
        self.builddir = os.path.join(self.stagedir, 'build')
        os.makedirs(self.builddir, exist_ok=True)

        # Explicitly specify the source directory for CMake
        self.build_system.srcdir = self.sourcesdir
        self.build_system.out_of_source_build = True

        # Ensure that CMake is invoked correctly from the build directory
        self.prebuild_cmds += [
            f'cd {self.builddir} && cmake {self.sourcesdir} {" ".join(self.build_system.config_opts)}'
        ]

    @sanity_function
    def validate_build(self):
        binaries = []
        if self.build_type == 'main':
            binaries.append('src/app_sod2d/sod2d')
            if not self.use_gpu:  binaries.append('tool_meshConversorPar/tool_meshConversorPar')
        elif self.build_type == 'tools':
            binaries.append('tool_meshConversorPar/tool_meshConversorPar')
            
        return sn.all([
            sn.assert_true(not sn.contains(self.stderr, r'error:')),
            sn.all(sn.assert_true(os.path.exists(os.path.join(self.builddir, exe))) for exe in binaries),
            sn.assert_true( f'USE_GPU:BOOL={"ON" if self.use_gpu else "OFF"}' in open(os.path.join(self.builddir, 'CMakeCache.txt')).read())
        ])
    @run_before('sanity')
    def validate_precision(self):
        if self.rp_vtk < self.rp or self.rp_avg < self.rp:
            raise SanityError("VTK/avg precision cannot be lower than main precision")
