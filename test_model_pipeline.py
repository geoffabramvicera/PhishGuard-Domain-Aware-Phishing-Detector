"""Smoke test for the hybrid sparse feature pipeline without the large dataset."""
import unittest

import numpy as np
from sklearn.linear_model import SGDClassifier

from model_pipeline import build_matrix, create_vectorizers


class HybridPipelineTests(unittest.TestCase):
    def test_combines_numeric_features_and_hostname_ngrams(self):
        urls = [
            "https://www.google.com",
            "https://github.com",
            "https://microsoft.com",
            "https://paypal.com",
            "http://paypal-secure-login.xyz/verify",
            "http://account-verify.example.xyz/login?session=123",
            "http://192.0.2.10/login",
            "https://secure-billing.example.net/update",
        ]
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int8)
        numeric_vectorizer, scaler, domain_vectorizer, path_vectorizer = create_vectorizers()
        matrix, rows = build_matrix(
            urls,
            numeric_vectorizer,
            scaler,
            domain_vectorizer,
            path_vectorizer,
            fit_numeric=True,
        )
        self.assertEqual(matrix.shape[0], len(urls))
        self.assertGreater(matrix.shape[1], len(rows[0]))
        self.assertTrue(np.isfinite(matrix.data).all())

        classifier = SGDClassifier(
            loss="log_loss", max_iter=3, tol=1e-3, random_state=7, average=True
        )
        classifier.fit(matrix, y)
        probabilities = classifier.predict_proba(matrix)
        self.assertEqual(probabilities.shape, (len(urls), 2))
        self.assertTrue(np.isfinite(probabilities).all())


if __name__ == "__main__":
    unittest.main()
