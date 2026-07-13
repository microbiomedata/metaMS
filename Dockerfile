FROM python:3.13-slim AS base

WORKDIR /metams

# Install .NET runtime via official script to avoid legacy Mono repo issues on arm64.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates libssl3 libkrb5-3 zlib1g gcc python3-dev && \
    curl -sSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh && \
    chmod +x /tmp/dotnet-install.sh && \
    /tmp/dotnet-install.sh --runtime dotnet --channel 8.0 --install-dir /usr/local/dotnet && \
    rm /tmp/dotnet-install.sh

ENV DOTNET_ROOT=/usr/local/dotnet
ENV PATH="${PATH}:/usr/local/dotnet"
ENV PYTHONNET_RUNTIME=coreclr
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# Copy MetaMS package sources and metadata.
COPY metaMS/ /metams/metaMS/
COPY README.md disclaimer.txt Makefile requirements.txt setup.py /metams/

# Keep existing package behavior while using coreclr runtime.
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir pycparser && \
    python -m pip install --no-cache-dir --editable . && \
    apt-get purge -y gcc python3-dev && apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*