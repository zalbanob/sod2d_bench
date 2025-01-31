import reframe as rfm

@rfm.simple_test
class Sod2dBaseParams(rfm.RegressionTest):
    branch     = parameter(['master', 'bsc-epicure-opt'])
    precision  = parameter(['single', 'double'])
    p_order    = parameter([3, 4, 5])
    use_gpu    = parameter([True, False])
