import reframe as rfm

@rfm.simple_test
class GmshInstallTest(rfm.RunOnlyRegressionTest):
    valid_systems = ['*']
    valid_prog_environs = ['builtin']
    
    @run_before('run')
    def check_gmsh(self):
        self.executable = 'which gmsh'
    
    @run_before('sanity')
    def set_sanity(self):
        self.sanity_patterns = sn.assert_found(r'gmsh', self.stdout)
