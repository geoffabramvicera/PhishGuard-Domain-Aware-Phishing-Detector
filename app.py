"""Local Flask API for the hybrid domain-aware phishing URL model."""
from pathlib import Path

import joblib
from flask import Flask, jsonify, request
from flask_cors import CORS

from model_pipeline import MODEL_VERSION, build_matrix
from url_features import (
    explain_domain,
    explain_url_structure,
    extract_features,
    known_major_domain,
    recognized_major_homepage,
    validate_url,
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "phishing_model.pkl"

app = Flask(__name__)
CORS(app)
model_bundle = None
model_load_error = None
try:
    loaded = joblib.load(MODEL_PATH)
    if isinstance(loaded, dict) and loaded.get("model_version") == MODEL_VERSION:
        model_bundle = loaded
        print(f"Loaded domain-aware model bundle: {MODEL_PATH}")
    else:
        model_load_error = "The saved model is from an older version. Retrain with train_model.py."
        print(f"WARNING: {model_load_error}")
except FileNotFoundError:
    model_load_error = "phishing_model.pkl is missing. Run train_model.py first."
    print(f"WARNING: {model_load_error}")
except Exception as error:
    model_load_error = f"The model could not be loaded: {error}"
    print(f"WARNING: {model_load_error}")


@app.get("/health")
def health():
    return jsonify(
        status="ok" if model_bundle is not None else "model_missing",
        model_loaded=model_bundle is not None,
        model_version=MODEL_VERSION if model_bundle is not None else None,
        model_name=model_bundle.get("model_name") if model_bundle else None,
        error=model_load_error,
    ), 200 if model_bundle is not None else 503


@app.post("/predict")
def predict():
    if model_bundle is None:
        return jsonify(error=model_load_error or "The model is unavailable. Run train_model.py."), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send a JSON object containing a 'url' field."), 400
    url = data.get("url", "")
    if not isinstance(url, str):
        return jsonify(error="The URL must be text."), 400
    url = url.strip()
    validation_error = validate_url(url)
    if validation_error:
        return jsonify(error=validation_error), 400

    try:
        matrix, _ = build_matrix(
            [url],
            model_bundle["numeric_vectorizer"],
            model_bundle["numeric_scaler"],
            model_bundle["domain_vectorizer"],
            model_bundle["path_vectorizer"],
        )
        classifier = model_bundle["classifier"]
        raw_prediction = int(classifier.predict(matrix)[0])
        probabilities = classifier.predict_proba(matrix)[0]
        classes = list(classifier.classes_)
        phishing_score = float(probabilities[classes.index(1)]) * 100 if 1 in classes else 0.0
        raw_confidence = float(probabilities[classes.index(raw_prediction)]) * 100

        recognized_domain = recognized_major_homepage(url)
        known_domain = known_major_domain(url)
        is_recognized_homepage = recognized_domain is not None
        review_required = bool(known_domain and raw_prediction == 1 and not is_recognized_homepage)
        if is_recognized_homepage:
            final_is_phishing = False
            result_label = "Recognized major-domain homepage"
            decision_source = "recognized_major_domain_homepage"
            explanation = (
                f"This exact HTTPS homepage matches the local recognition list for {recognized_domain}. "
                "The model score remains visible for transparency. This is not a live reputation check "
                "and does not apply to subpages or user-hosted content."
            )
        elif review_required:
            # Do not turn mixed signals into either an automatic safe verdict or a definitive phishing warning.
            # The raw model prediction and score remain visible so the user can review the URL carefully.
            final_is_phishing = False
            result_label = "Known domain, but URL needs review"
            decision_source = "known_domain_model_disagreement"
            explanation = (
                f"The hostname exactly matches {known_domain}, but the model found URL patterns associated with phishing. "
                "This is a mixed signal, not a safe verdict. Check the exact path and page content before interacting. "
                "The local domain list is not a live reputation service."
            )
        else:
            final_is_phishing = raw_prediction == 1
            result_label = "Potential phishing URL" if final_is_phishing else "No phishing indicators detected by the model"
            decision_source = "hybrid_domain_and_url_model"
            explanation = (
                "The classifier combines hostname character patterns, path and query character patterns, and numeric domain and URL structure features. "
                "It does not inspect page content or query live domain reputation."
            )

        score = round(phishing_score, 2)
        return jsonify(
            url=url,
            is_phishing=bool(final_is_phishing),
            model_is_phishing=bool(raw_prediction == 1),
            phishing_score=score,
            confidence=score,  # Legacy name retained for existing frontend compatibility.
            prediction_confidence=round(raw_confidence, 2),
            result_label=result_label,
            decision_source=decision_source,
            recognized_homepage=is_recognized_homepage,
            recognized_domain=recognized_domain,
            known_major_domain=known_domain,
            review_required=review_required,
            explanation=explanation,
            features=extract_features(url),
            domain_analysis=explain_domain(url),
            url_analysis=explain_url_structure(url),
            model_name=model_bundle.get("model_name", "Hybrid domain and URL character n-gram classifier"),
            limitation=(
                "This model estimates patterns from its dataset. It does not verify ownership, "
                "domain age, DNS records, redirects, or live threat reputation. A low score does not guarantee safety."
            ),
        )
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify(error="The model could not analyze this URL. Check the backend console and retrain if the feature schema changed."), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
