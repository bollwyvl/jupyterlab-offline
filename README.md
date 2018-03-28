# ☠️ EXPERIMENTAL ☠️ jupyterlab-offline
> _(Re)build JupyterLab and Extensions Faster With More Energy, but without an npm registry_

> # ☠️ NO REALLY ☠️ THIS WILL MESS UP YOUR JUPYTERLAB ☠️

# Features
- [x] store yarn.lock and dependencies
- [x] build static assets from offline lockfiles and dependencies
- [x] scaffold command for conda recipe
- [ ] better tests

# Use cases
- npm is down
- you can't run your own npm repository

# Alternative Approaches
- provide a local npm repository

  Could be `couchapp` or an alternative, lightweight, scope-enabled, npm-compatible registry

  - pro
    - doesn't need `git` (needed to merge lockfiles)
    - probably more robust to minor semver changes
  - meh
    - still can't account for "missed-chance" duplication
    - probably the same on disk
  - con
    - another port opened, probably...
    - more node

# Failure modes
## Missed-chance duplication
If...
- package A requires version 1.1 and less than 1.3 or greater of B
  - and bundles B@1.1
- package C requires version 1.2 or greater of B
  - and bundles B@1.3

Then the one valid resolution (B@1.2) would not be in the offline cache.

- Impact: build fails, requires manual intervention
 (e.g. `conda remove last-thing`)
- Likelihood: ??? (needs data)

# Command-Line Usage
## `jupyter laboffline build`
Attempt to build the current JupyterLab application using only offline assets.
These are usually put in `$APP_DIR/offline` by installing packages.

## `jupyter laboffline install`
Attempt to perform a clean install of the extension at that version, capturing
its yarn.lock and npm dependencies.

```bash
jupyter laboffline install @jupyter-widgets/jupyterlab-manager 0.33.2
```

Known dependencies should **already have been installed** through your package
manager.

## `jupyterlab-offline scaffold conda <@npm/name of extension> <simple semver>`
Print out a scaffold `conda-build` `meta.yaml` for an extension

> TODO: explore pip option

```bash
git clone https://github.com/conda-forge/staged-recipes
cd staged-recipes
mkdir -p recipes/bqplot
jupyterlab-offline scaffold conda bqplot 0.3.6 > recipes/bqplot/meta.yaml
# Add already-packged upstreams with good semantic versioning
# Make a PR!
# Add it to your release automation
# TODO: tie into bot
```

# API

    TBD

# Installation

    TBD

## Dependencies
### `jupyterlab 0.31.12`
`jupyterlab-offline` reuses much of the `jupyterlab` infrastructure, and its
bundled package manager (`yarn` ne `jlpm`)

### `git`
`git` is needed to merge all of the yarn lockfiles together

### `nodejs`
`nodejs` is required to run `jupyterlab build`
> Other JavaScript runtimes, e.g. PyMiniRacer, might be possible


# Development
```
conda env update
source activate jupyterlab-offline-dev
anaconda-project run test # tbd
```
