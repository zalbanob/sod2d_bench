import os
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import run_after, run_before, sanity_function
from sod2d_bench.core.base_params import Sod2dBaseParams
from sod2d_bench.core.run import Sod2dSimulationTest

@rfm.simple_test
class TGVAnalysisTest(rfm.RunOnlyRegressionTest):
    branch     = parameter(['master', 'bsc-epicure-opt'])
    precision  = parameter(['single']) #, 'double'
    p_order    = parameter([3]) #, 4, 5
    use_gpu    = parameter([True, False])

    n_elements = parameter([8]) #16
    valid_systems       = ['*']
    valid_prog_environs = ['builtin']
    executable          = 'python3'
    num_tasks           = 1

    @run_after('init')
    def setup_run(self):
        # Depend on two simulation tests with different branches.
        self.depends_on('Sod2dSimulationTest', how_to='by_env',
                        branch="master",  # Reference branch
                        p_order=self.p_order,
                        n_elements=self.n_elements,
                        precision=self.precision)
        self.depends_on('Sod2dSimulationTest', how_to='by_env',
                        branch='bsc-epicure-opt',  # Test branch
                        p_order=self.p_order,
                        n_elements=self.n_elements,
                        precision=self.precision)

    @run_before('run')
    def setup_analysis(self):
        sim = self.getdep('Sod2dSimulationTest')
        self.cur_result = os.path.join(sim.output_dir, 'analysis_cube-1.dat')
        self.ref_result = os.path.join('Reference', 'analysis_cube-1.dat')
        
        self.executable_opts = [
            'check_tgv.py',
            '--current', self.cur_result,
            '--reference', self.ref_result,
            '--tolerance', '1e-4',
            '--abs-tol', '1e-12'
        ]

    @sanity_function 
    def validate_results(self):
        return sn.all([
            sn.assert_found(r'All results match within tolerance', self.stdout),
            sn.assert_eq(sn.count(sn.extractall(r'Mismatch', self.stdout)), 0)
        ])
