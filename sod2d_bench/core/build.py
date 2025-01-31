import reframe as rfm
import reframe.utility.sanity as sn
import os
from sod2d_bench.core.base_test import Sod2dBaseParams 

@rfm.simple_test
class Sod2dBuildTest(Sod2dBaseParams, rfm.CompileOnlyRegressionTest):
    build_type = parameter(['main', 'tools'])
    
    # Precision parameters with validation
    rp     = parameter([4, 8])  # 4=single, 8=double
    rp_vtk = parameter([4, 8])
    rp_avg = parameter([4, 8])

    valid_systems       = ['*']
    valid_prog_environs = ['sod2d-mesh']
    build_system        = 'CMake'
    sourcesdir          = None

    @run_after('init')
    def setup_build_config(self):
        # Disable invalid GPU+tools combinations
        if self.use_gpu and self.build_type == 'tools':
            self.valid_prog_environs = []

    @run_before('compile')
    def configure_build(self):
        # Fixed build directory structure
        self.builddir = os.path.join(
            'build',
            f'branch={self.branch}',
            f'p_order={self.p_order}',
            f'gpu={self.use_gpu}',
            f'build_type={self.build_type}',
            f'rp={self.rp}_vtk={self.rp_vtk}_avg={self.rp_avg}'
        )

        config_opts = [
            f'-D__PORDER__={self.p_order}',
            f'-D__RP__={self.rp}',
            f'-D__RP_VTK__={self.rp_vtk}',
            f'-D__RP_AVG__={self.rp_avg}',
            '-DBUILD_THTOOL=ON'
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
        self.prebuild_cmds = [
            f'git clone -b {self.branch} --depth=1 '
            f'https://gitlab.com/bsc_sod2d/sod2d_gitlab {self.sourcesdir}',
            f'cd {self.sourcesdir} && git submodule update --init --recursive'
        ]

    @sanity_function
    def validate_build(self):
        binaries = []
        if self.build_type == 'main':
            binaries.append('sod2d')
            if not self.use_gpu:
                binaries.append('tool_meshConversorPar')
        elif self.build_type == 'tools':
            binaries.append('tool_meshConversorPar')
            
        return sn.all([
            sn.assert_not_found(r'error:', self.stderr),
            sn.all(sn.assert_exists(os.path.join(self.builddir, exe)) 
                   for exe in binaries),
            sn.assert_found(rf'USE_GPU:BOOL={"ON" if self.use_gpu else "OFF"}',
                           os.path.join(self.builddir, 'CMakeCache.txt'))
        ])

    @run_before('sanity')
    def validate_precision(self):
        if self.rp_vtk < self.rp or self.rp_avg < self.rp:
            raise SanityError("VTK/avg precision cannot be lower than main precision")
