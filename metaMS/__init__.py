
__version__ = '3.3.1'

import os
# Get the path to the README file
readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")

# Read the contents of the README file if it exists
if os.path.exists(readme_path):
    try:
        with open(readme_path, "r", encoding="utf-8") as readme_file:
            __doc__ = readme_file.read()
    except Exception as e:
        __doc__ = "MetaMS: Metabolomics Workflows for GC-MS Metabolomics and LC-MS Lipidomics."
        print(f"Warning: Could not read README.md file. Error: {e}")
else:
    __doc__ = "MetaMS: Metabolomics Workflows for GC-MS Metabolomics and LC-MS Lipidomics."

