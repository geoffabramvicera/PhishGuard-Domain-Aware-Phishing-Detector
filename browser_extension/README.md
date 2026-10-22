# PhishGuard browser extension

This Manifest V3 extension scans a current tab URL or a pasted URL by calling your existing local Flask backend at `http://127.0.0.1:5000`.

## Install in Brave

1. Start the backend from the main Python project folder:
   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```
2. Open `brave://extensions`.
3. Turn on Developer mode.
4. Click Load unpacked and select this `browser_extension` folder, the folder containing `manifest.json`.
5. Pin PhishGuard from the extension menu.
6. Open a regular website, click PhishGuard, then choose Analyze URL.

For Chrome, use `chrome://extensions` instead.

You do not need to start the separate HTTP server on port 8000 when using this extension. You must keep the Python backend running on port 5000. `phishing_model.pkl` must exist in the main project folder, and the backend must successfully load it.

## What it can and cannot do

- Reads the active tab URL after the user opens the extension.
- Lets the user paste any `http://` or `https://` URL for analysis.
- Displays the API's verdict, estimated phishing score, domain analysis, and URL structure analysis.
- Does not automatically scan every page or block navigation.
- Does not inspect page contents, check live domain reputation, or guarantee safety.

If the backend URL changes, update `API_BASE` at the top of `popup.js`, and update `host_permissions` in `manifest.json` to match that local address. Keep the host permissions limited to the local API.
