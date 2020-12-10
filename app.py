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
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", False)

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
    datasets = {}
    for job in jobs.keys():
        dt = datetime.datetime.strptime(job[:16], DT_FORMAT)
        fname = job[17:]
        status = jobs[job].get()
        datasets[job] = {
            "dated_fname": job,
            "fname": fname,
            "dt": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
        }
        if type(status) == type([]):
            # This was a pipeline w/bmi
            if status[0] is None:
                # cleaning is not yet done
                datasets[job]["cleaned_fname"] = ""
            else:
                # cleaning is done
                # "dt-", 1 to remove the slash
                # TODO: does pathlib make this simpler?
                cleaned_fname = str(status[0])[len(RESULT_DIR) + 1 :]
                datasets[job]["cleaned_fname"] = cleaned_fname
            if status[2] is None:
                # bmi is not yet done
                datasets[job]["bmi_fname"] = ""
            else:
                # bmi is done
                bmi_fname = str(status[2])[len(RESULT_DIR) + 1 :]
                datasets[job]["bmi_fname"] = bmi_fname
        else:
            # Not a pipeline, just cleaning
            # TODO: verify, can this happen?
            cleaned_fname = str(status)[len(RESULT_DIR) + 1 :]
            datasets[job]["cleaned_fname"] = cleaned_fname

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

            if request.form.get("calculate-bmi", "no") == "yes":
                options = {}
                bmi_radio = request.form.get("bmi-radio", "include")
                if bmi_radio == "include":
                    # no further options to handle, use default longwide()
                    pass
                elif bmi_radio == "all":
                    options["include_all"] = True
                elif bmi_radio == "choose":
                    inclusion_types = []
                    for t in [
                        "Include",
                        "Exclude-Carried-Forward",
                        "Exclude-Duplicate",
                        "Exclude-Too-Many-Errors",
                        "Exclude-Min-Height-Change",
                        "Exclude-Max-Height-Change",
                        "Exclude-Min-Weight-Change",
                        "Exclude-Max-Weight-Change",
                    ]:
                        if request.form.get(t, None):
                            inclusion_types.append(t)
                    options["inclusion_types"] = inclusion_types

                # Start a queue pipeline
                pipeline = (
                    r_cleangrowth.s(dated_fname)
                    .then(r_longwide, options=options)
                    .then(r_ext_bmiz)
                )
            else:
                # Does not require a pipeline, but use one for consistency
                # of result
                pipeline = r_cleangrowth.s(dated_fname)
            jobs[dated_fname] = huey_queue.enqueue(pipeline)
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
    app.run(debug=app.config["DEBUG"], host="0.0.0.0")
