# Packaging JupyterLab for offline building

## User Story
```gherkin
   As an end end user,
Given I have a package manager (e.g. pip, conda, apt, yum, etc.)
  And I am not connected to the internet
 When I install a labextension
 Then it should build.
```

## Motivation
While **business, education, and science end-users** of JupyterLab want to write
code, only a small proportion (e.g. IJavaScript kernel users vs all users) will
have any interest in the NodeJS/npm ecosystem, and to the extent possible
should be shielded from its quirks while having a robust interactive
computational environment.

Similarly, **extension developers** will likely be interested in supporting
issues with _their_ code, not the explosion of interactions between different
versions of **_n_-level-deep dependencies** failing to install, etc.

Despite heroic efforts, we've ended up with a **highly extensible** application
that requires a bootcamp degree in **full-stack web application development**
to actually extend, especially when **things go wrong**.

## Goal
By making **JupyterLab extensions installable by "normal means,"** i.e. the
package manager they used to install JupyterLab itself, **end users** will be
more **quickly, reliably, and confidently** use a Lab ecosystem that
**developers** will be able to support more **efficiently, simply, and
robustly**.

## Options
### Option 0: Do nothing
### Option 1: Consensus yarn offline mirror
### Option 2: Run a local npm registry

## Experiment: Option 1
In this repo, we'll explore (initially) Option 1, packaging for
`conda`. In addition to JupyterLab Core, we'll look at some key
second- and third-party extensions:
- `ipywidgets`: really first-party, but not included in `jupyterlab` by default (yet)
- `bqplot`: a well-supported widget library that uses key dependencies like `d3`
- `pythreejs`: a well-supported widget library that uses a heavy dependency, `three ^0.99.0`
- `ipyvolume`: a well-supported widget library that also uses `three ^0.85.0`

### Build `jupyterlab-offline(-*)`
#### `jupyterlab-offline`
This packages the entire build chain (`webpack`).

####
