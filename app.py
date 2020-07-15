#!/usr/bin/env python3

from pathlib import Path

from flask import Flask, request, redirect, render_template, url_for, flash
from werkzeug.utils import secure_filename

SECRET_KEY = b"ZX\xfdN\x1a\xc4O\x92\x0f2W\x98q\xabu\x1eWvJ\xf4\xb9\xcd?T"

DATASETS_DIR = "datasets"
STATUS_DIR = "status"
RESULTS_DIR = "results"
ALLOWED_EXTENSIONS = {"csv"}

app = Flask(__name__)
app.config["DATASETS_DIR"] = DATASETS_DIR
app.secret_key = SECRET_KEY


def allowed_file(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.j2")


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
            filename = secure_filename(file.filename)
            file.save(Path(app.config["DATASETS_DIR"]) / filename)
            flash("Dataset uploaded successfully.")
        else:
            flash("Dataset name should end in '.csv'")
    return redirect(url_for("index"))


if __name__ == "__main__":
    Path(DATASETS_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATUS_DIR).mkdir(parents=True, exist_ok=True)
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    app.run(debug=True, host="0.0.0.0")
