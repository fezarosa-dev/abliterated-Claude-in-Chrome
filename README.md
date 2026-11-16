# Abliterated Claude in Chrome

Removes site restrictions from the [Claude in Chrome](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) browser extension.

By default, Claude in Chrome blocks interaction with certain websites (Reddit, social media, etc.) via a server-side category check. This tool patches the extension locally so it works on **all sites**.

## How it works

The installer copies your installed Claude in Chrome extension, injects a 10-line fetch interceptor into the service worker entry point, and outputs a patched extension you load as "unpacked" in Chrome. No files are modified in the original extension.

The interceptor replaces the server-side URL category check (`/api/web/url_hash_check/`) with an immediate `category0` (allowed) response. Everything else works exactly like the original.

## Requirements

- **Chrome** (or Chromium, Brave, Edge) with **Claude in Chrome** installed from the Web Store
- **Python 3.9+**
- **Pillow** *(optional, for the custom icon)*: `pip install Pillow`

## Install

```bash
git clone https://github.com/fezarosa-dev/abliterated-Claude-in-Chrome.git
cd abliterated-Claude-in-Chrome
python install.py
```

Then in Chrome:

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked** → select the `patched-extension/` folder
4. **Disable** the original "Claude" extension (keep it installed for updates)

That's it. The patched extension appears as **"Claude (Unblocked)"** with an unlock badge on the icon.

## Update

When the original extension updates via the Web Store, just run the installer again:

```bash
python install.py
```

Then reload the extension in `chrome://extensions/` (click the refresh icon on the card).

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

Flatpak and Snap Chrome installations on Linux are also supported.

## How it works (technical)

The patch adds a fetch interceptor at the top of `service-worker-loader.js`:

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

This intercepts the category check API call before it reaches Anthropic's server and returns an "allowed" response. All other API calls (chat, authentication, etc.) pass through untouched.

The patch is applied to the service worker entry point — not to minified chunk files — so it survives extension updates without needing to find renamed functions in re-minified code.

## Disclaimer

This tool modifies a commercial extension for personal use. It bypasses an intentional safety classification by Anthropic. Use at your own discretion.

## License

MIT
