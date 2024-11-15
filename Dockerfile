FROM jcarr87/corems-base-py3.10
WORKDIR /metams

COPY metaMS/ /metams/metaMS/
COPY README.md disclaimer.txt Makefile requirements.txt setup.py /metams/
COPY db/ /metams/db/

# Install the specific version of corems
RUN pip3 install corems==2.2.1

# Install other dependencies from requirements.txt
RUN pip3 install -r requirements.txt

# Install the MetaMS package in editable mode
RUN pip3 install --editable .


