# Publish This Project to GitHub

This guide publishes the source code while keeping local Python environments, generated model files, and the raw dataset out of Git by default.

## Before publishing

1. Confirm the folder contains the latest working application and extension.
2. Run the tests:

   ```powershell
   .\.venv\Scripts\python.exe -m unittest discover -v
   ```

3. Review `.gitignore`. It intentionally excludes `phishing_dataset.csv` because its source and redistribution license have not yet been recorded, and excludes `phishing_model.pkl` because it is generated locally.
4. Do not commit API keys, passwords, `.env` files, personal data, or private URLs.
5. Choose a license for your own code before inviting people to reuse it. Verify the dataset's terms and Public Suffix List attribution separately.

## Option A: Git commands

### 1. Create an empty GitHub repository

On GitHub, create a new repository. A suitable name is `PhishGuard-Domain-Aware-Phishing-Detector`. Choose the visibility you prefer. Do not initialize the remote repository with a README, license, or `.gitignore`, because this project already has local versions.

### 2. Open PowerShell in the project root

Run `dir` and confirm `app.py`, `README.md`, `requirements.txt`, and `browser_extension` appear.

Check Git is installed:

```powershell
git --version
```

If Git is not installed, install Git for Windows and reopen PowerShell.

### 3. Initialize and review the repository

```powershell
git init
git branch -M main
git status --short
```

Stage the files:

```powershell
git add .
git status --short
```

**Review the staged file list before committing.** `phishing_dataset.csv`, `.venv`, and `phishing_model.pkl` should not appear. Verify the ignore rules with:

```powershell
git check-ignore -v phishing_dataset.csv
git check-ignore -v phishing_model.pkl
```

If `git status --short` shows secrets, private data, or files you do not intend to publish, stop and remove them from the staging area before committing.

### 4. Commit the project

```powershell
git commit -m "Initial release of PhishGuard domain-aware detector"
```

If Git asks you to configure your identity, use your preferred Git commit name and email:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Then run the commit command again.

### 5. Connect the remote repository

Replace `YOUR-GITHUB-USERNAME` with your GitHub username and adjust the repository name if you chose another one:

```powershell
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/PhishGuard-Domain-Aware-Phishing-Detector.git
git push -u origin main
```

Follow the authentication prompt from Git or your credential manager. Do not put passwords or personal access tokens directly into a remote URL or share them in chat.

If Git says `origin` already exists, inspect it:

```powershell
git remote -v
```

To correct the URL, use:

```powershell
git remote set-url origin https://github.com/YOUR-GITHUB-USERNAME/PhishGuard-Domain-Aware-Phishing-Detector.git
git push -u origin main
```

### 6. Verify the result

Refresh the repository page on GitHub. Confirm the README renders, the `browser_extension` folder appears, and the raw dataset and model artifact were not committed.

## Option B: GitHub Desktop

1. Install and sign in to GitHub Desktop.
2. Use **File > Add Local Repository** and select this project root. If it is not already a repository, choose the option to create a repository there.
3. Review the changed files and check that the CSV and model artifact are ignored.
4. Commit the files with a message such as `Initial release of PhishGuard domain-aware detector`.
5. Choose **Publish repository**, set the name and visibility, and publish.
6. Review the files on GitHub after publishing.

## Dataset note

The local project archive contains a training CSV so the application can be run locally after extraction. The CSV is ignored by Git because the supplied file does not record its original source or redistribution terms. The README explains how a fresh clone can acquire an authorized copy. Once the source and license have been verified, update the documentation and `.gitignore` before distributing the data.
