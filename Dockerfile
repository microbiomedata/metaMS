FROM jcarr87/corems-base-py3.10
WORKDIR /metams

COPY metaMS/ /metams/metaMS/
COPY README.md disclaimer.txt Makefile requirements.txt setup.py /metams/
COPY db/ /metams/db/

# Install the MetaMS package in editable mode
RUN pip3 install --editable .


