from pathlib import Path

from rpy2 import robjects

from queue import huey_queue

# FIXME - external config, please
DATASET_DIR = "dataset"
RESULT_DIR = "result"


@huey_queue.task()
def r_cleangrowth(fname, options={}):
    dataset_fname = Path(DATASET_DIR) / fname
    result_fname = str(Path(RESULT_DIR) / f"{str(fname)[:-4]}-cleaned.csv")
    robjects.r(f"""
       library(data.table)
       library(growthcleanr)
       d <- fread("{str(dataset_fname)}")
       setkey(d, subjid, param, agedays)
       d[, clean_value:=cleangrowth(subjid, param, agedays, sex, measurement)]
       fwrite(d, "{str(result_fname)}")
       """)
    return result_fname


@huey_queue.task()
def r_longwide(fname, options={}):
    # Note: will already have "RESULT_DIR/" prepended
    result_fname = f"{str(fname)[:-4]}-wide.csv"
    # TODO: pass in exclusion options correctly
    robjects.r(f"""
        library(data.table)
        library(growthcleanr)
        d <- fread("{fname}")
        d_wide <- longwide(d)
        fwrite(d_wide, "{str(result_fname)}")
        """)
    return result_fname


@huey_queue.task()
def r_ext_bmiz(fname, options={}):
    # Using -9 to remove all of "-wide.csv"
    result_fname = f"{str(fname)[:-9]}-bmi.csv"
    robjects.r(f"""
        library(data.table)
        library(growthcleanr)
        d <- fread("{fname}")
        d_bmi <- ext_bmiz(d)
        fwrite(d_bmi, "{str(result_fname)}")
    """)
    return result_fname
