# Contributing to the Documentation

You're working on a project and want (or are forced) to contribute to this project? Great! Here's everything you need to set up and change the documentation.

## How does the Documentation work?

This documentation uses [MKDocs for Material](https://squidfunk.github.io/mkdocs-material/). Read through the documentation if you want to get started. Alternatively, you can just look through the documentation files. Pretty much everything in here is plain Markdown, the only exception are [Admonitions](https://squidfunk.github.io/mkdocs-material/reference/admonitions/), which you might have seen here and there.

## Getting started

To get started, you'll have to do several things:

1. MKDocs is based on Python, so you'll need to have Pthon installed
2. You'll need to create a Virtual Environment to install `mkdocs-material` using `pip`. You can also just use the `requirements.txt` file at the root of the project.
3. You're pretty much done setting everything up. Now you'll just need to serve the documentation locally in order to see your changes. For this, make sure you are in a Terminal which has your Virtual Environment enabled and run `mkdocs serve --livereload`

For convenience, here's a script for the initial setup. Please note that executing this code as a script-file will not leave your terminal inside the Virtual Environment and will thus not enable you to call mkdocs. To serve the mkdocs server after executing the script, simply run `python -m venv .venv` followed by `mkdocs serve --livereload`. These commands need to be executed from the project root. The script only needs to be run once and never again as long as the Virtual Environment is not deleted.

```bash
#!/bin/sh
cd "./$(dirname "$0")/.."
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Creating new pages or changing the navigation

The last important thing to know is the configuration for MKDocs. The config is located at the root of this Project, it's called `mkdocs.yaml`. In order to add additional pages to the documentation or edit the Navigation bar, this file has to be edited. It's a yaml file and should be self-explanatory. When in doubt, refer to the [MKDocs configuration documentation](https://www.mkdocs.org/user-guide/configuration/).

## But how do I get my local changes into the github.io?

The ci workflow in `.github/workflows/` automatically updates the github.io on every push. So to get your changes online, you'll just have to commit and push them!
