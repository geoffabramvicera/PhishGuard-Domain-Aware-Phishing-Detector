# PhishGuard Browser Extension

The `browser_extension` directory contains a Manifest V3 extension for Chromium-based browsers, including Brave and Google Chrome.

## What it does

- Reads the active tab URL after the user opens the extension popup.
- Allows a URL to be pasted into the popup.
- Sends the selected URL to the local Flask API at `http://127.0.0.1:5000/predict`.
- Displays the verdict, estimated phishing score, domain indicators, and URL indicators.

## Install in Brave

1. Ensure the project is set up and `phishing_model.pkl` exists.
2. Start the backend from the main project root:

   ```powershell
   .\.venv\Scripts\python.exe app.py
   ```

3. Open `brave://extensions`.
4. Enable **Developer mode**.
5. Click **Load unpacked**.
6. Select this repository's `browser_extension` directory. Select the folder containing `manifest.json`, not the repository root.
7. Pin PhishGuard using Brave's extensions menu.
8. Open an ordinary website, open the extension popup, and choose to analyze the current tab or paste a URL.

For Chrome, use `chrome://extensions` instead.

## Permissions

- `activeTab`: allows the extension to read the current active tab after the user invokes the popup.
- `host_permissions` for localhost and `127.0.0.1`: allow the extension to call the local API.

The extension does not need the standalone web server on port 8000. It does need the Flask backend on port 5000. If that address changes, update both `API_BASE` in `popup.js` and the matching host permission in `manifest.json`.

## Limitations

- Manual scanning only. It does not scan every navigation automatically.
- It does not block or prevent navigation.
- It cannot scan browser-internal pages such as extension settings.
- It does not inspect page HTML, JavaScript, downloads, or redirects.
- It depends on the backend and the generated model being available locally.
- A positive or negative prediction is not a guarantee of maliciousness or safety.
