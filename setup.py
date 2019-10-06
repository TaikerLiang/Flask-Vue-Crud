from setuptools import setup, find_packages


def get_requirements(env):
    with open(f'requirements-{env}.txt') as fp:
        return [
            x.strip()
            for x in fp.read().split('\n')
            if not x.startswith('#')
        ]


install_requires = get_requirements('base')
dev_requires = get_requirements('dev')
tests_requires = get_requirements('tests')
deploy_requires = get_requirements('deploy')


setup(
    name='epsc',
    version='0.1',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'tests': tests_requires,
        'deploy': deploy_requires,
    },
    entry_points={
        'console_scripts': ['epsc = cli_main:cli'],
    },
)
