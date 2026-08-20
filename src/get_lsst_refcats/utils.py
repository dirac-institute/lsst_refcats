import importlib
import os
import yaml
import astropy.table
import requests
import socket
import re

refcat_name_to_dataset_name = {
    "ps1": "ps1_pv3_3pi_20170110",
    "ps1_old": "ps1_pv3_3pi_20170110_old",
    "panstarrs1": "ps1_pv3_3pi_20170110",
    "panstarrs": "ps1_pv3_3pi_20170110",
    "Pan-STARRS1": "ps1_pv3_3pi_20170110",
    "gaia": "gaia_dr2_20200414",
    "gaia_dr2": "gaia_dr2_20200414",
    "gaiadr2": "gaia_dr2_20200414",
    "Gaia-DR2": "gaia_dr2_20200414",
    "gaia_dr3": "gaia_dr3_20230707",
    "gaiadr3": "gaia_dr3_20230707",
    "Gaia-DR3": "gaia_dr3_20230707",
}

# if socket.gethostname() == "epyc.astro.washington.edu":
#     def get_file(path, output_dir):
#         print(f"Getting file for path: {path}")
#         os.makedirs(output_dir, exist_ok=True)
#         output_path = os.path.join(output_dir, os.path.basename(path))
#         print(f"Writing to output directory: {output_path}")
#         with open(os.path.join("/epyc/data/lsst_refcats", path), "rb") as i:
#             with open(output_path, "wb") as o:
#                 o.write(i.read())
#         return os.path.abspath(output_path)
# else:
REMOTE_URL = "https://epyc.astro.washington.edu/~stevengs/lsst_refcats"
def get_file(path, output_dir):
    print(f"Getting file for path: {path}")
    response = requests.get(os.path.join(REMOTE_URL, path))
    response.raise_for_status()
    output_path = os.path.join(output_dir, os.path.basename(path))
    os.makedirs(output_dir, exist_ok=True)
    print(f"Writing to output directory: {output_path}")
    with open(output_path, "wb") as f:
        f.write(response.content)
    return os.path.abspath(output_path)

def get_local_file(path):
    if PROJECT_DIR is None:
        raise ValueError("You need to define a PROJECT_DIR environment variable. Did you run a provided Bash script or the python code directly?")
    full_path =  os.path.join(PROJECT_DIR, path)

def load_refcat_yaml(dataset_name, output_dir):
    if dataset_name == "ps1_pv3_3pi_20170110":
        get_file("exports/ps1_export_gen3.yaml", output_dir)
        return yaml.load(open(get_file("exports/ps1_export_gen3.yaml", output_dir), "r"), Loader=yaml.CLoader)
    elif dataset_name == "gaia_dr2_20200414":
        return yaml.load(open(get_file("exports/ps1_export_gen3.yaml", output_dir), "r"), Loader=yaml.CLoader)
    elif dataset_name == "gaia_dr3_20230707":
        return yaml.load(open(get_file("exports/ps1_export_gen3.yaml", output_dir), "r"), Loader=yaml.CLoader)
    else:
        raise ValueError(f"dataset name {dataset_name} is not supported")

def make_refcat_import(dataset_name, shards, output_dir):
    dataset_configs = {
        "ps1_pv3_3pi_20170110": ("ps1_pv3_3pi_20170110", "ps1/ps1_pv3_3pi_20170110"),
        "ps1_pv3_3pi_20170110_old": (
            "ps1_pv3_3pi_20170110_old",
            "refcats/ps1_pv3_3pi_20170110",
        ),
        "gaia_dr2_20200414": ("gaia_dr2_20200414", "refcats/gaia_dr2_20200414"),
        "gaia_dr3_20230707": ("gaia_dr3_20230707", "GAIA_DR3/gaia_dr3"),
    }

    if dataset_name not in dataset_configs:
        raise ValueError(f"dataset name {dataset_name} is not supported")

    sub_dir, rel_path = dataset_configs[dataset_name]
    output_dir = os.path.join(output_dir, sub_dir)
    index_file = get_file(f"{rel_path}/index.dat", output_dir)

    # Pre-compile regex pattern for each shard to match full numbers only
    # (?<!\d) ensures no digit directly before, (?!\d) ensures no digit directly after
    shard_patterns = {s: re.compile(rf"(?<!\d){s}(?!\d)") for s in shards}

    shard_to_filename = {}

    with open(index_file) as f:
        for line in f:
            filename = line.strip()
            for s, pattern in shard_patterns.items():
                if pattern.search(filename):
                    shard_to_filename[s] = filename
                    break  # Found the shard for this file, move to next line

    aligned_paths = []
    aligned_shards = []

    # Process requested shards in guaranteed order
    for s in shards:
        if s in shard_to_filename:
            filename = shard_to_filename[s]
            full_path = get_file(os.path.join(rel_path, filename), output_dir)

            if os.path.exists(full_path):
                aligned_paths.append(full_path)
                aligned_shards.append(s)

    return astropy.table.Table(
        [aligned_paths, aligned_shards], names=["filename", "htm7"]
    )
    
