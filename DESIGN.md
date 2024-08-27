This is a working amalgamation of various tools, not a well-designed pipeline.

With some ranger districts being adjacent on arbitrary lines, and some ranger districts divided into multiple PDFs, and all MVUM PDFs including legends, I wanted a scalabale way to combine them all together.

By applying the manually crafted MVUM mask, the legends are removed. By applying the Ranger district boundary (available as data export from USFS), the process clips irrelevant sections. Any overlap between PDFs in the same ranger district _shouldn't_ matter which one gets priority.

The PDF conversion and clipping is naively highly parallelizable. I am not motivated enough right now.

I tried using some GDAL libraries in Python directly, and gave up. I couldn't get them working just right, already had the CLI versions working, and wanted my tiles!

Possible future improvements

- pass `GDAL_PDF_DPI=200` in process.py, instead of invocation environment variable
- test allowing multiple ranger districts per input file (at least GMUG has PDFs spanning multiple ranger districts)
- allow custom ranger district boundaries (at least ARP Canyon Lakes is invalid to gdal)
- parallelize input file processing

References

- <https://gis.stackexchange.com/a/464303> was helpful for Geo PDF to TIFF conversion, especially the `GDAL_PDF_DPI` environment variable.
- QGIS was helpful for figuring out the mask application command `gdalwarp`, as QGIS will display it when clipping.
- Some random articles suggested combining via vrt files, then using gdal2tiles would be smarter than something like `gdal_merge` to merge all the individual files together. We'll see how that goes as more forests are added!
