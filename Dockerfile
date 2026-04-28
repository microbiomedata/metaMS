# Python base image
FROM python:3.11.1-bullseye

ENV PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  DOTNET_ROOT=/usr/local/dotnet \
  PATH="${PATH}:/usr/local/dotnet" \
  PYTHONNET_RUNTIME=coreclr \
  DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# Install native dependencies and the .NET runtime used by pythonnet.
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates clang gcc python3-dev \
  && curl -sSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
  && chmod +x /tmp/dotnet-install.sh \
  && /tmp/dotnet-install.sh --runtime dotnet --channel 8.0 --install-dir /usr/local/dotnet \
  && rm /tmp/dotnet-install.sh \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/* /tmp/*


# Pythonnet: 3.0.1 (from PyPI)
# Note: pycparser must be installed before pythonnet can be built
RUN pip install --no-cache-dir pycparser \
  && pip install --no-cache-dir pythonnet==3.0.1 \
  && rm -rf /root/.cache /tmp/*
  
# Copy MetaMS contents
WORKDIR /metams
COPY metaMS/ /metams/metaMS/
COPY README.md disclaimer.txt Makefile requirements.txt setup.py /metams/

# Install the correct version of CoreMS from github
RUN pip install git+https://github.com/EMSL-Computing/CoreMS.git@v3.11.0

# Install the MetaMS package in editable mode
RUN pip3 install --no-cache-dir --editable . \
  && rm -rf /root/.cache /tmp/*