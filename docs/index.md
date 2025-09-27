# The Earth Library

![earthlib unmixed](img/earth-unmixed.png)

<p align="center">
  <em>A global spectral library for satellite land cover mapping.</em>
</p>

---

**Documentation**: [earth-chris.github.io/earthlib](https://earth-chris.github.io/earthlib)

**Source code**: [earth-chris/earthlib](https://github.com/earth-chris/earthlib)

---

## :earth_asia: Introduction

`earthlib` is a python package featuring a global spectral library of reference spectra. It also includes software tools for satellite-based land cover mapping.

The library contains several thousand unique spectral endmembers representing green vegetation, soil, non-photosynthetic vegetation, urban materials, and burned materials. The reflectance data cover the visible to the shortwave infrared wavelengths (400-2450 nm) at 10 nm band widths.

`earthlib` provides tools to resample these spectra to match the wavelengths of popular satellite and airborne earth observing sensors. The purpose is to support running [spectral mixture analysis](introduction.md) in a sensor-agnostic way. Running spectral mixture analysis across sensors with a consistent spectral library is a new approach to creating analysis-ready data, providing consistent outputs.

This library supports running spectral mixture analysis in Google Earth Engine via the `earthengine-api` python package. This is an optional dependency, not installed by default. These routines are not currently well-tested, as best-practices for automated testing of the Earth Engine API are not clear.

The goal of `earthlib` is to help users quantify spatial and temporal patterns of global land cover change in a [sensor-generic](sources.md) fashion.


## :seedling: Installation

This library can be installed via `pip`.

```bash
pip install earthlib
```

To install the Google Earth Engine utilities:

```bash
pip install earthlib[ee]
```

You can also clone the source repository and install it locally.

```bash
git clone https://github.com/earth-chris/earthlib.git
cd earthlib
pip install -e .
```

## :deciduous_tree: Developed by

[Christopher Anderson](https://cbanderson.info)[^1]

<a href="https://www.linkedin.com/in/christopher-b-anderson/">![LinkedIn Follow](https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white)</a>
<a href="https://scholar.google.com/citations?hl=en&user=LoGxS40AAAAJ&view_op=list_works">![Google Scholar](https://img.shields.io/badge/Google%20Scholar-%2320beff?color=1f1f18&logo=google-scholar&style=flat-square)</a>
<a href="https://orcid.org/0000-0001-7392-4368">![ORC-ID](https://img.shields.io/badge/ORCID-0000--0001--7392--4368-brightgreen)</a>
<a href="https://github.com/earth-chris">![GitHub Stars](https://img.shields.io/github/stars/earth-chris?affiliations=OWNER%2CCOLLABORATOR&style=social)</a>

This package was primarily developed during my time at the Stanford Center for Conservation Biology and at Salo Sciences.

[^1]: [Planet Labs PBC](https://www.planet.com)
