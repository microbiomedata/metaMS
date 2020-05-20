import pathlib, os, sys
import setuptools
from setuptools import Command, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="metaMS",
    version="1.1.0",
    description="Data processing, and annotation for metabolomics analysis by low-resolution GC-MS",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.pnnl.gov/mass-spectrometry/metaMS",
    author="Corilo, Yuri",
    author_email="corilo@pnnl.gov",
    license="BSD",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],

    install_requires=['Click', 'CoreMS'],
    entry_points= '''
            [console_scripts]
            metaMS=metaMS.cli:cli
            ''',
)
    