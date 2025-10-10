# Python base image
FROM python:3.11.1-bullseye

# Mono: 6.12
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
  && echo "deb http://download.mono-project.com/repo/debian buster/snapshots/6.12 main" > /etc/apt/sources.list.d/mono-official.list \
  && apt-get update \
  && apt-get install -y clang \
  && apt-get install -y mono-devel=6.12\* \
  && rm -rf /var/lib/apt/lists/* /tmp/*


# Pythonnet: 3.0.1 (from PyPI)
# Note: pycparser must be installed before pythonnet can be built
RUN pip install pycparser \
  && pip install pythonnet==3.0.1
  
# Copy MetaMS contents
WORKDIR /metams
COPY metaMS/ /metams/metaMS/
COPY README.md disclaimer.txt Makefile requirements.txt setup.py /metams/

# Install the correct version of CoreMS from github
RUN pip install git+https://github.com/EMSL-Computing/CoreMS.git@v3.9.1

# Install the MetaMS package in editable mode
RUN pip3 install --editable .