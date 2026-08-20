import tempfile

shards = [189344, 188576, 188578, 188579, 188577, 189389, 188585, 188589, 189376, 188608, 188610, 189379, 188611, 189378, 188609, 188614, 188621, 188622, 188623, 188496, 189264, 188497, 188499, 189265, 189267, 189266, 189278]

def test_ps1_import_file():
    from get_lsst_refcats.utils import make_refcat_import
    with tempfile.TemporaryDirectory() as tempdir:
        table = make_refcat_import("ps1_pv3_3pi_20170110", shards, tempdir)
        assert len(table) == len(shards)

def test_ps1_old_import_file():
    from get_lsst_refcats.utils import make_refcat_import
    with tempfile.TemporaryDirectory() as tempdir:
        table = make_refcat_import("ps1_pv3_3pi_20170110_old", shards, tempdir)
        assert len(table) == len(shards)

def test_gaiadr3_import_file():
    from get_lsst_refcats.utils import make_refcat_import
    with tempfile.TemporaryDirectory() as tempdir:
        table = make_refcat_import("gaia_dr3_20230707", shards, tempdir)
        assert len(table) == len(shards)

def test_gaiadr2_import_file():
    from get_lsst_refcats.utils import make_refcat_import
    with tempfile.TemporaryDirectory() as tempdir:
        table = make_refcat_import("gaia_dr2_20200414", shards, tempdir)
        assert len(table) == len(shards)