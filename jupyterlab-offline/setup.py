from setuptools import setup

setup(
    name='jupyterlab-offline',
    version='0.1.0',
    description='Tools for offline JupyterLab assets',
    url='http://github.com/jupyterlab/jupyterlab-offline',
    author='Jupyter Development Team',
    author_email='jupyter@googlegroups.com',
    license='BSD-3-Clause',
    packages=['jupyterlab_offline'],
    setup_requires=['jupyterlab'],
    entry_points={
        'console_scripts': [
            'jupyter-laboffline = jupyterlab_offline.labofflineapp:main',
        ]
    },
    zip_safe=False,
    include_package_data=True,
)
