# Developer Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Setting Up the Development Environment](#setting-up-the-development-environment)
3. [Releasing a new version](#releasing-a-new-version)
    1. [Bump Version Numbers](#bump-version-numbers)
    2. [Push Updated Docker Image](#push-updated-docker-image)
4. [Generate Documentation](#generate-documentation)

## Introduction
This guide provides instructions for developers working on the project. It covers setting up the development environment, pushing Docker images, generating documentation, and bumping version numbers.

## Setting Up the Development Environment
1. Clone the repository:
    ```sh
    git clone https://github.com/your-repo/metams.git
    cd metams
    ```
2. Create a virtual environment:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
4. Install developer-specific dependencies:
    ```sh
    pip install -r requirements-dev.txt
    ```

## Releasing a new version

The following steps should be followed in order

### Bump Version Numbers
The versioning of the repo, docker image and the GC/MS workflow are currently 3.1.0.
The version of the lipid workflow is currently 1.1.0.
The version of the LCMS metabolomics workflow is currently 0.0.0.

To bump the repo *and all workflows*, run one of the following commands.  This will update the runtime version of all of the workflows, the version of the repo and the version of the docker image.

    ```sh
    make major
    ```

    ```sh
    make minor
    ```

    ```sh
    make patch
    ```
### Push Updated Docker Image
Use the github action to push a docker image to the appropriate dockerhub repository.

## Generating Documentation

**This happens automatically with bumping versions if using the `make major` commands (or similar) above.**
Overview documentation of the two workflows can be found the docs folder of this repo.

For the lipidomics workflow, edit only the `docs/lcms_lipidomics/index.rst` file.  Once changes are made there, re-render the `docs/lcms_lipidomics/index.html` and the `docs/lcms_lipidomics/README_LCMS_LIPID.md` with the following command.  

    ```sh
    make convert_lipid_rst_to_md
    ```

For the LCMS metabolomics workflow, edit the `index.rst` file within the `docs/lcms_metabolomics` subfolder.  Once changes are made there, re-render the `docs/lcms_metabolomics/index.html` and the `docs/lcms_metabolomics/README_LCMS_METABO.md` with the following command for lcms metabolomics:

    ```sh
    make convert_lcmsmetab_rst_to_md
    ```

API documentation can be found in the docs/metaMS file. We use [pdoc](https://github.com/mitmproxy/pdoc) to generate the API documentation.  To regenerate the API documentation, run the following command.  Note that **this happens automatically with bumping versions if using the `make major` commands (or similar) above.**


    ```sh
    make docu
    ```
