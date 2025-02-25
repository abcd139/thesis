"""
Basic watcher for continuous EEG recording, with some visualization (soonTM).

eegnb stuff is based on: https://neurotechx.github.io/eeg-notebooks/auto_examples/visual_n170/00x__n170_run_experiment.html#sphx-glr-auto-examples-visual-n170-00x-n170-run-experiment-py
pylsl stuff is based on: https://github.com/labstreaminglayer/liblsl-Python/blob/master/pylsl/examples/ReceiveAndPlot.py
"""

from typing import List, Optional
from datetime import datetime, timezone
from time import time, sleep
from pathlib import Path
import logging
import subprocess

import click
import pylsl
import pyqtgraph as pg
import coloredlogs
from pyqtgraph.Qt import QtCore, QtGui

from eegwatch.util import print_statusline
from .devices import EEGDevice, all_devices

experiment = "test"

# For plotting
UPDATE_INTERVAL = 60  # ms between screen updates


logger = logging.getLogger(__name__)


def notify(summary: str, body: str, urgency: str = "normal"):
    """
    ``urgency`` can be one of ['low', 'normal', 'critical']
    """
    subprocess.call(
        ["notify-send", summary, body, "--app-name", "eegwatch", "--urgency", urgency]
    )


@click.group(help="Collect EEG data during device usage")
def main():
    logging.basicConfig(level=logging.INFO)
    coloredlogs.install(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("pygatt").setLevel(logging.WARNING)


@main.command()
@click.option(
    "--device",
    type=click.Choice(all_devices),
    default="museS",
    help="Which device to use",
)
@click.option(
    "--duration",
    type=int,
    default=5 * 60,
    help="Duration to record for",
)
@click.option(
    "--subject-id",
    type=int,
    default=0,
    help="Subject ID to store recording as",
)
@click.option(
    "--loop/--no-loop", is_flag=True, default=True, help="Wether to loop recording"
)
@click.option(
    "extras",
    "--extra",
    type=click.Choice(["PPG", "ACC", "GYRO"]),
    multiple=True,
    default=[],
    help="Extra sources to record (only supported for Muse devices)",
)
def connect(
    device: str, duration: float, subject_id: int, loop: bool, extras: List[str]
):
    """Connect to device and start streaming & recording"""
    from .util import generate_save_fn

    eeg_device = EEGDevice.create(device_name=device)

    times_ran = 0
    while loop or times_ran < 1:
        # Create save file name
        save_fn = generate_save_fn(
            device, experiment, subject_id=subject_id, session_nb=1
        )

        logger.info(f"Recording to {save_fn}")
        try:
            eeg_device.start(
                save_fn, duration=duration, extras={e: True for e in extras}
            )
        except IndexError:
            logger.exception("Error while starting recording, trying again in 5s...")
            sleep(5)
            continue
        except Exception as e:
            if "No Muses found" in str(e):
                msg = "No Muses found, trying again in 5s..."
                logger.warning(msg)
                notify("Couldn't connect", msg)
                sleep(5)
                continue
            else:
                raise

        loud = True
        started = time()
        stop = started + duration
        print(f"Starting recording for {duration}s")
        while time() < stop:
            sleep(1)
            last_modified = _check_recording_status(save_fn)
            if last_modified is None:
                print("Waiting for data to be written to file...")
            elif last_modified > 10:
                print("Data was written more than 10s ago, perhaps the stream died?")

            if loud:
                progress = time() - started
                status = (
                    "fresh"
                    if last_modified is not None and last_modified < 3
                    else "stale"
                )
                print_statusline(
                    f"Recording #{times_ran + 1}: {round(progress)}/{duration}s ({status})"
                )
        print("Done!")
        logger.info("Done recording")
        times_ran += 1


def _check_recording_status(path: Path) -> Optional[float]:
    """Returns the time since file was written, or None if it doesn't exist."""
    if path.exists():
        now = datetime.now()
        return now.timestamp() - path.stat().st_mtime
    else:
        return None


@main.command()
@click.option(
    "--device",
    "device_name",
    type=click.Choice(all_devices),
    default="museS",
    help="Which device to use",
)
def check(device_name: str):
    """Checks signal quality"""
    device = EEGDevice.create(device_name)

    last_good = False
    last_check = time()
    last_bads: List[str] = []
    while True:
        # Check every 0.5s
        if time() > last_check + 0.5:
            bads = device.check(max_uv_abs=200)
            all_good = len(bads) == 0
            if all_good:
                if not last_good:
                    logger.info("All channels good!")
            else:
                if bads != last_bads:
                    logger.warning(
                        "Warning, bad signal for channels: " + ", ".join(bads)
                    )
            last_good = all_good
            last_check = time()
            last_bads = bads


@main.command()
@click.option(
    "--device",
    type=click.Choice(all_devices),
    default="museS",
    help="Which device to use",
)
def plot(device: str):
    """Plot existing LSL stream"""
    from eegwatch.lslutils import PULL_INTERVAL, PLOT_DURATION, _get_inlets

    assert device.startswith("muse"), "Only Muse devices supported for now"
    # print(eeg_device)

    # TODO: Get the live data and do basic stuff to check signal quality, such as:
    #        - Checking signal variance.
    #        - Transforming into the frequency domain.

    offset = datetime.now(tz=timezone.utc).timestamp() - pylsl.local_clock()

    def local_clock_to_timestamp(local_clock):
        return local_clock + offset

    streams = pylsl.resolve_bypred("name='Muse' and type='EEG'", timeout=10)
    if not streams:
        print("No stream could be found")
        exit(1)

    for s in streams:
        logger.debug(streams)

    # Create the pyqtgraph window
    pw = pg.plot(title="LSL Plot")
    plt = pw.getPlotItem()
    plt.enableAutoRange(x=False, y=True)

    inlets = _get_inlets(plt=plt)

    def scroll():
        """Move the view so the data appears to scroll"""
        # We show data only up to a timepoint shortly before the current time
        # so new data doesn't suddenly appear in the middle of the plot
        fudge_factor = PULL_INTERVAL * 0.002
        plot_time = local_clock_to_timestamp(pylsl.local_clock())
        pw.setXRange(plot_time - PLOT_DURATION + fudge_factor, plot_time - fudge_factor)

    def update():
        # Read data from the inlet. Use a timeout of 0.0 so we don't block GUI interaction.
        mintime = local_clock_to_timestamp(pylsl.local_clock()) - PLOT_DURATION
        # call pull_and_plot for each inlet.
        # Special handling of inlet types (markers, continuous data) is done in
        # the different inlet classes.
        for inlet in inlets:
            inlet.pull_and_plot(mintime, plt)

    # create a timer that will move the view every update_interval ms
    update_timer = QtCore.QTimer()
    update_timer.timeout.connect(scroll)
    update_timer.start(UPDATE_INTERVAL)

    # create a timer that will pull and add new data occasionally
    pull_timer = QtCore.QTimer()
    pull_timer.timeout.connect(update)
    pull_timer.start(PULL_INTERVAL)

    import sys

    # Start Qt event loop unless running in interactive mode or using pyside.
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()


if __name__ == "__main__":
    main()
