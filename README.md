# MVUM TMS Generation

Generate TMS tiles of United States Forest Service (USFS) Motor Vehicle Use Maps (MVUM), especially to see those dispersed camping dots next to roads in Gaia GPS.

## How to use in Gaia GPS

This is a hobby interest of mine. Maps may be incorrect or not up to date. You are responsible for ensuring accuracy.

If hosting becomes too expensive for me, I will investigate some licensing, and try to give any contributors (based on commit message email) access for free or reduced cost. If you'd like to donate money, you may use <https://paypal.me/burkemw3>

Use Gaia's Import Custom Map feature using TMS (Tile Map Service) option: [docs](https://help.gaiagps.com/hc/en-us/articles/115003639068-Adding-a-TMS-Map-Source). The url is `http://mvum-tms-generation.s3-website-us-east-1.amazonaws.com/fd3a484/tiles/{z}/{x}/{y}.png`. Zoom levels are 8-14.

## Background

USFS publishes MVUM vector data, which is included in mp apps, like Gaia GPS, and includes things like roads. The USFS published data does not include the dots alongside roads that show where dispersed camping is allowed, so Gaia can't render it. Most USFS forests do publish Georeferenced PDFs that do include the dots, though.

Separately, Gaia allows loading custom map sources. This project clips and composites USFS PDFs into a custom map that can be loaded in Gaia GPS.

These maps are base layer maps, not vector maps. You can set the transparency to somewhat see other base layers, but not perfect. Still much easier for me to toggle gaia layers, than have to try to match multiple sources and handle multiple download locations for offline use.

## Forest Notes

Included Forests

* Colorado's ARP Arapaho and Roosevelt National Forests and Pawnee National Grassland
* Colorado's GMUG Grand Mesa, Uncompahgre and Gunnison National Forests
* Colorado's WHITERIVER White River National Forest

Excluded Forests

* Colorado's Pike-San Isabel National Forests & Cimarron and Comanche National Grasslands (PSICC) does not include dispersed camping designations on their MVUMs. This dataset does not PSICC forest.

Other forests need to be investigated and added or excluded.

## Adding/Updating Maps

> ### Legal Notice <!-- omit in toc -->
>
> When contributing to this project, you agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

0. Add an entry in `config.json` for a new source USFS file (or update existing)
    * `title` is a human friendly display name, especially USFS Forest Code, then file reference
 * `id` is a unique, machine-focused name, especially for intermediate file names
 * `mvum_pdf` is URL to USFS Georeferenced PDF
 * `mvum_md5` is the md5sum of the USFS Georeferenced PDF
 * `mvum_mask_geojson` is the path to a mask file defined below
 * `ranger_district_id` is defined below
0. Download the USFS pdf file.
0. Use something like `md5` command-line tool to determine the PDF's md5 sum
0. Use a tool like QGIS to generate an geojson file with a polygon that covers the map area on the PDF. Exclude legend selections. The polygon may include areas that are not in the ranger distrcit (those should be filtered out by the ranger district lines). Ensure the file has a CRS defined. Example QGIS steps
   0. Load the PDF as a raster layer
   0. Create a temporary scratch layer, with Polygon geometry type, and same CRS as PDF. Make sure CRS has EPSG prefix.
   0. Draw a polygon to cover the map area
   0. Right click on temporary layer > Export > Save Feature As ...
   0. Use GeoJSON format, a consistent filename (in the data-files directory), and make sure CRS is selected (with EPSG prefix).
0. To find the ranger district id use `python3 find_ranger.py --rdb data-files/Ranger_District_Boundaries_\(Feature_Layer\).geojson --q "search_term"` to search for the ranger district of the PDF.

See Generating Tiles section below for testing.

## Generating Tiles

0. Make sure dependencies are present (e.g. gdal with python bindings available on PATH, python libraries). (TODO document dependencies and/or provide consistent environment)
   - sqlite, gdal, etc
0. Make sure you have the ranger district boundaries (currently using geojson from <https://data-usfs.hub.arcgis.com/datasets/usfs::ranger-district-boundaries-feature-layer/about>) and updated config.json with the path (e.g. `data-files/Ranger_District_Boundaries_(Feature_Layer).geojson`) (file is too big for github)
0. Make sure the cache folder has all PDFs that config file references (filename is `${md5hash}.pdf`) (TODO make `requests` or something else work).
0. For final files, run `GDAL_PDF_DPI=200 python3 process.py -c config.json`. For testing, consider reducing GDAL_PDF_DPI value. For testing, consider using a smaller config.json file. For example, 1-2 existing input files, plus whatever is being added.
