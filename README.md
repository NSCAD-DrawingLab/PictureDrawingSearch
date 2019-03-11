# PictureDrawingSearch

PictureDrawingSearch is an experiment program for a study looking at the effects of different types of visual masking (central, peripheral, and none) on drawing from observation.

![picture_drawing_screenshot](https://drive.google.com/uc?id=1Hwx9caCncjJtJYBQ8-lWGSxdRvAuGmpY)

## Requirements

PictureDrawingSearch is programmed in Python 2.7 using the [KLibs framework](https://github.com/a-hurst/klibs). It has been developed and tested on macOS (10.9 through 10.13), but should also work with minimal hassle on computers running [Ubuntu](https://www.ubuntu.com/download/desktop) or [Debian](https://www.debian.org/distrib/) Linux. It is not currently compatible with any version of Windows, nor will it run under the [Windows Subsystem for Linux](https://msdn.microsoft.com/en-us/commandline/wsl/install_guide).

The experiment is designed to be run with an EyeLink eye tracker, but it can be downloaded and tested without one (using the mouse cursor as a stand-in for gaze position) by adding the flag `-ELx` to the `klibs run` command.

## Getting Started

### Installation

First, you will need to install the KLibs framework by following the instructions [here](https://github.com/a-hurst/klibs).

Then, you can then download and install the experiment program with the following commands (replacing `~/Downloads` with the path to the folder where you would like to put the program folder):

```
cd ~/Downloads
git clone https://github.com/NSCAD-DrawingLab/PicutreDrawingSearch.git
```

### Running the Experiment

PictureDrawingSearch is a KLibs experiment, meaning that it is run using the `klibs` command at the terminal (running the 'experiment.py' file using python directly will not work).

To run the experiment, navigate to the PictureDrawingSearch folder in Terminal and run `klibs run [screensize]`,
replacing `[screensize]` with the diagonal size of your display in inches (e.g. `klibs run 24` for a 24-inch monitor). If you just want to test the program out for yourself and skip demographics collection, you can add the `-d` flag to the end of the command to launch the experiment in development mode.