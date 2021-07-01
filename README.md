# FRAPdiff
FRAP analysis on .tif movies containing an ImageJ ROI of the bleach rectangle.
FRAPdiff estimates K_off and diffusion. Detail are described in further detail
in Gerganova et al. https://www.biorxiv.org/content/10.1101/2020.12.18.423457v3

## Example

### 1. GUI

Open a (Anaconda) command-line shell and type.
`frapdiff`
### 2. Command-line interface

Open a command-line shell and type.
`frapdiff -h`
### 3. Jupyter notebook

```python
from frapdiff import frapdiff

result_dict = frapdiff.extract_frap_profiles_and_fit(
                movie_fn,
                bleach_correction=True,
                roi_ext_factor=1.5,
                project_on='v',
                mirror='first_half',
                D_guess=0.05,
                koff_guess=0.1,
                min_l_f=8,
                max_l_f=16,
                correction_region_size=150,
                )
```

## Installation
### pip (developer, recommended)
1. Clone this repository
2. `cd frapdiff`
3. `pip install -e .`

### pip (current master)
`pip install git+https://git.ist.ac.at/csommer/frapdiff`

### Dependencies (automatically installed via pip)
numpy, pandas, tifffile, roifile, Gooey, wxPython, scipy, matplotlib


