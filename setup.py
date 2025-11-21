from setuptools import setup, find_packages

setup(
    name='gametime',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'gametime=cli:main',
        ],
    },
    python_requires='>=3.10',
    author='Berkeley Learn and Verify Group',
    description='Worst-Case Execution Time (WCET) Analysis Tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
)