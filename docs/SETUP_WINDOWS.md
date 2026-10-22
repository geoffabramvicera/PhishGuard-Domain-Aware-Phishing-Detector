# Windows Setup and Runbook

This guide assumes Python 3.12 is installed and that you are running PowerShell on Windows.

## Find the project root

The project root is the directory containing `app.py`, `train_model.py`, `model_pipeline.py`, `url_features.py`, and `requirements.txt`. In PowerShell, run `dir` and confirm those files appear before continuing.

## First-time setup

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If using a fresh clone of the GitHub repository, first obtain an authorized copy of the training CSV and place it at the project root as `phishing_dataset.csv`. The raw dataset is excluded from Git until its source and redistribution rights have been confirmed.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Train the model:

```powershell
.\.venv\Scripts\python.exe train_model.py
```

Wait for `phishing_model.pkl` to be saved. Do not close the terminal during training.

## Run the standalone web app

Terminal 1:

```powershell
.\.venv\Scripts\python.exe app.py
```

Terminal 2, opened in the same project folder:

```powershell
py -3.12 -m http.server 8000
```

Browse to `http://localhost:8000/index.html`.

## Run the browser extension

Only the backend is needed. Start it using Terminal 1 above, then load the `browser_extension` folder into `brave://extensions` or `chrome://extensions` with Developer mode enabled. See [BROWSER_EXTENSION.md](BROWSER_EXTENSION.md).

## Stop the servers

Select each server terminal and press `Ctrl+C`. The saved model and virtual environment remain on disk.
