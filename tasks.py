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

    # Handle cleangrowth() options
    include_carryforward = ""
    if options.get("include-carryforward", False):
        include_carryforward = ", include.carryforward=TRUE"

    recover_unit_error = ""
    if options.get("recover-unit-error", False):
        recover_unit_error = ", recover.unit.error=TRUE"

    save_medians = ""
    if options.get("save-medians", False):
        sdmedian_fname = str(Path(RESULT_DIR) / f"{str(fname)[:-4]}-medians.csv")
        save_medians = f", sdmedian.filename='{sdmedian_fname}'"

    save_recenter = ""
    if options.get("save-recenter", False):
        sdrecenter_fname = str(Path(RESULT_DIR) / f"{str(fname)[:-4]}-recenter.csv")
        save_recenter = f", sdrecentered.filename='{sdrecenter_fname}'"

    robjects.r(
        f"""
        library(data.table)
        library(growthcleanr)
        d <- fread("{str(dataset_fname)}")
        setkey(d, subjid, param, agedays)
        d[, clean_value:=cleangrowth(subjid, param, agedays, sex, measurement
            {include_carryforward}
            {recover_unit_error}
            {save_medians}
            {save_recenter}
        )]
        fwrite(d, "{str(result_fname)}")
        """
    )
    return result_fname


@huey_queue.task()
def r_longwide(fname, options={}):
    # Note: will already have "RESULT_DIR/" prepended
    result_fname = f"{str(fname)[:-4]}-wide.csv"
    if options.get("include_all", None):
        option_str = ", include_all=TRUE"
    elif options.get("inclusion_types", []):
        option_str = (
            ", inclusion_types=c("
            + ", ".join(['"%s"' % it for it in options.get("inclusion_types")])
            + ")"
        )
    else:
        option_str = ""
    robjects.r(
        f"""
        library(data.table)
        library(growthcleanr)
        d <- fread("{fname}")
        d_wide <- longwide(d{option_str})
        fwrite(d_wide, "{str(result_fname)}")
        """
    )
    return result_fname


@huey_queue.task()
def r_ext_bmiz(fname, options={}):
    # Using -9 to remove all of "-wide.csv"
    result_fname = f"{str(fname)[:-9]}-bmi.csv"
    robjects.r(
        f"""
        library(data.table)
        library(growthcleanr)
        d <- fread("{fname}")
        d_bmi <- ext_bmiz(d)
        fwrite(d_bmi, "{str(result_fname)}")
    """
    )
    return result_fname
