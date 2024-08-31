import argparse
import glob
import json
import os
# import requests
import shutil
import subprocess
import sys


parser = argparse.ArgumentParser("process")
parser.add_argument("-c", help="Path to config file", type=str, default="config.json")
parser.add_argument("-i", help="Path to incremental config file", type=str)
args = parser.parse_args()

f = open(args.c)
data = json.load(f)

cache_dir = data["output"]["cache_folder"]
ranger_districts_filename = data["input"]["ranger_districts_geo_json"]
mosaic_file_name = os.path.join(cache_dir, "mosaic.vrt")
if os.path.isfile(mosaic_file_name):
    os.remove(mosaic_file_name)
tiles_folder_name = "tiles"
if args.i is None and os.path.isdir(tiles_folder_name):
    shutil.rmtree(tiles_folder_name)
incremental_tiles_folder_name = "incremental_tiles"
if args.i is not None and os.path.isdir(incremental_tiles_folder_name):
    shutil.rmtree(incremental_tiles_folder_name)

# fix ranger geometry, and create indexed-sqlite storage
ranger_db_filename = os.path.join(cache_dir, "ranger_districts.sqlite")
if os.path.isfile(ranger_db_filename):
    os.remove(ranger_db_filename)
subprocess.run(
    ["ogr2ogr", "-makevalid", "-of", "sqlite", ranger_db_filename, ranger_districts_filename],
    check=True)
subprocess.run(
    ["sqlite3", ranger_db_filename, "CREATE INDEX IF NOT EXISTS idx_rangerdistrictid ON `ranger_district_boundaries_(feature_layer)` (rangerdistrictid);", ".exit"],
    check=True)

if args.i is not None:
    inc_f = open(args.i)
    ext_data = data
    inc_data = json.load(inc_f)
    data = inc_data

seen_ids = set([])
files_to_merge = []
for i in data["input"]["pdfs"]:
    print("processing " + i["title"])

    # Handle PDF file
    # TODO add download support. can't get requests module right now!
    # r = requests.get(i["mvum_pdf"], allow_redirects=True)
    # pdf_filename = os.join.path(cache_dir, mvum_md5 + ".pdf")
    # open(pdf_filename, 'wb').write(r.content)
    # check md5 hash
    # result = subprocess.run(["md5", pdf_filename], capture_output=True, check=True)
    # if result.stdout.rstrip() != i["mvum_md5"]:
    #     raise ValueError("configured hash " + i["mvum_md5"] + " and actual hash " + result.stdout.rstrip() + " don't match")

    # check for hash duplicate
    if i["id"] in seen_ids:
        raise ValueError("duplicate id " + i["id"] + ". noticed in " + i["title"])
    seen_ids.add(i["id"])

    # convert to geotiff
    # gdal_translate -of GTiff cache/30c494f8908b6fa65334710f288f3ec3.pdf cache/30c494f8908b6fa65334710f288f3ec3.tif
    # TODO check options, especially DPI
    # TODO needs `GDAL_PDF_DPI=200` environment variable. Can it be part of script?
    mvum_gpdf_filename = os.path.join(cache_dir, i["mvum_md5"] + ".pdf")
    mvum_gtif_filename = os.path.join(cache_dir, i["id"] + ".tif")
    subprocess.run(
        ["gdal_translate", "-of", "GTiff", mvum_gpdf_filename, mvum_gtif_filename],
        check=True)

    # apply mvum mask
    # gdalwarp -dstalpha -overwrite -of GTiff -crop_to_cutline -cutline "data-files/arp-boulder-north.geojson" output.tif next.tif
    # TODO check cli options
    mvum_mask_filename = os.path.join(cache_dir, i["id"] + "-mvum-masked" + ".tif")
    subprocess.run([
        "gdalwarp", "-dstalpha", "-overwrite", "-of", "GTiff",
        "-cutline", i["mvum_mask_geojson"], "-crop_to_cutline",
        "-wo", "NUM_THREADS=ALL_CPUS",
        "-t_srs", "EPSG:4326", # force to WGS84, for consistency and what ranger district file uses
        mvum_gtif_filename,
        mvum_mask_filename
        ], check=True)

    # apply ranger district mask
    # gdalwarp -dstalpha -overwrite -of GTiff -crop_to_cutline -cutline "data-files/Ranger_District_Boundaries_(Feature_Layer).geojson" -cwhere "RANGERDISTRICTID = '99021001010343'" cache/30c494f8908b6fa65334710f288f3ec3.tif output.tif
    # TODO check cli options
    for ranger_idx, ranger_id in enumerate(i["ranger_district_ids"]):
        ranger_mask_filename = os.path.join(cache_dir, i["id"] + "-ranger-masked-" + str(ranger_idx) + ".tif")
        cwhere = "RANGERDISTRICTID = '" + ranger_id + "'"
        subprocess.run([
            "gdalwarp", "-dstalpha", "-overwrite", "-of", "GTiff",
            # for smaller files that vrt references
            "-co", "COMPRESS=DEFLATE", "-co", "PREDICTOR=2", "-co", "ZLEVEL=9",
            "-crop_to_cutline", "-cutline", ranger_db_filename,
            "-wo", "NUM_THREADS=ALL_CPUS",
            "-cwhere", cwhere,
            mvum_mask_filename,
            ranger_mask_filename
            ], check=True)

        files_to_merge.append(ranger_mask_filename)