def deferred_import(module, name=None, ns=globals()):
    """Defer the import of the stack untill we actually need it to be able to
    print help message before the heat death of the universe.
    """
    if name is None:
        name = module
    if ns.get(name, False):
        return
    try:
        ns[name] = importlib.import_module(module)
    except ImportError as e:
        raise ImportError("No Rubin Stack found. Please activate Rubin stack.") from e

def get_exp_metadata(exposure):
    """Return exposure's bounding box, wcs and, if existant, filter
    and calibration data.

    Parameters
    ----------
    exposure : `afw.image.ExposureF`
        Exposure
    """
    deferred_import("lsst.pipe.base", "pipeBase")
    expInfo = exposure.getInfo()

    #filterName = expInfo.getFilter().getName() or None
    filterName = expInfo.getFilter().physicalLabel or None
    if filterName == "_unknown_":
        filterName = None

    return pipeBase.Struct(
        bbox  = exposure.getBBox(),
        wcs   = expInfo.getWcs(),
        filterName = filterName,
    )

def get_shard_filename(refcatConf, shardId):
    """Returns the name of the shard file."""
    return f"{refcatConf.ref_dataset_name}_{shardId}_refcats_gen2.fits"


def get_shard_filepath(refcatConf, refcatLocation, shardId):
    """Return the filepath to the shard file."""
    return os.path.join(refcatLocation, get_shard_filename(refcatConf, shardId))


def resolve_input_meaning(input_val, default_val):
    """Resolves the meaning of given input value to the given default value,
    the input value or to ``None``.

    When the given input value is ``None`` returns the default value.
    When the input value is truthy returns the given input value.
    When the input value is falsy returns ``None``

    Parameters
    ----------
    input_val : any
        Input value.
    default_val : any
        Output value when input_value is None.

    Returns
    -------
    interpreted_val : any
        Given value, default value or None - depending on the input.
    """
    if input_val is None:
        return default_val
    elif input_val:
        return input_val
    else:
        return None


############################################################
#                         Resolvers
############################################################

def calculate_circle(bbox, wcs, pixelMargin):
    """Computes on-sky center and radius of search region

    Parameters
    ----------
    bbox : `lsst.geom.Box2DI` or `lsst.geom.Box2D`
        Bounding box
    wcs : `lsst.afw.geom.SkyWcs`
        WCS
    pixelMargin : `int` or `float`
        padding in pixels by which the bbox will be expanded

    Returns
    ----------
    coord : `lsst.geom.SpherePoint`
        ICRS center of the search region
    radius : `lsst.geom.Angle`
        Radius of the search region
    bbox : `lsst.geom.Box2D`
        Bounding box used to compute the circumscribed circle
    """
    deferred_import("lsst.geom", "geom")
    deferred_import("lsst.pipe.base", "pipeBase")
    bbox = geom.Box2D(bbox)
    bbox.grow(pixelMargin)
    coord  = wcs.pixelToSky(bbox.getCenter())
    radius = max(coord.separation(wcs.pixelToSky(pp)) for pp in bbox.getCorners())
    return pipeBase.Struct(coord=coord, radius=radius, bbox=bbox)


def resolve_circle2shard_ids(refCatConf, circle):
    """Resolves IDs of shards overlapping an on-sky circular region.

    Parameters
    ----------
    refCatConf : `lsst.meas.algorithms.DatasetConfig`
        Configuration of the reference catalog
    circle : `lsst.pipe.base.Struct`
        Struct containing ICRS center of the search region
        (`lsst.geom.SpherePoint`) and radius of the search region
        (`lsst.geom.Angle`).

    Returns
    ----------
    shard_ids : `list`
        List of integer IDs of reference catalog shards overlapping the region.
    """
    ref_dataset_name = refCatConf.ref_dataset_name
    deferred_import("lsst.meas.algorithms", "measAlgs")
    indexer = measAlgs.IndexerRegistry[refCatConf.indexer.name](refCatConf.indexer.active)
    shard_ids, boundary_mask = indexer.getShardIds(circle.coord, circle.radius)
    return shard_ids


