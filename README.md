# lsst_refcats

Download (trimmed) GaiaDR3 / GaiaDR2 / Pan-STARRS1 reference catalogs for use with the LSST Science Pipelines.

Requires the LSST Science Pipelines as a dependency: https://pipelines.lsst.io/
- This package has been tested with version `w_2024_34` of the Science Pipelines. 

Install:
```
$ python -m pip install git+https://github.com/dirac-institute/lsst_refcats.git
```

Usage:
```
usage: lsst-refcats [-h] [--output OUTPUT] [--paths PATHS [PATHS ...]] [--repo REPO] [--dataset DATASET] [--collections COLLECTIONS]
                    [--where WHERE] [--refcat_indexer REFCAT_INDEXER] [--pixel_margin PIXEL_MARGIN] [--log-level LOG_LEVEL]
                    [--export-run EXPORT_RUN] [--export-dataset-name EXPORT_DATASET_NAME] [--import-file] [--processes PROCESSES]
                    refcat_name

positional arguments:
  refcat_name           The reference catalog name

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        The output file to write the trimmed refcat YAML to (default: data/refcats)
  --paths PATHS [PATHS ...], -p PATHS [PATHS ...]
                        The paths to fits files to search (default: [])
  --repo REPO, -b REPO  The repo to search for exposures (default: None)
  --dataset DATASET     The dataset name to search if using repo (default: None)
  --collections COLLECTIONS
                        The collections to search if using repo (default: None)
  --where WHERE         A constraint for the dataset search if using repo (default: )
  --refcat_indexer REFCAT_INDEXER
                        The refcat indexer (default: HTM)
  --pixel_margin PIXEL_MARGIN
                        The pixel margin for determining overlapping refcat shards (default: 300)
  --log-level LOG_LEVEL
                        The logging level, one of DEBUG, INFO, WARN, ERROR (default: INFO)
  --export-run EXPORT_RUN
                        The RUN collection name to export collections into (default: refcats)
  --export-dataset-name EXPORT_DATASET_NAME
                        The dataset name to use for exported datasets (default: None)
  --import-file         Make import ECSV file (new style) instead of YAML export file (default: False)
  --processes PROCESSES, -J PROCESSES
                        Number of processes to use for opening fits files or loading dataset refs (default: 8)
```

Example:
```
$ lsst-refcats gaiadr3 --paths image.fits.fz --import-file
$ butler create ./repo
$ butler register-dataset-type ./repo gaia_dr3_20230707 SimpleCatalog htm7
$ butler ingest-files ./repo gaia_dr3_20230707 refcats/gaia_dr3 ./data/refcats/gaia_dr3_20230707.ecsv
lsst.daf.butler.script.ingest_files INFO: Ingesting 27 dataset ref(s) from 27 file(s)
$ butler query-datasets ./repo gaia_dr3_20230707 --collections "refcats/gaia_dr3"
lsst.daf.butler.script.queryDatasets INFO: Processing 1 dataset type

       type             run                         id                   htm7 
----------------- ---------------- ------------------------------------ ------
gaia_dr3_20230707 refcats/gaia_dr3 ae761abd-3d9a-4ede-a21d-bb9b757af459 188496
...
```

Credits:

Code authored by [stevenstetzler](https://github.com/stevenstetzler/) and [DinoBektesevic](https://github.com/DinoBektesevic/).
