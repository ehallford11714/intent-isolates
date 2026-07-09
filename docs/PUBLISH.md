# Publish notes

## Build

```bash
cd IntentIsolates
python -m pip install -e ".[dev]"
python -m pytest -q
python -m build
```

## GitHub

```bash
git init
git add .
git commit -m "intentisolates 0.3.0: isolates, typology, motifs, trajectories, layer-IV bridge"
gh repo create intent-isolates --public --source=. --remote=origin --push
git tag v0.3.0
git push origin v0.3.0
```

## PyPI / TestPyPI

```bash
# TestPyPI first (recommended)
python -m twine upload --repository testpypi dist/*

# PyPI
python -m twine upload dist/*
```

Requires `TWINE_USERNAME=__token__` and `TWINE_PASSWORD` (PyPI API token), or interactive login.

If auth is missing, GitHub + tag `v0.3.0` remain the distribution source; install via:

```bash
pip install git+https://github.com/ehallford11714/intent-isolates.git
```
