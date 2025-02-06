import os
import numpy as np
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import run_after, run_before, sanity_function, performance_function, parameter

@rfm.simple_test
class MeshGenerationTest(rfm.RunOnlyRegressionTest):
    side_len       = parameter([2 * np.pi])  
    n_elements     = parameter([8, 16])
    num_partitions = parameter([1])
    p_order        = parameter([3])

    valid_systems       = ['*']
    valid_prog_environs = ['builtin']
    executable          = 'bash'
    executable_opts     = []

    @run_after('init')
    def set_output_dir(self):
        param_str = f'L{self.side_len}_ne{self.n_elements}_o{self.p_order}_np{self.num_partitions}'
        self.output_dir = f'/gpfs/projects/bsc99/bsc099260/EuroHPC/SOD2D/VALIDATION_FRAMEWORK/meshes/p{self.p_order}/ne{self.n_elements}' #os.path.abspath(f'meshes/p{self.p_order}/ne{self.n_elements}')
        os.makedirs(self.output_dir, exist_ok=True)

    @run_before('run')
    def prepare_script(self):
        # Full paths to required tools
        self.mesh_tool   = "/gpfs/projects/bsc99/bsc099260/EuroHPC/SOD2D/SRC/OPT1/sod2d_gitlab/build_cpu/tool_meshConversorPar/tool_meshConversorPar"
        self.gmsh_script = "/gpfs/projects/bsc99/bsc099260/EuroHPC/SOD2D/SRC/OPT1/sod2d_gitlab/utils/gmsh2sod2d/gmsh2sod2d.py"
        
        if not all(os.path.exists(p) for p in [self.mesh_tool, self.gmsh_script]):
            raise OSError("Critical executables missing")

        self.mesh_prefix = f"mesh_n{self.side_len}_n{self.n_elements}_o{self.p_order}"
        self.geo_path = os.path.join(self.output_dir, f'{self.mesh_prefix}.geo')
        self.msh_path = os.path.join(self.output_dir, f'{self.mesh_prefix}.msh')
        self.config_path = os.path.join(self.output_dir, f'{self.mesh_prefix}_config.dat')

        with open(self.geo_path, 'w') as f:
            f.write(self._geo_content())
            
        with open(self.config_path, 'w') as f:
            f.write(self._config_content())

        opts = [
            f'mkdir -p {self.output_dir} && ',
            f'cd {self.output_dir} && ',
            f'gmsh {self.geo_path} -0 -o {self.msh_path} && ',
            f'python {self.gmsh_script} {self.msh_path[:-4]} -p 1 -r {self.p_order} && ',
            f'mpirun -np {self.num_partitions} {self.mesh_tool} {self.config_path}'
        ]
        # Build a single command string
        command_string = "-c '" + ' '.join(opts) + "'"
        print(command_string)
        self.executable_opts = [command_string]

    def _geo_content(self):
        geo_content = (
            f'pi = 3.14159265;\n'
            f'n = {self.n_elements};\n'
            f'h = {self.side_len}/n;\n'
            f'Point(1) = {{0,0,0,h}};\n'
            f'Point(2) = {{{self.side_len},0,0,h}};\n'
            f'Point(3) = {{{self.side_len},{self.side_len},0.0,h}};\n'
            f'Point(4) = {{0.0,{self.side_len},0.0,h}};\n'
            f'Line(1) = {{1,2}};\n'
            f'Line(2) = {{2,3}};\n'
            f'Line(3) = {{3,4}};\n'
            f'Line(4) = {{4,1}};\n'
            f'Line Loop(1) = {{1,2,3,4}};\n'
            f'Surface(1)   = {{1}};\n'
            f'Transfinite Surface {{1}};\n'
            f'Recombine Surface   {{1}};\n'
            f'Extrude {{0, 0, {self.side_len}}} {{\n'
            f'    Surface{{1}}; Layers{{n}}; Recombine;\n'
            f'}}\n'
            f'//+ Set every surface to periodic, using surf(1) as master\n'
            f'Physical Surface("Periodic") = {{21,13,17,25,26,1}};\n'
            f'//+ Set the fluid region\n'
            f'Physical Volume("fluid") = {{1}};\n'
            f'//+ Set the output mesh file version\n'
            f'Mesh.MshFileVersion = 2.2;\n'
            f'//+ Options controlling mesh generation\n'
            f'Mesh.ElementOrder = {self.p_order};\n'
            f'Mesh 3;\n'
            f'//+ Generate the periodicity between surface pairs\n'
            f'Periodic Surface {{17}} = {{25}} Translate {{{self.side_len}, 0, 0}};\n'
            f'Periodic Surface {{21}} = {{13}} Translate {{0, {self.side_len}, 0}};\n'
            f'Periodic Surface {{26}} = {{1}} Translate  {{0, 0, {self.side_len}}};'
        )
        return geo_content

    def _config_content(self):
        config_content = (
            f'gmsh_filePath "{self.output_dir}/"\n'
            f'gmsh_fileName "{self.mesh_prefix}"\n'
            f'mesh_h5_filePath "{self.output_dir}/"\n'
            f'mesh_h5_fileName "{self.mesh_prefix}_partitions"\n'
            f'num_partitions {self.num_partitions}\n'
            f'lineal_output 1\n'
            f'eval_mesh_quality 1'
        )
        return config_content

    @sanity_function
    def validate_mesh(self):
        expected_nodes = (self.n_elements * self.p_order + 1)**3
        expected_elems = self.n_elements**3
        return sn.all([
            sn.assert_found(r'Done writing \'.*\.msh\'', self.stdout),
            sn.assert_found(r'Everything Done!', self.stdout),
            sn.assert_not_found(r'ERROR|Error|error|FAIL|FAILED|Failed', self.stdout),
            sn.assert_eq(
                sn.extractsingle(r'Detected <(\d+)> nodes', self.stdout, 1, int),
                expected_nodes
            ),
            # Uncomment and adjust if element count check is required:
            # sn.assert_eq(
            #     sn.extractsingle(r'Elems found: (\d+) inner', self.stdout, 1, int),
            #     expected_elems
            # )
        ])

    @performance_function('s', perf_key='gmsh_time')
    def extract_gmsh_time(self):
        return sn.extractsingle(r'From start: Wall (\d+\.\d+)s', self.stdout, 1, float)

    @performance_function('s', perf_key='total_time')
    def extract_total_time(self):
        return sn.extractsingle(r'Total Mesh generation time\s+(\d+\.\d+)', self.stdout, 1, float)

    @run_before('performance')
    def set_perf_vars(self):
        self.perf_variables = {
            'gmsh_time': self.extract_gmsh_time(),
            'total_time': self.extract_total_time(),
        }
