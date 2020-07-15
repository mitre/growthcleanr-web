#!/usr/bin/env python3

import datetime
import json
import os
from pathlib import Path
import subprocess

import psutil

from flask import (
    Flask,
    flash,
    redirect,
    request,
    render_template,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename


# Each execution of each instance will get its own new key
SECRET_KEY = os.urandom(16)

DATASET_DIR = "dataset"
STATUS_DIR = "status"
RESULT_DIR = "result"
ALLOWED_EXTENSIONS = {"csv"}
# Standard GMT, e.g. "YYYYMMDDTHHMMSSZ"
DT_FORMAT = "%Y%m%dT%H%M%SZ"

app = Flask(__name__)
app.config["DATASET_DIR"] = DATASET_DIR
app.secret_key = SECRET_KEY


def allowed_file(fname):
    """Verify that the uploaded file matches our extension requirement."""
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def utcnow():
    """Shorthand form for generating valid datetimes."""
    return datetime.datetime.utcnow().strftime(DT_FORMAT)


def read_state():
    """Examine the working directories for available datasets, process status, 
    and results. Clean up as needed."""
    datasets = {}
    # Build a dataset list from DATASET_DIR
    for dataset in [ds for ds in os.listdir(DATASET_DIR) if ds.startswith("20")]:
        dt = datetime.datetime.strptime(dataset[:16], DT_FORMAT)
        fname = dataset[17:]
        datasets[dataset] = {
            "dated_fname": dataset,
            "fname": fname,
            "dt": dt.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # Examine process status, attach to dataset info
    for process in sorted(os.listdir(STATUS_DIR)):
        status_fname = Path(".") / STATUS_DIR / process
        status = json.load(open(status_fname))
        dataset_fname = status["dataset"]
        dataset = datasets[dataset_fname]
        pid = status["pid"]
        # Is there a cleaned file in results?
        result_fname = Path(".") / RESULT_DIR / f"cleaned-{dataset['dated_fname']}"
        if os.path.isfile(result_fname):
            # It's done; clean up the old status
            try:
                proc = psutil.Process(pid)
                proc.kill()
            except Exception as e:
                pass
            os.remove(status_fname)
        else:
            # Is it still running?
            # TODO: Should probably check the process name as well to be very sure
            process_exists = psutil.pid_exists(pid)
            if process_exists:
                # TODO: sneaky to modify dicts that are list members directly
                dataset["pid"] = status["pid"]
                dataset["status"] = "Pending"
            else:
                # Note: only handle failure case and cleanup here; success case
                # will be dealt with under results below
                dataset["status"] = "Error"
                os.remove(status_fname)

    # Build result file list, format = "cleaned-datetime-origname.csv"
    for result in os.listdir(RESULT_DIR):
        dataset_fname = result[8:]
        dataset = datasets[dataset_fname]
        dataset["cleaned_fname"] = result
        # Handle completed files
        dataset["status"] = "Done"

    # Return files w/status, associated results ordered by date/time
    return datasets


@app.route("/")
def index():
    datasets = read_state()
    # sort by dt
    datasets = [v for k, v in sorted(datasets.items())]
    return render_template("index.j2", datasets=datasets)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No dataset part found")
        return redirect(request.url)
    file = request.files["file"]
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == "":
        flash("No dataset selected")
    if file:
        if allowed_file(file.filename):
            fname = secure_filename(file.filename)
            # Prepend a dt to avoid name collisions
            dated_fname = "%s-%s" % (utcnow(), fname)
            file.save(Path(app.config["DATASET_DIR"]) / dated_fname)
            flash("Dataset uploaded successfully.")
            # Start a detached subprocess to run gc on the file
            cmd = [
                "gcdriver.R",
                "--quietly",
                Path(".") / DATASET_DIR / dated_fname,
                Path(".") / RESULT_DIR / f"cleaned-{dated_fname}",
            ]
            proc = subprocess.Popen(cmd)
            # Write PID info & filename to STATUS_DIR
            status = {"pid": proc.pid, "dataset": dated_fname}
            status_fname = Path(".") / STATUS_DIR / f"status-{dated_fname}"
            json.dump(status, open(status_fname, "w"))
        else:
            flash("Dataset name should end in '.csv'")
    return redirect(url_for("index"))


@app.route("/cleaned_file/<cleaned_fname>", methods=["GET"])
def cleaned_file(cleaned_fname):
    return send_from_directory(Path(".") / RESULT_DIR, cleaned_fname)


if __name__ == "__main__":
    Path(DATASET_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATUS_DIR).mkdir(parents=True, exist_ok=True)
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)
    app.run(debug=True, host="0.0.0.0")
