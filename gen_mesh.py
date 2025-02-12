#!/usr/bin/env python3
import os
import argparse
import math

def generate_geo_content(side_len, n_elements, p_order):
    """Generate the .geo file content with mesh parameters."""
    return f'''pi = 3.14159265;
n = {n_elements};
h = {side_len}/n;
Point(1) = {{0,0,0,h}};
Point(2) = {{{side_len},0,0,h}};
Point(3) = {{{side_len},{side_len},0.0,h}};
Point(4) = {{0.0,{side_len},0.0,h}};
Line(1) = {{1,2}};
Line(2) = {{2,3}};
Line(3) = {{3,4}};
Line(4) = {{4,1}};
Line Loop(1) = {{1,2,3,4}};
Surface(1) = {{1}};
Transfinite Surface {{1}};
Recombine Surface {{1}};
Extrude {{0, 0, {side_len}}} {{
    Surface{{1}}; Layers{{n}}; Recombine;
}}
Physical Surface("Periodic") = {{21,13,17,25,26,1}};
Physical Volume("fluid") = {{1}};
Mesh.MshFileVersion = 2.2;
Mesh.ElementOrder = {p_order};
Mesh 3;
Periodic Surface {{17}} = {{25}} Translate {{{side_len}, 0, 0}};
Periodic Surface {{21}} = {{13}} Translate {{0, {side_len}, 0}};
Periodic Surface {{26}} = {{1}} Translate {{0, 0, {side_len}}};'''

def generate_config_content(output_dir, mesh_prefix, num_partitions):
    """Generate the config file content."""
    return f'''gmsh_filePath "{output_dir}/"
gmsh_fileName "{mesh_prefix}"
mesh_h5_filePath "{output_dir}/"
mesh_h5_fileName "{mesh_prefix}_partitions"
num_partitions {num_partitions}
lineal_output 1
eval_mesh_quality 1'''

def main():
    parser = argparse.ArgumentParser(description='Generate mesh files for simulation')
    parser.add_argument('--p_order', type=int, required=True, help='P order value')
    parser.add_argument('--n_elements', type=int, required=True, help='Number of elements')
    parser.add_argument('--num_partitions', type=int, required=True, help='Number of partitions')
    parser.add_argument('--side_len', type=float, default=2*math.pi, help='Side length (default: 2π)')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory path')
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate mesh prefix
    mesh_prefix = f'mesh_n{args.side_len}_n{args.n_elements}_o{args.p_order}'

    # Generate and write .geo file
    geo_path = os.path.join(args.output_dir, f'{mesh_prefix}.geo')
    with open(geo_path, 'w') as f:
        f.write(generate_geo_content(args.side_len, args.n_elements, args.p_order))

    # Generate and write config file
    config_path = os.path.join(args.output_dir, f'{mesh_prefix}_config.dat')
    with open(config_path, 'w') as f:
        f.write(generate_config_content(args.output_dir, mesh_prefix, args.num_partitions))

    print(f"Generated files in {args.output_dir}:")
    print(f"- {geo_path}")
    print(f"- {config_path}")

if __name__ == '__main__':
    main()
