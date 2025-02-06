import os
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import run_after, run_before, sanity_function, parameter
from sod2d_bench.core.base_params import Sod2dBaseParams
from sod2d_bench.core.build import Sod2dBuildTest
from sod2d_bench.meshes.cube_gen import MeshGenerationTest


@rfm.simple_test
class Sod2dSimulationTest(rfm.RunOnlyRegressionTest):
    branch     = parameter(['master', 'bsc-epicure-opt'])
    precision  = parameter(['single', 'double'])
    p_order    = parameter([3, 4, 5])
    use_gpu    = parameter([True, False])

    valid_systems       = ['*']
    n_elements          = parameter([8, 16, 32]) 
    valid_prog_environs = ['builtin']
    executable          = 'sod2d'
    num_tasks           = 4
    num_tasks_per_node  = 4

    @run_after('init')
    def set_params(self):
        self.rp = 4 if self.precision == 'single' else 8
        self.rp_vtk = self.rp
        self.rp_avg = self.rp

    @run_after('init')
    def set_deps(self):
        self.depends_on('Sod2dBuildTest', 
                        how_to='by_env',
                        branch=self.branch, 
                        p_order=self.p_order,
                        use_gpu=self.use_gpu, 
                        build_type='main',  # Use 'main' as valid build_type
                        rp=self.rp, 
                        rp_vtk=self.rp_vtk, 
                        rp_avg=self.rp_avg)
        self.depends_on('MeshGenerationTest', 
                        how_to='by_env',
                        branch=self.branch, 
                        p_order=self.p_order,
                        n_elements=self.n_elements, 
                        rp=self.rp)

    @run_before('run')
    def setup_run(self):
        build = self.getdep('Sod2dBuildTest')
        mesh  = self.getdep('MeshGenerationTest')
        self.output_dir = f'results_{self.branch}_p{self.p_order}_ne{self.n_elements}'
        
        self.executable_opts = [
            f'-m {mesh.mesh_prefix}_partitions.hdf',
            f'-o results_{self.branch}_p{self.p_order}_ne{self.n_elements}'
        ]
        # Uncomment and set variables if needed:
        # self.variables = {
        #     'OMP_NUM_THREADS': str(self.num_tasks_per_node),
        # }

    @sanity_function
    def validate_run(self):
        return sn.all([
            sn.assert_found(r'Simulation completed successfully', self.stdout),
            sn.assert_exists(
                os.path.join(
                    f'results_{self.branch}_p{self.p_order}_ne{self.n_elements}', 
                    'solution.hdf'
                )
            )
        ])
