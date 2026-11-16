#!/usr/bin/env python3
"""
Build script for CI — downloads Claude in Chrome from the Web Store,
patches it, and packages it as a ZIP for release.

Usage:
  python build.py download   # download CRX from Chrome Web Store
  python build.py patch      # extract and patch the extension
  python build.py version    # print the current version
  python build.py zip        # create release ZIP
"""

import io
import json
import os
import shutil
import struct
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

EXTENSION_ID = "fcoeoabgfenejglbffodgkkbkcdhcgfn"
CHROME_VERSION = "131.0.6778.86"
BUILD_DIR = Path("build")
CRX_PATH = BUILD_DIR / "extension.crx"
EXTRACTED_DIR = BUILD_DIR / "extracted"
PATCHED_DIR = BUILD_DIR / "patched"

FETCH_INTERCEPTOR = """\
// Site unblock with per-site blocklist support
const _fetch = globalThis.fetch;
let _blockedSites = new Set();
chrome.storage.local.get({blockedSites: []}, r => { _blockedSites = new Set(r.blockedSites); });
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.blockedSites)
    _blockedSites = new Set(changes.blockedSites.newValue || []);
});
globalThis.fetch = function(url, opts) {
  if (String(url).includes('/api/web/url_hash_check/')) {
    try {
      const body = typeof opts?.body === 'string' ? JSON.parse(opts.body) : {};
      const host = body.url ? new URL(body.url).hostname.replace(/^www\\./, '') : '';
      if (host && _blockedSites.has(host))
        return _fetch.apply(this, arguments);
    } catch(e) {}
    return Promise.resolve(new Response(JSON.stringify({category: "category0"}), {
      status: 200, headers: {"Content-Type": "application/json"}
    }));
  }
  return _fetch.apply(this, arguments);
};

"""


def download():
    """Download CRX from Chrome Web Store."""
    BUILD_DIR.mkdir(exist_ok=True)

    url = (
        f"https://clients2.google.com/service/update2/crx"
        f"?response=redirect"
        f"&prodversion={CHROME_VERSION}"
        f"&acceptformat=crx2,crx3"
        f"&x=id%3D{EXTENSION_ID}%26uc"
    )

    print(f"Downloading from Chrome Web Store...")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        data = resp.read()

    CRX_PATH.write_bytes(data)
    print(f"Downloaded: {len(data)} bytes")


def extract_crx(crx_path: Path, dest: Path):
    """Extract a CRX3 file (ZIP with a header)."""
    data = crx_path.read_bytes()

    # CRX3 format: magic(4) + version(4) + header_size(4) + header + ZIP
    if data[:4] == b'Cr24':
        version = struct.unpack('<I', data[4:8])[0]
        if version == 3:
            header_size = struct.unpack('<I', data[8:12])[0]
            zip_start = 12 + header_size
        elif version == 2:
            pk_len = struct.unpack('<I', data[8:12])[0]
            sig_len = struct.unpack('<I', data[12:16])[0]
            zip_start = 16 + pk_len + sig_len
        else:
            raise ValueError(f"Unknown CRX version: {version}")
    elif data[:2] == b'PK':
        zip_start = 0
    else:
        raise ValueError("Not a valid CRX or ZIP file")

    if dest.exists():
        shutil.rmtree(dest)

    with zipfile.ZipFile(io.BytesIO(data[zip_start:])) as zf:
        zf.extractall(dest)

    print(f"Extracted to {dest}")


def patch():
    """Extract CRX and apply patches."""
    extract_crx(CRX_PATH, EXTRACTED_DIR)

    if PATCHED_DIR.exists():
        shutil.rmtree(PATCHED_DIR)
    shutil.copytree(EXTRACTED_DIR, PATCHED_DIR)

    # Remove integrity metadata
    metadata = PATCHED_DIR / "_metadata"
    if metadata.exists():
        shutil.rmtree(metadata)

    # Patch manifest
    manifest_path = PATCHED_DIR / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest.pop("update_url", None)
    manifest["name"] = "Claude (Unblocked)"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=3)

    # Inject fetch interceptor
    loader = PATCHED_DIR / "service-worker-loader.js"
    content = loader.read_text(encoding="utf-8")
    if "/api/web/url_hash_check/" not in content:
        loader.write_text(FETCH_INTERCEPTOR + content, encoding="utf-8")

    # Add popup
    patch_files = Path(__file__).parent / "patch-files"
    if patch_files.exists():
        for f in patch_files.iterdir():
            shutil.copy2(f, PATCHED_DIR / f.name)

    # Add popup to manifest action
    manifest_path = PATCHED_DIR / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest.setdefault("action", {})["default_popup"] = "popup.html"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=3)

    # Generate icon
    generate_icon(PATCHED_DIR / "icon-128.png")

    print("Patch applied")


def generate_icon(icon_path: Path):
    """Add unlock padlock badge to the extension icon."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed — skipping icon")
        return

    if not icon_path.exists():
        return

    img = Image.open(icon_path).convert("RGBA").resize((128, 128), Image.LANCZOS)
    overlay = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy, r = 92, 92, 32
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=(255, 255, 255, 240), outline=(60, 60, 60, 200), width=2)
    bx, by, bw, bh = 78, 90, 28, 22
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4, fill=(76, 175, 80))
    draw.arc([bx + 5, by - 18, bx + 23, by + 4], start=180, end=350,
             fill=(76, 175, 80), width=4)
    draw.ellipse([bx + 11, by + 7, bx + 17, by + 13], fill=(255, 255, 255))

    Image.alpha_composite(img, overlay).save(icon_path)


def version():
    """Print the extension version."""
    manifest_path = PATCHED_DIR / "manifest.json"
    if not manifest_path.exists():
        # Try from extracted
        manifest_path = EXTRACTED_DIR / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    print(manifest["version"])


def make_zip():
    """Create release ZIP from patched extension."""
    manifest_path = PATCHED_DIR / "manifest.json"
    with open(manifest_path) as f:
        ver = json.load(f)["version"]

    zip_name = f"claude-unblocked-v{ver}"
    # shutil.make_archive creates zip_name.zip from PATCHED_DIR
    # We want the ZIP to contain a single folder
    staging = BUILD_DIR / zip_name
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(PATCHED_DIR, staging)

    shutil.make_archive(zip_name, "zip", BUILD_DIR, zip_name)
    print(f"Created {zip_name}.zip")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build.py [download|patch|version|zip]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "download":
        download()
    elif cmd == "patch":
        patch()
    elif cmd == "version":
        version()
    elif cmd == "zip":
        make_zip()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
