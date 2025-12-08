from .utils import deferred_import, refcat_name_to_dataset_name, resolve_bbox2shard_ids, create_bbox_and_wcs_from_decam_fits, resolve_exposure_shard_ids, load_refcat_yaml, make_refcat_import
import argparse
import os
import yaml
import logging
import sys
import joblib

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s:%(filename)s:%(lineno)s - %(funcName)5s()] %(message)s")


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("refcat_name", type=str, help="The reference catalog name")
    parser.add_argument("--output", "-o", type=str, default="data/refcats", help="The output file to write the trimmed refcat YAML to")
    parser.add_argument("--paths", "-p", nargs="+", type=str, default=[], help="The paths to fits files to search")
    parser.add_argument("--repo", "-b", type=str, default=None, help="The repo to search for exposures")
    parser.add_argument("--dataset", default=None, help="The dataset name to search if using repo")
    parser.add_argument("--collections", default=None, help="The collections to search if using repo")
    parser.add_argument("--where", default="", help="A constraint for the dataset search if using repo")
    parser.add_argument("--refcat_indexer", default="HTM", help="The refcat indexer")
    parser.add_argument("--pixel_margin", type=int, default=300, help="The pixel margin for determining overlapping refcat shards")
    parser.add_argument("--log-level", help="The logging level, one of DEBUG, INFO, WARN, ERROR", default="INFO")
    parser.add_argument("--export-run", type=str, default="refcats", help="The RUN collection name to export collections into")
    parser.add_argument("--export-dataset-name", type=str, default=None, help="The dataset name to use for exported datasets")
    parser.add_argument("--import-file", action="store_true", help="Make import ECSV file (new style) instead of YAML export file")
    parser.add_argument("--processes", "-J", type=int, default=8, help="Number of processes to use for opening fits files or loading dataset refs")

    args = parser.parse_args()
    if args.repo is not None and args.dataset is None:
        raise ValueError("must use argument --dataset if specifying repo")
    logger.setLevel(getattr(logging, args.log_level))

    os.makedirs(args.output, exist_ok=True)

    deferred_import("lsst.meas.algorithms", "measAlgs", ns=globals())
    refCatConf = measAlgs.DatasetConfig()
    ref_dataset_name  = refcat_name_to_dataset_name.get(args.refcat_name, None)
    if ref_dataset_name is None:
        raise ValueError(f"{args.refcat_name} is not an alias for any dataset name, use one of {list(refcat_name_to_dataset_name.keys())}")
    refCatConf.ref_dataset_name = ref_dataset_name
    if args.refcat_indexer != "HTM":
        raise ValueError(f"refcat indexer {args.refcat_indexer} is not supported")
    refCatConf.indexer = args.refcat_indexer

    if args.export_dataset_name is None:
        export_dataset_name = ref_dataset_name
    else:
        export_dataset_name = args.export_dataset_name

    bboxes = []
    wcss = []
    if args.paths:
        def work(path):
            import logging
            logging.basicConfig()
            logger = logging.getLogger(__name__)
            logger.setLevel(getattr(logging, args.log_level))
            logger.info(f"loading fits {path}")
            return create_bbox_and_wcs_from_decam_fits(path)
        
        results = joblib.Parallel(n_jobs=args.processes)(joblib.delayed(work)(path) for path in args.paths)
        for bbox, wcs in results:
            bboxes.extend(bbox)
            wcss.extend(wcs)
    
    # for path in args.paths:
    #     logger.info(f"loading fits {path}")
    #     bbox, wcs = create_bbox_and_wcs_from_decam_fits(path)
    #     bboxes.extend(bbox)
    #     wcss.extend(wcs)
    
    if args.repo:
        deferred_import("lsst.daf.butler", "dafButler", ns=globals())
        butler = dafButler.Butler(args.repo, collections=args.collections)
        refs = butler.registry.queryDatasets(args.dataset, where=args.where)
        def work(ref):
            import logging
            logging.basicConfig()
            logger = logging.getLogger(__name__)
            logger.setLevel(getattr(logging, args.log_level))
            logger.info(f"loading dataset {ref}")

            wcs = butler.get(f"{args.dataset}.wcs", ref.dataId, collections=ref.run)
            bbox = butler.get(f"{args.dataset}.detector", ref.dataId, collections=ref.run).getBBox()
            return bbox, wcs
        
        results = joblib.Parallel(n_jobs=args.processes)(joblib.delayed(work)(ref) for ref in refs)
        for bbox, wcs in results:
            bboxes.append(bbox)
            wcss.append(wcs)

        # for ref in refs:
        #     logger.info(f"loading dataset {ref}")
        #     bboxes.append(bbox)
        #     wcss.append(wcs)
    
    shards = []
    for bbox, wcs in zip(bboxes, wcss):
        shards.extend(resolve_bbox2shard_ids(refCatConf, bbox, wcs, pixelMargin=args.pixel_margin))

    shards = list(set(shards))
    logger.info("shards: %s", shards)
    if args.import_file:
        import_table = make_refcat_import(ref_dataset_name, shards, args.output)
        import_table.write(os.path.join(args.output, ref_dataset_name + ".ecsv"), format="ascii.ecsv")
    else:
        # load the full yaml and trim to include just the chosen shards
        logger.info(f"loading refcat for {ref_dataset_name}")
        refcat = load_refcat_yaml(ref_dataset_name)
        datasets = list(filter(lambda d : d['type'] == "dataset", refcat['data']))[0]
        collection = list(filter(lambda d : d['type'] == "collection", refcat['data']))[0]
        dataset_type = list(filter(lambda d : d['type'] == "dataset_type", refcat['data']))[0]
        collection['name'] = args.export_run
        dataset_type['name'] = export_dataset_name
        logger.info("trimming records")
        records = list(filter(lambda rec : rec['data_id'][0]['htm7'] in shards, datasets['records']))
        datasets['records'] = records
        datasets['run'] = args.export_run
        datasets['dataset_type'] = export_dataset_name
        refcat['data'] = [collection, dataset_type, datasets]

        print(yaml.dump(refcat))

if __name__ == "__main__":
    main()

