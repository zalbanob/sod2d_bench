import reframe as rfm
import reframe.utility.sanity as sn
import os
from sod2d_bench.core.base_test import Sod2dBaseParams 


@rfm.simple_test
class Sod2dSimulationTest(Sod2dBaseParams, rfm.RunOnlyRegressionTest):
    valid_systems       = ['*']
    valid_prog_environs = ['sod2d-mesh']
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
                       build_type='master',
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
        build = self.getdep('Sod2dBuildTest', branch=self.branch, ...)
        self.output_dir = f'results_{self.branch}_p{self.p_order}_ne{self.n_elements}'
        
        self.executable_opts = [
            f'-m {mesh.mesh_prefix}_partitions.hdf',
            f'-o results_{self.branch}_p{self.p_order}_ne{self.n_elements}'
        ]
        #self.variables = {
        #    'OMP_NUM_THREADS': str(self.num_cpus_per_task),
        #}

    @sanity_function
    def validate_run(self):
        return sn.all([
            sn.assert_found(r'Simulation completed successfully', self.stdout),
            sn.assert_exists(f'results_{self.branch}_p{self.p_order}_ne{self.n_elements}/solution.hdf')
        ])
