#!/usr/bin/env python3
"""
Abliterated Claude in Chrome — Installer/Updater
Removes site category restrictions from Claude in Chrome extension.

Works on Linux, macOS, and Windows.
Usage: python install.py [--force]
"""

import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path

EXTENSION_ID = "fcoeoabgfenejglbffodgkkbkcdhcgfn"
PATCHED_NAME = "Claude (Unblocked)"

FETCH_INTERCEPTOR = """\
// Intercepts site category check — unlocks all sites
const _fetch = globalThis.fetch;
globalThis.fetch = function(url, opts) {
  if (String(url).includes('/api/web/url_hash_check/')) {
    return Promise.resolve(new Response(JSON.stringify({category: "category0"}), {
      status: 200, headers: {"Content-Type": "application/json"}
    }));
  }
  return _fetch.apply(this, arguments);
};

"""


def find_chrome_extension_dirs():
    """Find all possible Chrome/Chromium extension directories across platforms."""
    home = Path.home()
    system = platform.system()
    candidates = []

    if system == "Linux":
        candidates = [
            # Flatpak
            home / ".var/app/com.google.Chrome/config/google-chrome",
            home / ".var/app/org.chromium.Chromium/config/chromium",
            # Standard
            home / ".config/google-chrome",
            home / ".config/chromium",
            home / ".config/BraveSoftware/Brave-Browser",
            # Snap
            home / "snap/chromium/common/chromium",
        ]
    elif system == "Darwin":
        app_support = home / "Library/Application Support"
        candidates = [
            app_support / "Google/Chrome",
            app_support / "Chromium",
            app_support / "BraveSoftware/Brave-Browser",
            app_support / "Microsoft Edge",
        ]
    elif system == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        candidates = [
            local / "Google/Chrome/User Data",
            local / "Chromium/User Data",
            local / "BraveSoftware/Brave-Browser/User Data",
            local / "Microsoft/Edge/User Data",
        ]

    found = []
    for base in candidates:
        for profile in ["Default", "Profile 1", "Profile 2", "Profile 3"]:
            ext_dir = base / profile / "Extensions" / EXTENSION_ID
            if ext_dir.is_dir():
                found.append((str(base.name), ext_dir))

    return found


def get_latest_version(ext_dir: Path) -> Path | None:
    """Get the latest version directory of the extension."""
    versions = sorted(
        [d for d in ext_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )
    return versions[-1] if versions else None


def patch_extension(source: Path, dest: Path):
    """Copy and patch the extension."""
    # Clean and copy
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)

    # Remove integrity metadata
    metadata = dest / "_metadata"
    if metadata.exists():
        shutil.rmtree(metadata)

    # Patch manifest
    manifest_path = dest / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest.pop("update_url", None)
    manifest["name"] = PATCHED_NAME
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=3)

    # Inject fetch interceptor into service worker loader
    loader_path = dest / "service-worker-loader.js"
    if not loader_path.exists():
        print("ERROR: service-worker-loader.js not found")
        sys.exit(1)

    content = loader_path.read_text(encoding="utf-8")
    if "/api/web/url_hash_check/" not in content:
        loader_path.write_text(FETCH_INTERCEPTOR + content, encoding="utf-8")

    # Generate icon with unlock badge
    generate_icon(dest / "icon-128.png")


def generate_icon(icon_path: Path):
    """Add unlock padlock badge to the extension icon."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  Pillow not installed — skipping icon customization")
        print("  (optional: pip install Pillow)")
        return

    if not icon_path.exists():
        return

    img = Image.open(icon_path).convert("RGBA").resize((128, 128), Image.LANCZOS)
    overlay = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # White circle background
    cx, cy, r = 92, 92, 32
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=(255, 255, 255, 240), outline=(60, 60, 60, 200), width=2)
    # Lock body (green)
    bx, by = 78, 90
    bw, bh = 28, 22
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4, fill=(76, 175, 80))
    # Open shackle
    draw.arc([bx + 5, by - 18, bx + 23, by + 4], start=180, end=350,
             fill=(76, 175, 80), width=4)
    # Keyhole
    draw.ellipse([bx + 11, by + 7, bx + 17, by + 13], fill=(255, 255, 255))

    Image.alpha_composite(img, overlay).save(icon_path)


def main():
    force = "--force" in sys.argv
    script_dir = Path(__file__).resolve().parent
    dest = script_dir / "LOAD-THIS-IN-CHROME"
    hash_file = script_dir / ".current-hash"

    print("Abliterated Claude in Chrome — Installer")
    print("=" * 44)

    # Find extension
    found = find_chrome_extension_dirs()
    if not found:
        print(f"\nClaude in Chrome extension not found.")
        print("Make sure it's installed from the Chrome Web Store first.")
        sys.exit(1)

    if len(found) == 1:
        browser_name, ext_dir = found[0]
    else:
        print("\nMultiple installations found:")
        for i, (name, path) in enumerate(found):
            print(f"  [{i + 1}] {name} — {path}")
        try:
            choice = input("Choose [1]: ").strip() or "1"
        except EOFError:
            choice = "1"
        browser_name, ext_dir = found[int(choice) - 1]

    latest = get_latest_version(ext_dir)
    if not latest:
        print("No version directory found")
        sys.exit(1)

    # Check if update needed
    git_hash_file = latest / "git-hash.txt"
    current_hash = git_hash_file.read_text().strip() if git_hash_file.exists() else latest.name
    saved_hash = hash_file.read_text().strip() if hash_file.exists() else ""

    if current_hash == saved_hash and not force:
        print(f"\nAlready up to date: {current_hash}")
        print("Use --force to reinstall anyway.")
        return

    action = "Updating" if saved_hash else "Installing"
    print(f"\n{action} from {browser_name} (version: {current_hash})")

    patch_extension(latest, dest)
    hash_file.write_text(current_hash)

    print(f"\nDone! Extension patched at:\n  {dest}\n")
    print("To activate:")
    print("  1. Open chrome://extensions/")
    print("  2. REMOVE the original 'Claude' extension (they can't coexist)")
    print("  3. Enable 'Developer mode' (top right)")
    print("  4. Click 'Load unpacked'")
    print(f"  5. Select the folder that just opened (or navigate to):")
    print(f"     {dest}")
    print()
    print("To update later:")
    print("  1. Install Claude in Chrome from the Web Store again")
    print(f"  2. Run: python {Path(__file__).name}")
    print("  3. Remove the original again, reload the patched one")

    open_folder(dest)


def open_folder(path: Path):
    """Open folder in the system file manager."""
    import subprocess
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == "Darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == "Windows":
            subprocess.Popen(["explorer", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
