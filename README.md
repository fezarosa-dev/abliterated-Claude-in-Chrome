# Abliterated Claude in Chrome

Removes site restrictions from the [Claude in Chrome](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) browser extension.

By default, Claude in Chrome blocks interaction with certain websites (Reddit, social media, etc.) via a server-side category check. This tool patches the extension locally so it works on **all sites**.

## Quick start

### 1. Install

```bash
git clone https://github.com/fezarosa-dev/abliterated-Claude-in-Chrome.git
cd abliterated-Claude-in-Chrome
python install.py
```

> **Optional:** `pip install Pillow` for a custom icon with an unlock badge.

### 2. Load in Chrome

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked** → select the `LOAD-THIS-IN-CHROME/` folder (it opens automatically after install)
4. **Disable** the original "Claude" extension (toggle it off — don't uninstall it)

Done. The patched version appears as **"Claude (Unblocked)"** with an unlock badge on the icon.

## Important: why you need both extensions

```
┌─────────────────────────────────────────────────────┐
│  Chrome Web Store                                   │
│  ┌───────────────────┐                              │
│  │ Claude (original) │ ← receives auto-updates      │
│  │ DISABLED          │ ← but stays off              │
│  └───────────────────┘                              │
│              │ install.py copies & patches           │
│              ▼                                      │
│  ┌───────────────────┐                              │
│  │ Claude (Unblocked)│ ← the one you actually use    │
│  │ ENABLED (unpacked)│ ← loaded from LOAD-THIS-IN-  │
│  │                   │   CHROME/ folder              │
│  └───────────────────┘                              │
└─────────────────────────────────────────────────────┘
```

- **Keep the original installed but disabled.** Chrome still updates it in the background even when disabled. This is your source for new versions.
- **Only one can be active at a time** — both share the same extension ID, so Chrome won't load them simultaneously.
- The patched version is a local copy that Chrome doesn't auto-update, so your patch stays intact.

## Updating

When Anthropic releases a new version of Claude in Chrome:

```bash
cd abliterated-Claude-in-Chrome
python install.py
```

The script detects the new version automatically, copies it, and re-applies the patch. Then reload the extension in Chrome (click the ↻ icon on the extension card).

Use `--force` to reinstall even if the version hasn't changed:

```bash
python install.py --force
```

## Supported platforms

| Platform | Chrome | Chromium | Brave | Edge |
|----------|--------|----------|-------|------|
| Linux    | ✅     | ✅       | ✅    | —    |
| macOS    | ✅     | ✅       | ✅    | ✅   |
| Windows  | ✅     | ✅       | ✅    | ✅   |

Linux: standard, Flatpak, and Snap installations all supported.

### Requirements

- **Chrome** (or Chromium/Brave/Edge) with **Claude in Chrome** installed from the Web Store
- **Python 3.9+**
- **Pillow** *(optional)*: `pip install Pillow` — adds an unlock badge to the icon

## How it works

The installer copies your installed extension and injects a fetch interceptor at the top of `service-worker-loader.js` — the service worker entry point:

```js
const _fetch = globalThis.fetch;
globalThis.fetch = function(url, opts) {
  if (String(url).includes('/api/web/url_hash_check/')) {
    return Promise.resolve(new Response(
      JSON.stringify({category: "category0"}),
      {status: 200, headers: {"Content-Type": "application/json"}}
    ));
  }
  return _fetch.apply(this, arguments);
};
```

**What this does:** When the extension checks if a site is allowed (via `POST /api/web/url_hash_check/browser_extension`), the interceptor returns "allowed" (`category0`) immediately without calling Anthropic's server. All other API calls (chat, auth, etc.) pass through untouched.

**Why it's resilient:** The patch lives in the service worker entry point — a small, stable file — not in the minified JS chunks that change names and contents with every update. Running `install.py` after an update re-applies the same 10-line interceptor to the new version.

## FAQ

**Q: Can I use both extensions at the same time?**
No. They share the same extension ID. Keep the original disabled, use the patched one.

**Q: Will the patched version update automatically?**
No. That's the point — automatic updates would overwrite the patch. Run `python install.py` when you want to pull in a new version.

**Q: What if I uninstall the original?**
You lose the source for updates. The patched version keeps working, but you'll need to reinstall the original from the Web Store when you want to update.

**Q: Is this safe?**
The patch only changes how site categories are checked. All other functionality (chat, auth, side panel) works identically to the original. The interceptor is 10 lines of transparent code you can read above.

## Disclaimer

This tool modifies a commercial extension for personal use. It bypasses an intentional site classification by Anthropic. Use at your own discretion.

## License

MIT
