# FRAPdiff
FRAP analysis on .tif movies containing an ImageJ ROI of the bleach rectangle.
FRAPdiff estimates K_off and diffusion. Detail are described in further detail
in [Radler et al.](https://www.biorxiv.org/content/10.1101/2021.11.08.467681v1.article-info)

FRAPdiff is based on a [fitting routine](https://github.com/davidmrutkowski/1DReflectingDiffusion) developed and kindly shared by David	Rutkowski and colleagues. 


## Example

### 1. GUI

Open a (Anaconda) command-line shell and type.
`frapdiff`

### 2. Jupyter notebook

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

### 3. Command-line interface

Open a command-line shell and type.
`frapdiff -h`
This will show the command line usage and all
```
usage: frapdiff [-h] -d INPUT_DIR [-r] -o OUTPUT [-b] [-bs CORRECTION_REGION_SIZE] [-p {vertical,horizontal}]
                [-e EXTEND] [-m {No,first_half,second_half}] [-D D_INITIAL] [-K KOFF_INITIAL] [-min_lf MINIMUM_LF]
                [-max_lf MAXIMUM_LF]

FRAP analysis on .tif movies containing an ImageJ ROI of the bleach rectangle.
FRAPdiff estimates K_off and diffusion. Detail are described in further detail
in [Radler et al.](https://www.biorxiv.org/content/10.1101/2021.11.08.467681v1.article-info)

optional arguments:
  -h, --help            show this help message and exit

General:
  -d INPUT_DIR, --input_dir INPUT_DIR
                        Input Folder containing movies (.tif)
  -r, --recursive       Search movies in input folder recursively
  -o OUTPUT, --output OUTPUT
                        Output file (.tab)

Bleach correction:
  -b, --bleach_correction
                        Perfom simple, ratio-based bleach correction in upper-left window
  -bs CORRECTION_REGION_SIZE, --correction_region_size CORRECTION_REGION_SIZE
                        Size of bleach-correction window (upper left corner)

FRAP region:
  -p {vertical,horizontal}, --project_values {vertical,horizontal}
  -e EXTEND, --extend EXTEND
                        Extend original FRAP window by this factor to both sides each.
  -m {No,first_half,second_half}, --mirror_values {No,first_half,second_half}
                        Mirror intensity values. Use, when original profiles are not symmetric.

Fitting:
  -D D_INITIAL, --D_initial D_INITIAL
                        Initial guess for diffusion
  -K KOFF_INITIAL, --Koff_initial KOFF_INITIAL
                        Initial guess for K_off
  -min_lf MINIMUM_LF, --minimum_Lf MINIMUM_LF
                        Minimum L_f to restrict solver to reasonable values
  -max_lf MAXIMUM_LF, --maximum_Lf MAXIMUM_LF
                        Maximum L_f to restrict solver to reasonable values
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