def resolve_bbox2shard_ids(refCatConf, bbox, wcs, pixelMargin=300):
    """Resolves IDs of shards overlapping an on-sky bounding box.

    Parameters
    ----------
    refCatConf : `lsst.meas.algorithms.DatasetConfig object`
        Reference catalog configuration
    bbox : `lsst.geom.Box2D`
        bounding box of the region of interest
    wcs : `lsst.afw.geom.SkyWcs`
        WCS defining the bbox coordinate system
    pixelMargin: `int`
        Bounding box padding, in pixels. Default: 300.

    Returns
    ----------
    shard_ids : `list`
        IDs of reference catalog shards overlapping the region.
    """
    circle = calculate_circle(bbox, wcs, pixelMargin)
    shard_ids = resolve_circle2shard_ids(refCatConf, circle)
    return shard_ids


def resolve_exposure_shard_ids(refCatConf, exposure, pixelMargin=300, **kwargs):
    """Resolves IDs of shards overlapping an Exposure.

    Parameters
    ----------
    refCatConf : `lsst.meas.algorithms.DatasetConfig object`
        Reference catalog configuration
    exposure : `lsst.afw.ExposureF`
        Image
    pixelMargin: `int`
        Bounding box padding, in pixels. Default: 300.

    Returns
    ----------
    shard_ids : `list`
        IDs of reference catalog shards overlapping the region.
    """

    meta = get_exp_metadata(exposure)
    return resolve_bbox2shard_ids(
        refCatConf, bbox=meta.bbox,
        wcs=meta.wcs, pixelMargin=pixelMargin,
        **kwargs
    )


def resolve_decamraw_shard_ids(refCatConf, fitsPath, pixelMargin=300, **kwargs):
    """Resolves IDs of shards overlapping an fits file.

    Parameters
    ----------
    refCatConf : `lsst.meas.algorithms.DatasetConfig object`
        Reference catalog configuration
    exposure : `lsst.afw.ExposureF`
        Image
    pixelMargin: `int`
        Bounding box padding, in pixels. Default: 300.

    Returns
    ----------
    shard_ids : `list`
        IDs of reference catalog shards overlapping the region.
    """
    deferred_import("astropy.io.fits", "fitsio")
    deferred_import("lsst.geom", "geom")
    deferred_import("astropy.wcs", "awcs")
    deferred_import("lsst.afw.geom", "afwGeom")
    hdul = fitsio.open(fitsPath)

    shardIds = []
    bbox = geom.Box2D(geom.Point2D(0, 0), geom.Extent2D(hdul[1].header["NAXIS1"], hdul[1].header["NAXIS2"]))
    for hdu in hdul[1:]:
        wcs = awcs.WCS(hdu.header)
        crpix = geom.Point2D(wcs.wcs.crpix)
        crval = geom.SpherePoint(longitude=wcs.wcs.crval[0], latitude=wcs.wcs.crval[1], units=geom.degrees)
        skyWcs = afwGeom.makeSkyWcs(crpix=crpix, crval=crval, cdMatrix=wcs.wcs.cd, projection="TAN")
        shards = resolve_bbox2shard_ids(refCatConf, bbox=bbox, wcs=skyWcs, pixelMargin=pixelMargin, **kwargs)
        shardIds.extend(shards)

    return list(set(shardIds))

def create_bbox_and_wcs_from_decam_fits(path):
    bboxes = []
    wcss = []
    deferred_import("astropy.io.fits", "fitsio")
    deferred_import("lsst.geom", "geom")
    deferred_import("astropy.wcs", "awcs")
    deferred_import("lsst.afw.geom", "afwGeom")
    with fitsio.open(path) as hdul:
        bbox = geom.Box2D(geom.Point2D(0, 0), geom.Extent2D(hdul[1].header["NAXIS1"], hdul[1].header["NAXIS2"]))
        for hdu in hdul[1:]:
            wcs = awcs.WCS(hdu.header)
            crpix = geom.Point2D(wcs.wcs.crpix)
            crval = geom.SpherePoint(longitude=wcs.wcs.crval[0], latitude=wcs.wcs.crval[1], units=geom.degrees)
            skyWcs = afwGeom.makeSkyWcs(crpix=crpix, crval=crval, cdMatrix=wcs.wcs.cd, projection="TAN")        
            wcss.append(skyWcs)
            bboxes.append(bbox)
    return bboxes, wcss

