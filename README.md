# Abliterated Claude in Chrome

Removes site restrictions from the [Claude in Chrome](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) browser extension.

By default, Claude in Chrome blocks interaction with certain websites (Reddit, social media, etc.) via a server-side category check. This tool patches the extension locally so it works on **all sites**.

## Quick start

### 1. Prerequisites

- **Claude in Chrome** installed from the [Chrome Web Store](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbvcdhcgfn)
- **Python 3.9+**
- *(optional)* `pip install Pillow` — adds an unlock badge to the icon

### 2. Install

```bash
git clone https://github.com/fezarosa-dev/abliterated-Claude-in-Chrome.git
cd abliterated-Claude-in-Chrome
python install.py
```

### 3. Load in Chrome

1. Go to `chrome://extensions/`
2. **Remove** the original "Claude" extension (click "Remove" — they can't coexist)
3. Enable **Developer mode** (top right toggle)
4. Click **Load unpacked** → select the `LOAD-THIS-IN-CHROME/` folder (it opens automatically after install)

Done. The patched version appears as **"Claude (Unblocked)"** with an unlock badge on the icon.

## How updating works

The original and patched extensions share the same ID — Chrome can't have both at once. So the update cycle is:

```
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  FIRST TIME                                              │
  │  ══════════                                              │
  │  Claude (original) ──install.py──▶ Claude (Unblocked)    │
  │  installed from          │         loaded as unpacked     │
  │  Web Store               │                                │
  │                          ▼                                │
  │                    Remove original                        │
  │                                                          │
  │  UPDATING                                                │
  │  ════════                                                │
  │  1. Install original from Web Store again                │
  │  2. python install.py                                    │
  │  3. Remove original                                      │
  │  4. Reload patched in chrome://extensions/               │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
```

You only need the original installed **during the install.py step** — it's the source the script copies from. After that, remove it and use the patched one.

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

## How it works

The installer copies your installed extension and injects a fetch interceptor at the top of `service-worker-loader.js`:

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

When the extension checks if a site is allowed (`POST /api/web/url_hash_check/browser_extension`), the interceptor returns "allowed" immediately without calling Anthropic's server. All other API calls pass through untouched.

The patch lives in the service worker entry point — a small, stable file — not in minified chunks. Running `install.py` after an update re-applies the same interceptor to the new version.

## FAQ

**Q: Why can't I keep both installed?**
Both share the same extension ID. Chrome allows only one extension per ID. You must remove the original before loading the patched one.

**Q: Will the patched version update automatically?**
No — that's the point. Auto-updates would overwrite the patch. When you want a new version, install the original from the Web Store, run `install.py`, then remove the original.

**Q: Is this safe?**
The patch only changes how site categories are checked. All other functionality (chat, auth, side panel) works identically to the original. The interceptor is 10 lines of readable code shown above.

## Disclaimer

This tool modifies a commercial extension for personal use. It bypasses an intentional site classification by Anthropic. Use at your own discretion.

## License

MIT
