# Packaging JupyterLab for offline building

## User Story
```gherkin
   As an end end user,
Given I have a package manager (e.g. pip, conda, apt, yum, etc.)
  And I am not connected to the internet
 When I install a labextension
 Then it should build.
```

# Approach 1: Consensus yarn offline mirror

# Approach 2: Run a local npm registry
