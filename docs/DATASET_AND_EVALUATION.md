# Dataset, Evaluation, and Reproducibility

## Dataset schema

The training script expects a CSV file named `phishing_dataset.csv` in the project root with at least these columns:

- `url`: the URL string.
- `label`: either `legitimate` or `phishing`, case-insensitive after normalization.

Example:

```csv
url,label
https://example.com,legitimate
http://suspicious.example/login,phishing
```

Rows with missing values or empty URL strings are removed. Unexpected labels cause training to stop with an error rather than silently assigning them a class.

## Dataset provenance

The original project's supplied CSV did not include a source URL, paper citation, or clear redistribution license in its metadata. The repository therefore excludes the raw dataset from Git by default. Before sharing it publicly, identify the original source, confirm that redistribution is permitted, and record required citations or terms. Do not assume that a dataset is public domain just because it was downloaded from the internet.

To run the training script from a fresh clone, obtain an authorized copy and place it at the project root with the exact filename `phishing_dataset.csv`.

## Domain-disjoint evaluation

The training script groups URLs by registered domain or host group before dividing examples into training and test sets. This aims to prevent the same registered domain from appearing in both sets, which can make a random row split unrealistically easy.

Training prints:

- Accuracy
- Precision for the phishing class
- Recall for the phishing class
- F1 score
- False positive rate among legitimate examples
- Confusion matrix, actual labels by rows and predicted labels by columns
- Scikit-learn classification report

Record the actual output of your own full training run in a presentation. Do not use illustrative metrics, smoke-test figures, or metrics from a different dataset version as if they were current results.

## Interpreting metrics

- **Precision:** among URLs predicted as phishing, the proportion labeled phishing in the test split.
- **Recall:** among phishing-labeled URLs in the test split, the proportion predicted as phishing.
- **F1 score:** harmonic mean of precision and recall.
- **False positive rate:** among legitimate-labeled URLs in the test split, the fraction predicted as phishing.
- **Confusion matrix:** count of true negatives, false positives, false negatives, and true positives according to the displayed label order.

These measures describe performance on the chosen test subset, not guaranteed production performance. Dataset age, label errors, duplicated or near-duplicated URLs, changing attacker behavior, and differences between training data and real traffic all affect reliability. Domain-disjoint splitting reduces one source of leakage but does not solve all evaluation issues.

## Reproducing a run

Record the Python version, dependency versions, dataset source and version, training command, and full terminal metrics. Keep a copy of the terminal output or redirect it to a text file for your academic report. Avoid publishing URLs that contain private tokens or other sensitive values.
