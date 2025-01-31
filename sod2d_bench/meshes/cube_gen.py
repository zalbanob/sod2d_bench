import reframe as rfm
import reframe.utility.sanity as sn
import numpy as np


@rfm.simple_test
class MeshGenerationTest(rfm.RunOnlyRegressionTest):
    side_len   = parameter([2*np.pi])              # the side length of the cube
    n_elements = parameter([8, 16, 32])
    rp         = parameter([4, 8])
    rp_vtk     = parameter([4, 8])
    rp_avg     = parameter([4, 8])
    num_partitions = parameter([1])                    # Partition counts

    valid_systems       = ['*']
    valid_prog_environs = ['sod2d-mesh']
    executable          = 'bash'    
    # System configuration
    valid_systems       = ['*']
    valid_prog_environs = ['builtin']
    executable          = 'bash'
    prerun_cmds         = ['module load gmsh',  'module load python']


    @run_after('init')
    def set_dependencies(self):
        self.depends_on('GmshInstallTest',how_to='by_env')
        self.depends_on('PythonDepsTest', how_to='by_env')
        self.depends_on('Sod2dBuildTest', how_to='by_env',
                       branch=self.branch, p_order=self.p_order,
                       use_gpu=False, build_type='tools' if self.use_gpu else 'master',
                       rp=self.rp, rp_vtk=self.rp_vtk, rp_avg=self.rp_avg)

     @run_after('init')
    def set_output_dir(self):
        param_str       = f'L{self.side_len}_ne{self.n_elements}_o{self.p_order}_np{self.num_partitions}'
        self.output_dir = f'meshes/{self.branch}/p{self.p_order}/ne{self.n_elements}'

    
    @run_before('run')
    def prepare_script(self):
        build = self.getdep('Sod2dBuildTest', build_type='tools' if self.use_gpu else build_type='main')

        self.mesh_tool   = os.path.join(build.builddir  , 'tool_meshConversorPar')
        self.gmsh_script = os.path.join(build.sourcesdir, 'utils/gmsh2sod2d/gmsh2sod2d.py')
        
        # Generate mesh generation script
        self.mesh_prefix = f"mesh_n{self.side_len}_n{self.n_elements}_o{self.p_order}"
        self.geo_script  = f'{self.mesh_prefix}.geo'
        self.msh_file    = f'{self.mesh_prefix}.msh'
        self.config_file = f'{self.mesh_prefix}_config.dat'

        os.makedirs(self.output_dir, exist_ok=True)
        self.geo_path = os.path.join(self.output_dir, self.geo_script)
        self.msh_path = os.path.join(self.output_dir, self.msh_file)
        self.config_path = os.path.join(self.output_dir, self.config_file)
        
        geo_content = f'''pi = 3.14159265;
                        n = {self.n_elements};
                        h = {self.side_len}/n;
                        Point(1) = {{0,0,0,h}};
                        Point(2) = {{{self.side_len},0,0,h}};
                        Point(3) = {{{self.side_len},{self.side_len},0.0,h}};
                        Point(4) = {{0.0,{self.side_len},0.0,h}};

                        Line(1) = {{1,2}};
                        Line(2) = {{2,3}};
                        Line(3) = {{3,4}};
                        Line(4) = {{4,1}};

                        Line Loop(1) = {{1,2,3,4}};
                        Surface(1)   = {{1}};

                        Transfinite Surface {{1}};
                        Recombine Surface   {{1}};

                        Extrude {{0, 0, {self.side_len}}} {{
                            Surface{{1}}; Layers{{n}}; Recombine;
                        }}

                        //+ Set every surface to periodic, using surf(1) as master
                        Physical Surface("Periodic") = {{21,13,17,25,26,1}};

                        //+ Set the fluid region
                        Physical Volume("fluid") = {{1}};

                        //+ Set the output mesh file version
                        Mesh.MshFileVersion = 2.2;

                        //+ Options controlling mesh generation
                        Mesh.ElementOrder = {self.p_order}; //+ Set desired element order 
                        Mesh 3;                                //+ Volumetric mesh

                        //+ Generate the periodicity between surface pairs
                        Periodic Surface {{17}} = {{25}} Translate {{{self.side_len}, 0, 0}}; // left  & right
                        Periodic Surface {{21}} = {{13}} Translate {{0, {self.side_len}, 0}}; // front & back
                        Periodic Surface {{26}} = {{1}} Translate  {{0, 0, {self.side_len}}}; // top   & bottom
                        '''
        with open(self.geo_script, 'w') as f:
            f.write(geo_content)

        config_content = f'''gmsh_filePath "{self.output_dir}/"
                             gmsh_fileName "{self.mesh_prefix}"
                             mesh_h5_fileName "{self.mesh_prefix}_partitions"
                             num_partitions {self.num_partitions}
                             lineal_output 1
                             eval_mesh_quality 1
                             '''
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        self.executable_opts = [
            '-c',
            f'cd {self.output_dir} && '
            f'gmsh {self.geo_script} -0 -o {self.msh_file} && '
            f'python3 {gmsh_script} {self.mesh_prefix} -p 1 -r {self.p_order} && '
            f'mpirun -np {self.num_partitions} {self.mesh_tool} {self.config_file}'
        ]

    @sanity_function
    def validate_mesh(self):
        return sn.all([
            sn.assert_found(r'Mesh generation complete', self.stdout),
            sn.assert_exists(f'{self.output_dir}/{self.mesh_prefix}.msh'),
            sn.assert_exists(f'{self.output_dir}/{self.mesh_prefix}.h5'),
            sn.assert_exists(f'{self.output_dir}/{self.mesh_prefix}_partitions.hdf')
        ])

    @performance_function('GB')
    def mesh_size(self):
        return sn.extractsingle(r'Final mesh size: (\d+\.\d+) GB', self.stdout, 1, float)

    @run_before('performance')
    def set_perf_vars(self):
        self.perf_variables = {
            'size': self.mesh_size(),
            'gen_time': sn.extractsingle(r'Generation time: (\d+\.\d+)s',self.stdout, 1, float)
        }
