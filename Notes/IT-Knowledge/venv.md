# Python Virtual Environments (.venv)

## What is it

A `.venv` is an isolated Python environment that lives inside your project folder.
It has its own copy of Python and its own set of installed packages — completely separate from every other project on your machine.

## Why it matters

Without a venv, all your projects share the same global Python installation (the `base` conda environment).
This causes problems when two projects need different versions of the same package — they conflict and break each other.

With a venv, each project is self-contained. Installing something for Project A never affects Project B.

## How it works

When you activate a venv, your terminal's `python` and `pip` commands point to the venv instead of the system Python.
Anything you install with `pip install` goes into the venv folder, not your global environment.

The venv folder (`.venv/`) is never committed to git — it stays local on your machine.
Other developers (or you on another machine) recreate it from a `requirements.txt` file.

## How to set it up

Run these from your project root folder:

```bash
# 1. Create the venv (only do this once per project)
python -m venv .venv

# 2. Activate it (do this every time you open a new terminal)
source .venv/bin/activate

# Your prompt changes from (base) to (.venv) — this confirms it's active

# 3. Install your packages into it
pip install azure-ai-contentsafety azure-identity python-dotenv
```

## How to use it day to day

Every time you open a new terminal session, activate the venv first:

```bash
source .venv/bin/activate
```

To deactivate (go back to normal):

```bash
deactivate
```

To see what's installed in the active venv:

```bash
pip list
```

## VS Code integration

VS Code can use the venv automatically:
1. `Cmd+Shift+P` → **Python: Select Interpreter**
2. Pick the one showing `.venv`

Once selected, VS Code uses that interpreter for running scripts and resolving imports — the yellow import warnings go away.

## Saving your dependencies

When you want to record what packages your project needs (so someone else can recreate the venv):

```bash
pip freeze > requirements.txt
```

To recreate a venv from a requirements file:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## What goes in .gitignore

The `.venv/` folder is never committed — it's machine-specific and can be recreated.
Your `.gitignore` already has this covered:

```
.venv/
```
