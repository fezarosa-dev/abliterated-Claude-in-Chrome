# Abliterated Claude in Chrome

Removes site restrictions from the [Claude in Chrome](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) browser extension.

By default, Claude in Chrome blocks certain websites (Reddit, social media, etc.) via a server-side category check. This project patches the extension so it works on **all sites**.

## Install (2 steps)

1. Download the latest `claude-unblocked-*.zip` from [Releases](../../releases/latest)
2. Extract → open `chrome://extensions/` → enable **Developer mode** → **Load unpacked** → select the extracted folder

If you have the original "Claude" extension installed, **remove it first** (they share the same ID and can't coexist).

Done. The patched version appears as **"Claude (Unblocked)"** with an unlock badge on the icon.

## Per-site control

Click the extension icon to open the popup:

- **Toggle** — allow or block any site individually
- **Open Side Panel** — opens Claude's chat panel
- All sites are **allowed by default**. Blocking a site re-enables Anthropic's original restrictions for that site only.

## Updating

A GitHub Action checks daily for new versions and publishes a new release automatically. To update:

1. Download the new ZIP from [Releases](../../releases/latest)
2. Extract over the old folder (or to a new one)
3. Go to `chrome://extensions/` → click the ↻ reload button on the extension

## How it works

A fetch interceptor is injected at the top of `service-worker-loader.js`:

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

When the extension checks if a site is allowed (`POST /api/web/url_hash_check/browser_extension`), the interceptor returns "allowed" immediately. All other API calls pass through untouched.

## Building locally

If you prefer to build from your own installed extension instead of downloading the release:

```bash
pip install Pillow  # optional, for icon badge
python install.py
```

This copies your locally installed extension, patches it, and outputs to `LOAD-THIS-IN-CHROME/`.

Or build from the Chrome Web Store directly (same thing the CI does):

```bash
pip install Pillow
python build.py download && python build.py patch
# patched extension is in build/patched/
```

## Supported browsers

Chrome, Chromium, Brave, Edge — on Linux, macOS, and Windows.

## FAQ

**Q: Why do I need to remove the original extension?**
Both share the same extension ID. Chrome allows only one extension per ID.

**Q: Is this safe?**
The patch only changes how site categories are checked — 10 lines of readable code shown above. All other functionality works identically.

**Q: Can I build it myself instead of trusting the release?**
Yes. Clone the repo and run `python build.py download && python build.py patch`. The patched extension is in `build/patched/`.

## Disclaimer

This tool modifies a commercial extension for personal use. It bypasses an intentional site restriction by Anthropic. Use at your own discretion.

## License

MIT
