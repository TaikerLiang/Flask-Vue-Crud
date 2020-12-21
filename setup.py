from setuptools import setup, find_packages


def get_requirements(req_file):
    with open(req_file) as fp:
        return [
            x.strip()
            for x in fp.read().split('\n')
            if not x.startswith('#')
        ]


install_requires = get_requirements('src/requirements-app.txt')
dev_requires = get_requirements('requirements-dev.txt')


setup(
    name='epsc',
    version='0.2',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
    },
    entry_points={
        'console_scripts': ['epsc = cli_main:cli'],
    },
)
