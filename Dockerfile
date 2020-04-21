FROM corilo/corems:base-mono-pythonnet
WORKDIR /metaB

COPY coreMB/ /metaB/coreMB/
COPY README.md disclaimer.txt Makefile requirements.txt setup.py /metaB/
COPY db/ /metaB/db/
RUN pip3 install --editable .
ENTRYPOINT ["coreMB"]

