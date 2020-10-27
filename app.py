#!/usr/bin/env python3

import datetime
import os
from pathlib import Path
import subprocess

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

from queue import huey_queue
from tasks import r_cleangrowth, r_longwide, r_ext_bmiz


# Each execution of each instance will get its own new key
SECRET_KEY = os.urandom(16)

DATASET_DIR = "dataset"
RESULT_DIR = "result"
ALLOWED_EXTENSIONS = {"csv"}
# Standard GMT, e.g. "YYYYMMDDTHHMMSSZ"
DT_FORMAT = "%Y%m%dT%H%M%SZ"

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["DATASET_DIR"] = DATASET_DIR

jobs = {}


def allowed_file(fname):
    """Verify that the uploaded file matches our extension requirement."""
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def utcnow():
    """Shorthand form for generating valid datetimes."""
    return datetime.datetime.utcnow().strftime(DT_FORMAT)


def read_state():
    """Examine the working directories for available datasets, process status,
    and results. Clean up as needed."""
    # FIXME: Refactor to read state of jobs object from queue
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
    if file.filename == "":
        flash("No dataset selected")
    if file:
        if allowed_file(file.filename):
            fname = secure_filename(file.filename)
            # Prepend a dt to avoid name collisions
            dated_fname = "%s-%s" % (utcnow(), fname)
            file.save(Path(app.config["DATASET_DIR"]) / dated_fname)
            flash("Dataset uploaded successfully.")

            # Start a queue pipeline
            pipeline = (r_cleangrowth.s(dated_fname)
                .then(r_longwide)
                .then(r_ext_bmiz)
            )
            jobs[dated_fname] = huey_queue.enqueue(pipeline)
            # TODO: options? bmi?
        else:
            flash("Dataset name should end in '.csv'")
    return redirect(url_for("index"))


@app.route("/cleaned_file/<cleaned_fname>", methods=["GET"])
def cleaned_file(cleaned_fname):
    return send_from_directory(Path(".") / RESULT_DIR, cleaned_fname)


if __name__ == "__main__":
    # Initialize dirs if not yet present
    Path(DATASET_DIR).mkdir(parents=True, exist_ok=True)
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)
    # Start a huey worker/consumer process
    # TODO: Configurable worker count
    # cmd = ["huey_consumer", "tasks.huey_queue", "-w", "2", "-k", "process"]
    cmd = ["huey_consumer", "tasks.huey_queue", "-w", "2"]
    # TODO: clean up properly on exit
    proc = subprocess.Popen(cmd)
    # TODO: properly configurable debug
    app.run(debug=False, host="0.0.0.0")
