# growthcleanr-web

A simple web interface to the
[growthcleanr](https://github.com/carriedaymont/growthcleanr) R package for cleaning
clinical height and weight measurements. Presents a simple web interface for uploading
CSV data, cleaning that data with growthcleanr, and making results available.

This application is intended for use in a containerized setting using Docker.

Written in Python 3 with the [Flask](https://flask.palletsprojects.com/) web framework.

## Installation

An up-to-date installation of [Docker](https://www.docker.com/) is required.

To run the webapp using Docker, run the image directly, specifying a port
mapping:

```bash
% docker run -it -p 5000:5000 mitre/growthcleanr-web:latest
```

After the image is downloaded and run, visit http://localhost:5000/ in any
browser to use the application.

## Usage

This application receives CSV data files over its web interface,
and then cleans data in those files using `growthcleanr`'s
`cleangrowth()` function. With a data file in the [format specified
by
growthcleanr](https://github.com/carriedaymont/growthcleanr#data-preparation),
use the app's Upload function to post your CSV file, and click
"Refresh this page" until you see your that result dataset is done.
Click the result file to download!

Note that the result files will have the word "cleaned" and a date/time
prepended. This helps to avoid name conflicts if two files with the same name
are uploaded.

## Development

This application was developed using Python 3.8. To develop locally, in a clean
environment (e.g., a virtualenv), clone the repository, switch to the new directory, and
install dependencies:

```bash
% https://github.com/mitre/growthcleanr-web.git
% cd growthcleanr-web
% pip install -r requirements.txt
```

The application assumes that R and the R package
[growthcleanr](https://github.com/carriedaymont/growthcleanr) are installed, and
`gcdriver.R` (from growthcleanr's `exec` dir) is executable as
`/usr/local/bin/gcdriver.R`.

With those pieces in place, start the application:

```bash
% python app.py
```

You should now be able to visit the application at http://localhost:5000/.

Note that when it first starts, the application will create the `dataset`, `status`, and
`result` directories if necessary. New uploads land in `dataset` with a date/time
prefix. Once a `gcdriver` process starts, a status file is created in `status` to track
its process id (larger datasets can result in long-running processes of several minutes
or more). When a process completes successfully, a results file will be written to
`result` with the `cleaned-` prefix.

On every load of the index page in a browser, these three directories are scanned for
determine dataset and process state. Status files for completed or failed processes
should be cleaned up at this time.

## Notice

Copyright 2020 The MITRE Corporation.

Approved for Public Release; Distribution Unlimited. Case Number 19-2008
