import argparse
import json
import re

parser = argparse.ArgumentParser("find_ranger")
parser.add_argument("--rdb", help="Path to Ranger Distict Boundaries file (GeoJSO)", type=str)
parser.add_argument("--q", help="Ranger District search query", type=str)
args = parser.parse_args()

f = open(args.rdb)
data = json.load(f)

for i in data["features"]:
    if "type" not in i or i["type"] != "Feature":
        continue

    match = False
    properties = i["properties"]
    if re.search(args.q, properties["FORESTNAME"], re.IGNORECASE):
        match = True
    if re.search(args.q, properties["DISTRICTNAME"], re.IGNORECASE):
        match = True
    if match:
        print(
            properties["RANGERDISTRICTID"], "\t",
            properties["FORESTNAME"], "\t",
            properties["DISTRICTNAME"])

f.close()
