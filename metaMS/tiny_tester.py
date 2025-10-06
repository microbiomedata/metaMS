"""
INSTRUCTIONS TO RUN:
**Make sure you put the two test files into metaMS/ before building**

1. build with docker build -t local-metams:latest .
2. In a new terminal run docker run -it --entrypoint /bin/bash my_metams_image
    This will open a shell prompt within the docker image
3. cd metaMS
4. python tiny_tester.py

"""


from corems.mass_spectra.input.rawFileReader import ImportMassSpectraThermoMSFileReader
from multiprocessing import Pool
import click

def func(file_in):
   click.echo(f"Processing file: {file_in}")
   parser = ImportMassSpectraThermoMSFileReader(file_in)
   myLCMSobj = parser.get_lcms_obj(spectra="ms1")    
   return myLCMSobj

cores = 2
files = ["Blanch_Nat_Lip_C_4_AB_M_08_NEG_25Jan18_Brandi-WCSH5801.raw", "Blanch_Nat_Lip_C_4_AB_M_08_NEG_25Jan18_Brandi-WCSH5801-copy-2.raw"]
with Pool(cores) as pool:
    click.echo("In with pool...")
    mz_dicts = pool.map(func, files)