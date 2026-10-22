# System Architecture and Model Overview

## Components

| Component | Responsibility |
|---|---|
| `phishing_dataset.csv` | Labeled URLs used to fit and evaluate the classifier. The file is not tracked in Git by default until redistribution rights are documented. |
| `url_features.py` | Parses the URL and creates domain and URL structure features, explanatory indicators, and text strings for character n-grams. |
| `model_pipeline.py` | Creates feature vectorizers, scales numeric values, and combines numeric, hostname n-gram, and path/query n-gram matrices. |
| `train_model.py` | Reads and checks labels, groups examples by registered domain, splits domains between training and testing, evaluates the classifier, and saves the model bundle. |
| `app.py` | Exposes `/health` and `/predict` through a local Flask server. |
| `index.html` | Standalone dashboard for manually analyzing URLs and reading explanatory information. |
| `browser_extension/` | Manifest V3 popup that reads the active tab URL or accepts a pasted URL, then calls the local API. |
| `public_suffix_list.dat` | Offline snapshot used to identify public suffixes and registered domains more accurately than simply splitting on dots. |

## Inference flow

1. The user selects a URL in the web interface or browser extension.
2. The frontend sends a JSON POST request to `http://127.0.0.1:5000/predict`.
3. The API validates the input and uses the shared feature code.
4. The feature pipeline creates numeric domain and URL indicators plus hostname and path/query character n-grams.
5. The saved classifier estimates the probability of the phishing label.
6. The API returns its raw classifier prediction, score, final application label, and explanatory domain and URL observations.
7. The frontend displays the result with an explicit disclaimer.

## Model representation

The pipeline combines three feature groups:

- Numeric domain and URL features from `url_features.py`.
- Character n-grams derived from the hostname.
- Character n-grams derived from URL path and query text.

This allows the model to learn textual fragments and structure patterns. It still does not query live reputation, inspect page content, or prove ownership of a domain.

## Evaluation strategy

`train_model.py` uses a grouped split so URLs associated with the same registered domain are intended to stay in one group. This is more useful for estimating generalization to unseen domains than a random URL-row split, though all metrics remain dependent on the dataset and the group assignment. The training output includes accuracy, precision, recall, F1 score, false positive rate, confusion matrix, and a class report.

## Homepage context rule

A narrow rule recognizes the exact HTTPS root homepage for a small configured set of major domains. It does not trust every subpage or every subdomain. This mitigates a known failure mode of URL-structure-only classifiers, but it is not a reputation database or a substitute for threat intelligence.
