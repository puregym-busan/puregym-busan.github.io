#!/usr/bin/env python3
"""Prepare the explicit, flat GitHub Pages files. No dependencies required."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "publish"
PAGES = ("index.html", "concept-a.html", "concept-b.html", "concept-c.html")
PHOTOS = ("training.jpg", "studio.jpg", "recovery.jpg", "sauna.jpg", "plunge.jpg", "locker.jpg", "bikes.jpg")
OUTPUT.mkdir(exist_ok=True)
(ROOT / "qa").mkdir(exist_ok=True)

for name in PAGES:
    source = (ROOT / name).read_text(encoding="utf-8")
    for photo in PHOTOS:
        source = source.replace("assets/" + photo, photo)
    if re.search(r"assets/[^\s\"'<>]+", source):
        raise ValueError(f"Unpackaged asset in {name}")
    (OUTPUT / name).write_text(source, encoding="utf-8")

for photo in PHOTOS:
    shutil.copyfile(ROOT / "assets" / photo, OUTPUT / photo)
shutil.copyfile(ROOT / "favicon.svg", OUTPUT / "favicon.svg")
shutil.copyfile(ROOT / "README.md", OUTPUT / "README.md")
(OUTPUT / ".nojekyll").write_text("", encoding="utf-8")

sources = json.loads((ROOT / "ASSET_SOURCES.json").read_text(encoding="utf-8"))
sources["assets"] = [item for item in sources["assets"] if Path(item["file"]).name in PHOTOS]
for item in sources["assets"]:
    item["file"] = Path(item["file"]).name
(OUTPUT / "ASSET_SOURCES.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

allowlist = (*PAGES, *PHOTOS, "favicon.svg", "README.md", ".nojekyll", "ASSET_SOURCES.json")
unexpected = sorted(path.name for path in OUTPUT.iterdir() if path.name not in allowlist)
if unexpected:
    raise ValueError(f"Unexpected publish files: {unexpected}")

manifest = {name: hashlib.sha256((OUTPUT / name).read_bytes()).hexdigest() for name in sorted(allowlist)}
(ROOT / "qa" / "publish-sha256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
with zipfile.ZipFile(ROOT / "puregym-proposals.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in allowlist:
        archive.write(OUTPUT / name, name)
print(f"Prepared {len(allowlist)} files in publish/ and puregym-proposals.zip")
