import pathlib
from setuptools import setup, find_packages

# The directory containing this file
_this_dir = pathlib.Path(__file__).parent

# The text of the README file
long_description = (_this_dir / "README.md").read_text()

# Exec version file
exec((_this_dir / "frapdiff" / "version.py").read_text())

print(find_packages())

setup(
    name="frapdiff",
    packages=find_packages(include=["frapdiff", "frapdiff.*"]),
    version=__version__,
    description="FRAPdiff",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.ist.ac.at/csommer/frapdiff",
    license="GPL3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
    ],
    entry_points={"console_scripts": ["frapdiff=frapdiff.frapdiff:main_cli"]},
    author="Christoph Sommer",
    author_email="christoph.sommer23@gmail.com",
    install_requires=["numpy", "pandas", "tifffile", "roifile", "Gooey"],
)

