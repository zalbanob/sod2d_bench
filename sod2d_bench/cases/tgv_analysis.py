from sod2d_bench.core.base_test import Sod2dBaseParams 

@rfm.simple_test
class TGVAnalysisTest(Sod2dBaseParams, rfm.RunOnlyRegressionTest):
    n_elements = parameter([8, 16])
    valid_systems       = ['*']
    valid_prog_environs = ['sod2d-mesh']
    executable          = 'python3'
    num_tasks           = 1

    @run_after('init')
    def setup_run(self):
        self.depends_on('Sod2dSimulationTest', how_to='by_env',
                    branch='main',  # Reference branch
                    p_order=self.p_order,
                    n_elements=self.n_elements,
                    precision=self.precision)
        self.depends_on('Sod2dSimulationTest', how_to='by_env',
                    branch='optimized',  # Test branch
                    p_order=self.p_order,
                    n_elements=self.n_elements,
                    precision=self.precision)

    @run_before('run')
    def setup_analysis(self):
        sim = self.getdep('Sod2dSimulationTest')
        self.cur_result = os.path.join(sim.output_dir, f'analysis_cube-1.dat')
        self.ref_result = os.path.join('Reference', f'analysis_cube-1.dat')
        
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
