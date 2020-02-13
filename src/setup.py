from setuptools import setup, find_packages

setup(
    name='project',
    version='1.0',
    packages=find_packages(),
    data_files=[
        ('crawler/utils/local_files', ['crawler/utils/local_files/ping.html']),
    ],
    entry_points={
        'scrapy': ['settings = crawler.settings'],
    },
)
