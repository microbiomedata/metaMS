# Developer Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Setting Up the Development Environment](#setting-up-the-development-environment)
3. [Pushing Docker Images](#pushing-docker-images)
4. [Generating Documentation](#generating-documentation)
5. [Bumping Version Numbers](#bumping-version-numbers)

## Introduction
This guide provides instructions for developers working on the project. It covers setting up the development environment, pushing Docker images, generating documentation, and bumping version numbers.

## Setting Up the Development Environment
1. Clone the repository:
    ```sh
    git clone https://github.com/your-repo/metams.git
    cd metams
    ```
2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
3. Install developer-specific dependencies
    ```sh
    pip install -r requirements-dev.txt
    ```

## Steps to releasing a new version

### Pushing Updated Docker Image
You must be logged into docker hub
1. Build the push the tagged docker image
    ```sh
    make docker-nmdc
    ```

### Bumping Version Numbers
The versioning of the repo, docker image and the GC/MS workflow are currently 2.2.3
The version of the lipid workflow is currently 1.0.0

To bump *both* the repo and the lipid workflow, run one of the following commands.

    ```sh
    make major
    ```

    ```sh
    make minor
    ```

    ```sh
    make patch
    ```

### Generate Documentation
Documentation of the two workflows can be found the docs folder of this repo.

For the lipidomics workflow, edit only the `docs/index_lipid.rst` file.  Once changes are made there, re-render the `docs/index_lipid.html` and the `docs/README_LCMS_LIPID.md` with the following command.  This should happen after the version numbers are bumped.
    ```sh
    make convert_lipid_rst_to_md
    ```
