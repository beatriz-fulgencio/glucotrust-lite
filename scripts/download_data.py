"""Download a pinned original MedQuAD snapshot; never require Kaggle credentials."""
import hashlib
import argparse
import io
import json
from pathlib import Path
from zipfile import ZipFile

import requests

from glucotrust.ingest import COLLECTIONS

REVISION = "577bd37b96c02d1833b2c9eed2de9f96964e96cb"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use a previously downloaded pinned ZIP instead of network access")
    args = parser.parse_args()
    url = f"https://codeload.github.com/abachaa/MedQuAD/zip/{REVISION}"
    if args.archive:
        content = args.archive.read_bytes()
    else:
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        content = response.content
    root = Path("data/raw/MedQuAD-master")
    with ZipFile(io.BytesIO(content)) as archive:
        for member in archive.infolist():
            parts = Path(member.filename).parts[1:]
            if not parts or ".." in parts or member.is_dir():
                continue
            if parts[0] not in COLLECTIONS and parts[0] not in ("readme.txt", "LICENSE.txt"):
                continue
            target = root.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    manifest_path = Path("data/curated/input_manifest.json")
    if manifest_path.exists():
        expected = json.loads(manifest_path.read_text())
        for name, checksum in expected.items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != checksum:
                raise ValueError(f"Raw source checksum differs: {name}")
    print(f"Downloaded MedQuAD at {REVISION}; existing input checksums verified.")


if __name__ == "__main__":
    main()
