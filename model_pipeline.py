"""Shared hybrid model matrix construction for training and inference."""
from __future__ import annotations

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import StandardScaler

from url_features import domain_character_text, extract_features, path_character_text

MODEL_VERSION = 3


def create_vectorizers():
    """Create a numeric feature encoder and a stateless domain character encoder."""
    numeric_vectorizer = DictVectorizer(sparse=True, dtype=np.float32)
    numeric_scaler = StandardScaler(with_mean=False, copy=True)
    domain_vectorizer = HashingVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
        n_features=2**18,
        alternate_sign=False,
        norm="l2",
        lowercase=True,
        dtype=np.float32,
    )
    path_vectorizer = HashingVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        n_features=2**16,
        alternate_sign=False,
        norm="l2",
        lowercase=True,
        dtype=np.float32,
    )
    return numeric_vectorizer, numeric_scaler, domain_vectorizer, path_vectorizer


def build_matrix(
    urls: list[str],
    numeric_vectorizer: DictVectorizer,
    numeric_scaler: StandardScaler,
    domain_vectorizer: HashingVectorizer,
    path_vectorizer: HashingVectorizer,
    *,
    fit_numeric: bool = False,
):
    """Combine numeric features with hostname and path/query character n-grams."""
    feature_rows = [extract_features(url) for url in urls]
    if fit_numeric:
        numeric = numeric_vectorizer.fit_transform(feature_rows)
        numeric = numeric_scaler.fit_transform(numeric)
    else:
        numeric = numeric_vectorizer.transform(feature_rows)
        numeric = numeric_scaler.transform(numeric)

    domain_text = [domain_character_text(url) for url in urls]
    domain_ngrams = domain_vectorizer.transform(domain_text)
    path_text = [path_character_text(url) for url in urls]
    path_ngrams = path_vectorizer.transform(path_text)
    combined = hstack((numeric, domain_ngrams, path_ngrams), format="csr", dtype=np.float32)
    return combined, feature_rows
