import argparse
import json
import os
import subprocess
import tempfile


parser = argparse.ArgumentParser("cache_ranger_pdfs")
parser.add_argument("-c", help="Path to config file", type=str, default="config.json")
args = parser.parse_args()

f = open(args.c, "r+")
data = json.load(f)

cache_dir = data["output"]["cache_folder"]

for i in data["input"]["pdfs"]:
    if "mvum_md5" in i:
        continue

    temp_file = tempfile.NamedTemporaryFile()
    url = i["mvum_pdf"]
    etag_filename = os.path.join(cache_dir, i["id"] + ".etag.txt")
    subprocess.run(
        ["curl",
        "--etag-save", etag_filename, "--etag-compare", etag_filename,
        # add some headers to make server happy?
        "--http1.1",
        "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
        "-H", "Accept-Encoding: identity", "-H", "Connection: Keep-Alive",
        "-o", temp_file.name, url],
        check=True)
    result = subprocess.run(["md5", "-q", temp_file.name], capture_output=True, check=True)
    md5hash = result.stdout.decode('ascii').rstrip()
    i["mvum_md5"] = md5hash
    cached_pdf_path = os.path.join(cache_dir, md5hash + ".pdf")
    subprocess.run(["mv", temp_file.name, cached_pdf_path], check=True)

# write json back out!
f.truncate(0)
json.dump(data, f, indent=4)
