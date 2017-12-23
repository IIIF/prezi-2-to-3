"""Setup for iiif-prezi-upgrader."""
from setuptools import setup
import sys

setup(
    name='iiif-prezi-upgrader',
    packages=['iiif_prezi_upgrader'],
    test_suite="tests",
    version='0.1.0',
    description='A library to upgrade ',
    author='Rob Sanderson, Simeon Warner, Glen Robson',
    author_email='rsanderson@getty.edu',
    url='https://github.com/iiif-prezi/prezi-2-to-3',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
