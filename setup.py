from setuptools import setup, find_packages
import os

def get_requirements():
    """Parse requirements from 'requirements.txt'."""
    return []
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def get_package_data():
    """Collect all .py files in subdirectories."""
    package_data = {}
    dirs = ['cases', 'core', 'deps', 'meshes', 'validation']
    for directory in dirs:
        package_dir = os.path.join('sod2d_bench', directory)
        if os.path.exists(package_dir):
            package_data['sod2d_bench'] = [
                os.path.join('**', '*')
            ]
    return package_data

setup(
    name='sod2d_bench',
    version='0.0.1',
    description='Benchmarking Framework for SOD2D',
    long_description='Framework for HPC simulations and validations using SOD2D',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://gitlab.com/bsc_sod2d/sod2d_gitlab',
    license='MIT',
    packages=find_packages(),
    package_data=get_package_data(),
    install_requires=get_requirements(),
    entry_points={
        'console_scripts': [
            'run-simulation=sod2d_bench.core.run:main',
            'generate-mesh=sod2d_bench.meshes.cube_gen:main',
            'check-tgv=sod2d_bench.validation.check_tgv:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.8',
    zip_safe=False,
)