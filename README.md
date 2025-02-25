MSc Thesis
==========

[![GitHub Actions badge](https://github.com/ErikBjare/thesis/workflows/Test/badge.svg)](https://github.com/ErikBjare/thesis/actions)
[![Code coverage](https://codecov.io/gh/ErikBjare/thesis/branch/master/graph/badge.svg)](https://codecov.io/gh/ErikBjare/thesis)
[![Typechecking: Mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

My MSc thesis on "Classifying brain activity using electroencephalography and automated time tracking" (working title).

It is very much a work-in-progress. Progress is tracked using the [GitHub Projects board](https://github.com/ErikBjare/thesis/projects/1).

# Usage

Setting it up:

 - Ensure you have Python 3.7+ and `poetry` installed
 - Install dependencies with `poetry install`

Collecting data:

 - Run `eegwatch --help` for instructions on how to collect EEG data
 - Run [ActivityWatch](https://activitywatch.net) to collect device activity data
 - Run the codeprose task in [eeg-notebooks][eegnb] to collect data for the code vs prose task
     - Install eeg-notebooks with `pip install git+`
     - Run the codeprose task with `eegnb runexp -ex visual-codeprose -subject X`

Running classifier:

 - Run `./scripts/query_aw.py` to collect labels from the running ActivityWatch instance
   - You probably want to adjust the categorization rules embedded in the file
 - (TODO) Run `eegclassify --help` for instructions on how to train and run the classifier

# Devices

I've worked with multiple devices, but the experiments were performed using the Muse S, which is therefore the best-supported device.

 - Muse S 
   - PPG support (experimental)
 - Neurosity Notion 1 & 2
   - Thanks to [@andrewjaykeller](https://github.com/andrewjaykeller) at [@neurosity](https://github.com/neurosity) for sending me a refurbished Notion 1 to test with!
 - Neurosity Crown
 - OpenBCI Cyton
 - In theory: any device supported by Brainflow or muse-lsl

# Notebooks

Code notebooks are built in CI and available at:

 - [Main][nbmain] - primary notebook for the thesis, where we train a classifier for the code vs prose comprehension task.
 - [Signal][nbsignal] - for signal filtering and quality checking.
 - [Activity][nbactivity] - for classification of device activities.
 - [PPG][nbppg] - for a basic PPG analysis.

[nbmain]:       https://erik.bjareholt.com/thesis/Main.html
[nbsignal]:     https://erik.bjareholt.com/thesis/Signal.html
[nbactivity]:   https://erik.bjareholt.com/thesis/Activity.html
[nbppg]:        https://erik.bjareholt.com/thesis/PPG.html

# Writing

The latest version of the writing can be downloaded at:

 - Thesis report: [erik.bjareholt.com/thesis/thesis.pdf][thesis]
 - Goal document: [erik.bjareholt.com/thesis/goaldoc.pdf][goaldoc]
 - Presentation: [erik.bjareholt.com/thesis/presentation.pdf][presentation]
 - Popular scientific article (Swedish): [erik.bjareholt.com/thesis/popsci.pdf][popsci]

# Acknowledgements

See the Acknowledgements section in the [thesis][thesis].

[thesis]: https://erik.bjareholt.com/thesis/thesis.pdf
[goaldoc]: https://erik.bjareholt.com/thesis/goaldocument.pdf
[presentation]: https://erik.bjareholt.com/thesis/presentation.pdf
[popsci]: https://erik.bjareholt.com/thesis/popsci.pdf
[eegnb]: https://github.com/NeuroTechX/eeg-notebooks
