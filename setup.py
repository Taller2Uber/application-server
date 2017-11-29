
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file

setup(
    name='llevame',
    version='1.0.0',
    description='TP Taller2 2017 2do Cuat.',
    url='https://github.com/Taller2Uber/application-server',
    packages=[
        'llevame'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
    ]
)
