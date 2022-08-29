import logging
from pathlib import Path

from pctasks.cli.cli import setup_logging, setup_logging_for_module
from pctasks.dev.test_utils import run_process_items_workflow

HERE = Path(__file__).parent
DATASET_PATH = HERE / ".." / "dataset.yaml"


# Change the COG_CONTAINER to devstoreaccount1 in noaa_nclimgrid.py to avoid
# uploading COGs to nclimgridwesteurope
def test_daily():
    run_process_items_workflow(
        DATASET_PATH,
        collection_id="noaa-nclimgrid-daily",
        args={
            "registry": "localhost:5001",
        },
        chunks_limit=1
    )


def test_monthly():
    pass
    # The monthly data is one chunk for all data. Since COGs are being created,
    # it is onerous to run a test for this collection


if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    setup_logging_for_module("__main__", logging.DEBUG)
    test_daily()
    print("All tests passed")
    exit(0)
