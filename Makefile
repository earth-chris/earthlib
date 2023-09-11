####################
# setup

NAME=earthlib
CONDA=conda run --no-capture-output --name ${NAME}
PYVERSION=3.10
.PHONY: create docs test collections pypi

# help docs
.DEFAULT: help
help:
	@echo "--- [ $(NAME) developer tools ] --- "
	@echo ""
	@echo "make create - initialize conda dev environment"
	@echo "make docs   - install mkdocs dependencies"
	@echo "make test   - run package tests"
	@echo "make collections - generate new formatted collections.json file"
	@echo "make pypi   - build and upload pypi package"

####################
# utils

init:
	poetry init --python=^3.7
	poetry add --lock "earthengine-api>=0.1.317" "numpy>=1.21.5" "pandas>=1.3.5" "spectral>=0.22.4" "tqdm>=4.63.0"
	poetry add --lock --group dev "ipython^8.5.0" jupyter geemap pre-commit pytest pytest-cov pytest-xdist twine mkdocs mkdocs-material mkdocstrings[python] mkdocs-jupyter livereload

create:
	conda env list | grep -q ${NAME} || conda create --name=${NAME} python=${PYVERSION} -y
	${CONDA} poetry install
	${CONDA} pre-commit install

test:
	${CONDA} pytest -n auto --cov --no-cov-on-fail --cov-report=term-missing:skip-covered

collections:
	${CONDA} python scripts/generate_collections.py

pypi:
	rm -rf dist/
	${CONDA} poetry build
	twine upload dist/*
