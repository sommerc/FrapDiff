import os
import re
import sys
import json
import numpy
import pandas
import roifile
import tifffile
import traceback

from pathlib import Path
from matplotlib import pyplot as plt
from gooey import Gooey, GooeyParser

from .reflecting_diffusion_fitter import run_fitter


def get_physical_units_from_imagej_tif(tif_fn):
    with tifffile.TiffFile(tif_fn) as tif:
        assert tif.is_imagej
        tags = tif.pages[0].tags
        y_resolution = tags["YResolution"].value
        finterval = tif.imagej_metadata["finterval"]

        pixel_size = y_resolution[1] / y_resolution[0]
        return pixel_size, finterval


def simple_bleach_correction(mov, win_size):
    roi_values = mov[:, :win_size, :win_size]
    roi_values_mean = roi_values.mean(axis=(1, 2))

    mov_corr = (mov.T / roi_values_mean).T
    return mov_corr


def extract_frap_profiles_and_fit(
    mov_fn,
    bleach_correction=True,
    roi_ext_factor=1.5,
    project_on="v",
    mirror="first_half",
    D_guess=0.05,
    koff_guess=0.1,
    min_l_f=8,
    max_l_f=16,
    correction_region_size=150,
):

    roi = roifile.ImagejRoi.fromfile(str(mov_fn))
    if len(roi) == 0:
        extra_roi_file = str(mov_fn)[:-4] + ".roi"
        if os.path.exists(extra_roi_file):
            roi = roifile.ImagejRoi.fromfile(extra_roi_file)
            print("Cannot read ROI from tiff file, using .roi file...")
        else:
            raise RuntimeError("No ROI found in '{mov_fn}' or '{extra_roi_file}'")
    else:
        roi = roi[0]

    pixel_size, finterval = get_physical_units_from_imagej_tif(str(mov_fn))

    mov = tifffile.imread(str(mov_fn))
    if bleach_correction:
        mov = simple_bleach_correction(mov, correction_region_size)

    if project_on == "v":
        roi_height = roi.bottom - roi.top
        roi_extension = int(roi_height * roi_ext_factor)

        roi_values = mov[
            :,
            max(roi.top - roi_extension, 0) : min(
                roi.bottom + roi_extension, mov.shape[1] - 1
            ),
            roi.left : roi.right,
        ]
        roi_values_projected = roi_values.mean(axis=2)

    elif project_on == "h":
        roi_width = roi.right - roi.left
        roi_extension = int(roi_width * roi_ext_factor)

        roi_values = mov[
            :,
            roi.top : roi.bottom,
            max(roi.left - roi_extension, 0) : min(
                roi.right + roi_extension, mov.shape[2] - 1
            ),
        ]
        roi_values_projected = roi_values.mean(axis=1)

    else:
        raise ValueError(f"Value for 'project_on' not understood. Use 'v' or 'h'")

    # Find frame of bleaching
    time_bleach = numpy.argmax(numpy.abs(numpy.diff(roi_values_projected.mean(1)))) + 1

    roi_values_projected = (
        roi_values_projected / roi_values_projected[time_bleach - 1, :].mean()
    )

    data = roi_values_projected

    if mirror == "first_half":
        data1 = data[:, : (data.shape[1] // 2)]
        data = numpy.c_[data1, numpy.fliplr(data1)]
    elif mirror == "second_half":
        data2 = data[:, (data.shape[1] // 2) :]
        data = numpy.c_[numpy.fliplr(data2), data2]
    elif mirror.lower() == "no":
        pass
    else:
        raise ValueError(
            f"mirror parameter not understood. Use 'first_half', 'second_half', or 'no"
        )

    I0 = data[time_bleach - 1, :].mean()

    data = data[time_bleach:, :]

    # tifffile.imsave(mov_fn[:-4] + "_bc.tiff", (mov / I0).astype("float32")[:, None, ...])

    # plt.figure()
    # for line in data:
    #     plt.plot(line)

    # plt.show()

    # print("I0", I0)
    # print("time of bleach", time_bleach)

    data = pandas.DataFrame(data.T)
    data.insert(0, "loc", pixel_size * numpy.arange(data.shape[0]))

    print("  -- create table with projected ROI values")
    data_fn = str(mov_fn)[:-4] + f"_frap_recovery_proj.txt"
    data.to_csv(data_fn, "\t", header=False, index=False)

    result_fn = str(mov_fn)[:-4] + f"_results.json"
    print("  -- run fit routine...")

    result = run_fitter(
        data_fn,
        mov_fn.stem,
        I0=I0,
        t_step_size=float(finterval),
        D_guess=D_guess,
        koff_guess=koff_guess,
        min_l_f=min_l_f,
        max_l_f=max_l_f,
    )

    result["frameInteval"] = float(finterval)
    result["pixelSize"] = float(pixel_size)
    result["frameOfFrap"] = int(time_bleach)
    result["I0"] = I0
    result["File"] = str(mov_fn)

    print("  -- saving results to json")
    with open(result_fn, "w") as fh:
        json.dump(result, fh)

    return result


# this needs to be *before* the @Gooey decorator!
# (this code allows to only use Gooey when no arguments are passed to the script)
if len(sys.argv) >= 2:
    if not "--ignore-gooey" in sys.argv:
        sys.argv.append("--ignore-gooey")


@Gooey(
    program_name="FRAPdiff",
    program_description="""FRAP and diffusion analysis on .tif movies containing an ImageJ ROI of the bleach rectangle.""",
    tabbed_groups=True,
    target="frapdiff",  ### https://github.com/chriskiehl/Gooey/issues/219
    progress_regex=r"^#\s(?P<current>\d+)/(?P<total>\d+)\s###.*",
    progress_expr="current / total * 100",
    timing_options={
        "show_time_remaining": True,
        "hide_time_remaining_on_complete": True,
    },
)
def main_cli():
    """
    input_dir
    output
    recursive :: True
    bleach_correction :: True
    correction_region_size :: 150
    project_values :: vertical
    extend :: 1.5
    mirror_values :: first_half
    D_initial :: 0.05
    Koff_initial :: 0.1
    minimum_Lf :: 8.0
    maximum_Lf :: 16.0

    """

    parser = GooeyParser(
        description="""FRAP analysis on .tif movies containing an ImageJ ROI
                       of the bleach rectangle. FRAPdiff estimates K_off and
                       Diffusion parameters. Detail are described in further
                       detail in Gerganova et al. https://www.biorxiv.org/content/10.1101/2020.12.18.423457v3
                       """
    )
    in_movies_parser = parser.add_argument_group("General")

    in_movies_parser.add_argument(
        "-d",
        "--input_dir",
        required=True,
        help="Input Folder containing movies (.tif)",
        widget="DirChooser",
    )

    in_movies_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        gooey_options={"initial_value": True},
        help="Search movies in input folder recursively",
        default=False
    )

    in_movies_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file (.tab)",
        widget="FileSaver",
        gooey_options={
            "wildcard": "TAB (*.tab)|*.tab|" "All files (*.*)|*.*",
            "default_file": "results.tab",
        },
    )

    bleach_corr_parser = parser.add_argument_group("Bleach correction")

    bleach_corr_parser.add_argument(
        "-b",
        "--bleach_correction",
        action="store_true",
        gooey_options={"initial_value": True},
        help="Perfom simple, ratio-based bleach correction in upper-left window",
        default=False
    )

    bleach_corr_parser.add_argument(
        "-bs",
        "--correction_region_size",
        widget="IntegerField",
        gooey_options={"min": 0, "max": 999, "increment": 1, "initial_value": 150},
        help="Size of bleach-correction window (upper left corner)",
        type=int,
        default=150
    )

    frap_region_parser = parser.add_argument_group("FRAP region")

    frap_region_parser.add_argument(
        "-p",
        "--project_values",
        widget="Dropdown",
        choices=["vertical", "horizontal"],
        gooey_options={"initial_value": "vertical"},
        default="vertical",
        type=str,
    )

    frap_region_parser.add_argument(
        "-e",
        "--extend",
        widget="DecimalField",
        gooey_options={"min": 0, "max": 3.0, "increment": 0.1, "initial_value": 1.5},
        help="Extend original FRAP window by this factor to both sides each.",
        type=float,
        default=1.5
    )

    frap_region_parser.add_argument(
        "-m",
        "--mirror_values",
        widget="Dropdown",
        choices=["No", "first_half", "second_half"],
        help="Mirror intensity values. Use, when original profiles are not symmetric.",
        gooey_options={"initial_value": "first_half"},
        type=str,
        default="first_half"
    )

    fitting_parser = parser.add_argument_group("Fitting")

    fitting_parser.add_argument(
        "-D",
        "--D_initial",
        widget="DecimalField",
        gooey_options={"min": 0, "max": 3.0, "increment": 0.01, "initial_value": 0.05},
        help="Initial guess for diffusion",
        type=float,
        default=0.05
    )

    fitting_parser.add_argument(
        "-K",
        "--Koff_initial",
        widget="DecimalField",
        gooey_options={"min": 0, "max": 3.0, "increment": 0.01, "initial_value": 0.1},
        help="Initial guess for K_off",
        type=float,
        default=0.1
    )

    fitting_parser.add_argument(
        "-min_lf",
        "--minimum_Lf",
        widget="DecimalField",
        gooey_options={"min": 0, "max": 20.0, "increment": 1.0, "initial_value": 8},
        help="Minimum L_f to restrict solver to reasonable values",
        type=float,
        default=8
    )

    fitting_parser.add_argument(
        "-max_lf",
        "--maximum_Lf",
        widget="DecimalField",
        gooey_options={"min": 0, "max": 20.0, "increment": 1.0, "initial_value": 16},
        help="Maximum L_f to restrict solver to reasonable values",
        type=float,
        default=16
    )

    args = parser.parse_args()

    for key, value in vars(args).items():
        print(f"{key} :: {value}")

    if args.recursive:
        all_mov_fns = [path for path in Path(args.input_dir).rglob("*.tif")]
    else:
        all_mov_fns = [path for path in Path(args.input_dir).glob("*.tif")]

    results = []
    n = len(all_mov_fns)
    for i, mov_fn in enumerate(all_mov_fns):
        print(f"\n# {i+1}/{n} ### {mov_fn}")
        sys.stdout.flush()
        try:
            result_dict = extract_frap_profiles_and_fit(
                mov_fn=mov_fn,
                bleach_correction=args.bleach_correction,
                roi_ext_factor=args.extend,
                project_on=args.project_values[0],
                mirror=args.mirror_values,
                D_guess=args.D_initial,
                koff_guess=args.Koff_initial,
                min_l_f=args.minimum_Lf,
                max_l_f=args.maximum_Lf,
                correction_region_size=args.correction_region_size,
            )
            results.append(result_dict)
        except:

            print(f"\nERROR for file '{mov_fn}'\n")
            traceback.print_exc()
            print()

    tab = pandas.DataFrame(results)
    tab.to_csv(args.output, sep="\t")


if __name__ == "__main__":
    main_cli()

