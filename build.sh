#!/bin/bash
conda build -c conda-forge conda.recipes/jupyterlab
conda build -c conda-forge conda.recipes/jupyterlab-offline
conda build -c conda-forge conda.recipes/jupyterlab-offline-jupyter-widgets-jupyterlab-manager
conda build -c conda-forge conda.recipes/jupyterlab-offline-bqplot
