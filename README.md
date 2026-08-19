# The Earth Library

<img src="https://earth-chris.github.io/earthlib/img/earth-unmixed.png">

<p align="center">
  <em>A spectral library for continuous satellite land cover mapping.</em>
</p>

---

**Documentation**: [earth-chris.github.io/earthlib](https://earth-chris.github.io/earthlib)

**Source code**: [earth-chris/earthlib](https://github.com/earth-chris/earthlib)

---

## :earth_asia: Introduction

`earthlib` is a python package featuring a global spectral library. It was developed to support satellite-based land cover mapping.

The library contains a diverse catalog of unique spectral endmembers representing green vegetation, bare soil, non-photosynthetic vegetation, urban materials, and burned materials.

The reflectance data cover the visible to the shortwave infrared wavelengths (400-2450 nm) at 10 nm band widths.

`earthlib` provides tools to resample these spectra to match the wavelengths of popular satellite and airborne earth observing sensors. The purpose is to support running [spectral mixture analysis](https://earth-chris.github.io/earthlib/introduction/) in a sensor-agnostic fashion.

Running spectral mixture analysis across sensors with a consistent spectral library presents a new approach to creating consistent, analysis-ready data.

The goal of `earthlib` is to help users quantify spatial and temporal patterns of global land cover change in a [sensor-generic](https://earth-chris.github.io/earthlib/sources/) fashion.


## :seedling: Installation

This library can be installed via `pip`.

```bash
pip install earthlib
```

You can also clone the source repository and install it locally.

```bash
git clone https://github.com/earth-chris/earthlib.git
cd earthlib
pip install -e .
```

The Earth Engine routines (`earthlib.geelib`) are not currently available. They are out of date with the v1.1 API and are being reworked. The spectral library is unaffected.

## :hammer_and_wrench: Development

`earthlib` uses [pixi](https://pixi.sh) to manage environments.

```bash
git clone https://github.com/earth-chris/earthlib.git
cd earthlib
pixi install
```

Common tasks:

```bash
pixi run test                    # run tests with coverage
pixi run -e lint lint            # format and lint (installs pre-commit hooks)
pixi run -e typecheck typecheck  # run mypy
pixi run -e docs docs-serve      # serve docs locally
```

Please commit using the development environment to ensure code is well-formatted.

## :deciduous_tree: Developed by

[Christopher Anderson](https://cbanderson.info)[^1]

<a href="https://www.linkedin.com/in/christopher-b-anderson/">![LinkedIn Follow](https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white)</a>
<a href="https://scholar.google.com/citations?hl=en&user=LoGxS40AAAAJ&view_op=list_works">![Google Scholar](https://img.shields.io/badge/Google%20Scholar-%2320beff?color=1f1f18&logo=google-scholar&style=flat-square)</a>
<a href="https://orcid.org/0000-0001-7392-4368">![ORC-ID](https://img.shields.io/badge/ORCID-0000--0001--7392--4368-brightgreen)</a>
<a href="https://github.com/earth-chris">![GitHub Stars](https://img.shields.io/github/stars/earth-chris?affiliations=OWNER%2CCOLLABORATOR&style=social)</a>

This package was primarily developed at the Stanford Center for Conservation Biology and Salo Sciences.

[^1]: [Planet Labs PBC](https://www.planet.com)
