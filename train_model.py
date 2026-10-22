"""Train a hybrid domain-character and URL-structure phishing classifier."""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold

from model_pipeline import MODEL_VERSION, build_matrix, create_vectorizers
from url_features import (
    domain_character_text,
    explain_domain,
    explain_url_structure,
    get_group_domain,
    recognized_major_homepage,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "phishing_dataset.csv"
MODEL_PATH = BASE_DIR / "phishing_model.pkl"


def main() -> None:
    print("Loading phishing dataset...")
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH, usecols=["url", "label"]).dropna().copy()
    df["url"] = df["url"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip().str.lower()
    df = df[df["url"] != ""].reset_index(drop=True)
    labels = {"legitimate": 0, "phishing": 1}
    unexpected = sorted(set(df["label"]) - set(labels))
    if unexpected:
        raise ValueError(f"Unexpected labels: {unexpected}. Expected legitimate and phishing.")
    if df["label"].nunique() != 2:
        raise ValueError("The dataset must contain both legitimate and phishing examples.")

    urls = df["url"].tolist()
    y = df["label"].map(labels).to_numpy(dtype=np.int8)
    print(f"Loaded {len(urls):,} URLs")
    print(f"Legitimate: {(y == 0).sum():,}, phishing: {(y == 1).sum():,}")
    print("Resolving registrable domains to split by domain, not random URL rows...")
    groups = np.asarray([get_group_domain(url) for url in urls], dtype=object)
    print(f"Unique registrable domains or host groups: {len(set(groups)):,}")

    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx, test_idx = next(splitter.split(np.zeros(len(y), dtype=np.uint8), y, groups))
    train_urls = [urls[i] for i in train_idx]
    test_urls = [urls[i] for i in test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    print(f"Training rows: {len(train_idx):,}; held-out rows: {len(test_idx):,}")
    print("No registrable domain should appear in both train and test sets.")

    numeric_vectorizer, numeric_scaler, domain_vectorizer, path_vectorizer = create_vectorizers()
    print("Extracting domain and URL features for training...")
    X_train, train_feature_rows = build_matrix(
        train_urls,
        numeric_vectorizer,
        numeric_scaler,
        domain_vectorizer,
        path_vectorizer,
        fit_numeric=True,
    )
    del train_feature_rows
    print(f"Training matrix: {X_train.shape[0]:,} rows × {X_train.shape[1]:,} sparse features")
    print("Training the hybrid domain and URL character classifier. This may take several minutes on a laptop...")
    model = SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=1e-5,
        max_iter=20,
        tol=1e-3,
        random_state=42,
        average=True,
    )
    model.fit(X_train, y_train)
    del X_train

    print("Building held-out domain test matrix...")
    X_test, test_feature_rows = build_matrix(
        test_urls,
        numeric_vectorizer,
        numeric_scaler,
        domain_vectorizer,
        path_vectorizer,
        fit_numeric=False,
    )
    del test_feature_rows
    predictions = model.predict(X_test)

    print("\nEvaluation on held-out domains, not merely random URL rows")
    print(f"Accuracy:  {accuracy_score(y_test, predictions) * 100:.2f}%")
    print(f"Precision: {precision_score(y_test, predictions, pos_label=1, zero_division=0) * 100:.2f}%")
    print(f"Recall:    {recall_score(y_test, predictions, pos_label=1, zero_division=0) * 100:.2f}%")
    print(f"F1 score:  {f1_score(y_test, predictions, pos_label=1, zero_division=0) * 100:.2f}%")
    false_positives = int(((predictions == 1) & (y_test == 0)).sum())
    true_negatives = int(((predictions == 0) & (y_test == 0)).sum())
    fpr = false_positives / (false_positives + true_negatives) if false_positives + true_negatives else 0.0
    print(f"False positive rate among legitimate examples: {fpr * 100:.2f}%")
    print("Confusion matrix rows=actual, columns=predicted; order legitimate, phishing:")
    print(confusion_matrix(y_test, predictions, labels=[0, 1]))
    print(classification_report(y_test, predictions, labels=[0, 1], target_names=["Legitimate", "Phishing"], zero_division=0))

    bundle = {
        "model_version": MODEL_VERSION,
        "classifier": model,
        "numeric_vectorizer": numeric_vectorizer,
        "numeric_scaler": numeric_scaler,
        "domain_vectorizer": domain_vectorizer,
        "path_vectorizer": path_vectorizer,
        "model_name": "Hybrid domain and URL character n-gram classifier",
        "domain_split_evaluation": True,
    }
    joblib.dump(bundle, MODEL_PATH, compress=3)
    print(f"Saved model bundle to: {MODEL_PATH}")
    print("Important: domain-disjoint metrics are more demanding, but still depend on dataset quality and date.")

    print("\nExample URL analysis, illustrative until independently verified:")
    for url in [
        "https://github.com",
        "https://github.com/login",
        "https://github.com.evil.example/login",
        "https://githu-b.com/login/verify",
        "http://paypal-secure-login.xyz",
        "https://example.com/account/verify?session=12345",
    ]:
        row, _ = build_matrix([url], numeric_vectorizer, numeric_scaler, domain_vectorizer, path_vectorizer)
        score = float(model.predict_proba(row)[0][list(model.classes_).index(1)]) * 100
        homepage = recognized_major_homepage(url)
        verdict = f"RECOGNIZED EXACT HOMEPAGE: {homepage}" if homepage else ("POTENTIAL PHISHING" if int(model.predict(row)[0]) == 1 else "NO INDICATORS DETECTED")
        print(f"{verdict:42} score={score:6.2f}%  {url}")
        print(f"  Domain: {explain_domain(url)}")
        print(f"  URL:    {explain_url_structure(url)}")


if __name__ == "__main__":
    main()
