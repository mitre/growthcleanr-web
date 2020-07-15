# growthcleanr-web

A simple web interface to the [growthcleanr](https://github.com/carriedaymont/growthcleanr) R package for cleaning clinical height and weight measurements.

Presents a simple web interface for uploading CSV data, cleaning that data with
growthcleanr, and making results available.

This application is intended for use in a containerized setting using Docker.

Written in Python 3 with the Flask web framework.

## Installation

An up-to-date installation of [Docker](https://www.docker.com/) is required.

To run the webapp using Docker, run the image directly, specifying a port
mapping:

```bash
% docker run -it -p 8888:8888 dchud/growthcleanr-web:latest 
```

After the image is downloaded and run, visit http://localhost:8888/ in any
browser to use the application.

## Usage

This application receives CSV data files over its web interface, and then cleans
data in those files using `growthcleanr`'s `cleangrowth()` function. With a
data file in the [format specified by growthcleanr](https://github.com/carriedaymont/growthcleanr#data-preparation), use the app's Upload function
to post your CSV file, and click "Refresh this page" until you see your that result
dataset is done. Click the result file to download!

Note that the result files will have the word "cleaned" and a date/time
prepended. This helps to avoid name conflicts if two files with the same name
are uploaded.


## Notice

Copyright 2020 The MITRE Corporation.

Approved for Public Release; Distribution Unlimited. Case Number 19-2008
