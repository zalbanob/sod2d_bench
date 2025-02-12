#!/usr/bin/env python3
import os
import argparse
import sys
import pystache

def parse_params(param_list):
    params = {}
    for param in param_list:
        if '=' not in param:
            print(f"Invalid parameter format: {param}. Expected key=value", file=sys.stderr)
            sys.exit(1)
        key, value = param.split('=', 1)
        params[key] = value
    return params

def render_template(template_path, params):
    with open(template_path, 'r') as f:
        template_content = f.read()
    renderer = pystache.Renderer()
    rendered = renderer.render(template_content, params)
    return rendered

def main():
    parser = argparse.ArgumentParser(
        description="Render a mustache template with named parameters to an output directory."
    )
    parser.add_argument('--template'  , type=str, required=True, help='Path to the mustache template file.')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory where the rendered output will be written.')
    parser.add_argument('--param', action='append', default=[],help='Named parameter in the format key=value. Can be used multiple times.')
    parser.add_argument('--output_name', type=str, default=None,help='Optional output file name. Defaults to the template file name if not provided.')
    args = parser.parse_args()
    print(args)
    params = parse_params(args.param)

    os.makedirs(args.output_dir, exist_ok=True)
    rendered_content = render_template(args.template, params)
    
    if args.output_name: output_filename = args.output_name
    else: output_filename = os.path.basename(args.template)

    output_path = os.path.join(args.output_dir, output_filename)
    with open(output_path, 'w') as f:
        f.write(rendered_content)

    print(f"Rendered template written to: {output_path}")

if __name__ == '__main__':
    main()
