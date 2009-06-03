from setuptools import setup, find_packages

setup(
    name = "pymug",
    version = "0.1-dev",
    url = 'http://www.fort-awesome.net/wiki/Pymug',
    license = 'MIT',
    description = "A simple SmugMug wrapper",
    author = 'Erik Karulf <erik@karulf.com>',
    # Below this line is tasty Kool-Aide provided by the Cargo Cult
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools'],
)