# merge stuff together
print("merging: ", files_to_merge)
subprocess.run([
    "gdalbuildvrt",
    "-resolution", "highest",
    mosaic_file_name,
    *files_to_merge
    ], check=True)

# generate tiles
# gdal2tiles -z 8-14 --xyz -w leaflet output.tif tiles
# z8-14 is looking good
print("tiling")
subprocess.run([
    "gdal2tiles",
    "-z", "8-14",
    "--exclude",
    "--processes", "8", # TODO determine processor count?
    "--xyz",
    "-w", "leaflet",
    mosaic_file_name,
    tiles_folder_name if args.i is None else incremental_tiles_folder_name
    ], check=True)

# if not incremental, then exit
if args.i is None:
  sys.exit()

# find matching/overlapping tiles. delete them from both.
existing_tiles = glob.glob("*/*/*.png", root_dir=tiles_folder_name)
incremental_tiles = glob.glob("*/*/*.png", root_dir=incremental_tiles_folder_name)
overlapping_tiles = list(set(existing_tiles) & set(incremental_tiles))
for filepath in overlapping_tiles:
    os.remove(os.path.join(tiles_folder_name, filepath))
    os.remove(os.path.join(incremental_tiles_folder_name, filepath))
# copy remaining incremental tiles to persistent tiles
remaining_incremental_tiles = glob.glob("*/*/*.png", root_dir=incremental_tiles_folder_name)
for remaining_tile in remaining_incremental_tiles:
    shutil.copy2(
        os.path.join(incremental_tiles_folder_name, remaining_tile),
        os.path.join(tiles_folder_name, remaining_tile))
# combine all source files into another mosaic
print("merging existing and incremental: ", files_to_merge)
for i in ext_data["input"]["pdfs"]:
    for ranger_idx, ranger_id in enumerate(i["ranger_district_ids"]):
        ranger_mask_filename = os.path.join(cache_dir, i["id"] + "-ranger-masked-" + str(ranger_idx) + ".tif")
        files_to_merge.append(ranger_mask_filename)
subprocess.run([
    "gdalbuildvrt",
    "-resolution", "highest",
    mosaic_file_name,
    *files_to_merge
    ], check=True)
# re-run gdal2tiles with --resume this time
print("tiling mising")
subprocess.run([
    "gdal2tiles",
    "--resume",
    "-z", "8-14",
    "--exclude",
    "--processes", "8", # TODO determine processor count?
    "--xyz",
    "-w", "leaflet",
    mosaic_file_name,
    tiles_folder_name
    ], check=True)
# answer https://gis.stackexchange.com/q/467208
