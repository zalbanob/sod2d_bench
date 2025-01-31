site_configuration = {
    'systems': [
        {
            'name': 'cluster1',
            'descr': 'First HPC Cluster',
            'hostnames': ['login.*cluster1.com', 'compute.*cluster1.com'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'cpu',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'environs': ['sod2d-mesh'],
                    'processor': {'num_cpus': 40, 'num_gpus': 0}
                }
            ]
        },
        {
            'name': 'cluster2',
            'descr': 'Second HPC Cluster with GPUs',
            'hostnames': ['login.*cluster2.edu', 'gpu.*cluster2.edu'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'gpu',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'environs': ['sod2d-mesh'],
                    'processor': {'num_cpus': 16, 'num_gpus': 8}
                }
            ]
        }
    ],
    'environments': [
        {
            'name': 'sod2d-mesh',
            'modules': ['sod2d-mesh-v1', 'mpi'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'systems': ['cluster1']  # Applies to cluster1 only
        },
        {
            'name': 'sod2d-mesh',
            'modules': ['sod2d-mesh-v2', 'cuda', 'intelmpi'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'systems': ['cluster2']  # Applies to cluster2 only
        }
    ]
}