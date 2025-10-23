import pathlib, os, sys
import setuptools
from setuptools import Command, setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="metaMS",
    version="3.3.3",
    description="Data processing, and annotation for metabolomics analyses",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/EMSL-Computing/MetaMS",
    author="Corilo, Yuri",
    author_email="corilo@pnnl.gov",
    py_modules = ['metaMS'],
    packages = find_packages(),
    license="BSD",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],

    install_requires=['Click', 'CoreMS', 'requests'],
    
    entry_points={"console_scripts": ["metaMS = metaMS.cli:cli"]},


)
    