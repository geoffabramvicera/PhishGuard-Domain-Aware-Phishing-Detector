# Local API Reference

Base URL: `http://127.0.0.1:5000`

The API is intended for local development. It is not configured as a public production service.

## `GET /health`

Checks whether the trained model bundle was loaded when the Flask process started.

Example response when ready:

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_version": 3,
  "model_name": "Hybrid domain and URL character n-gram classifier",
  "error": null
}
```

When the model is missing or incompatible, the endpoint returns HTTP `503` and `model_loaded` is false. Retrain with the current `train_model.py` and restart `app.py`.

## `POST /predict`

Request content type: `application/json`

Example request:

```json
{
  "url": "https://example.com/login"
}
```

The response contains fields such as:

| Field | Meaning |
|---|---|
| `url` | URL string submitted for analysis. |
| `is_phishing` | Final application flag after the narrow homepage/context handling. |
| `model_is_phishing` | Raw classifier's binary prediction before contextual handling. |
| `phishing_score` | Model's score for the phishing class, expressed from 0 to 100. |
| `prediction_confidence` | Model probability assigned to the predicted class, expressed from 0 to 100. |
| `result_label` | Human-readable result category. |
| `decision_source` | Indicates which decision path produced the result. |
| `recognized_homepage` | True only for an exact homepage match from the configured list. |
| `review_required` | Indicates a mixed-signal situation requiring manual review. |
| `domain_analysis` | Hostname, registered domain, public suffix, and domain indicators. |
| `url_analysis` | URL path and query observations. |
| `explanation` | Short explanation of the prediction and its limitations. |
| `limitation` | General limitation statement returned by the API. |

The actual response contains additional feature data; the list above describes the fields most relevant to consumers.

## Error responses

Typical HTTP codes:

- `400 Bad Request`: request body is not JSON, a URL is missing, or URL validation fails.
- `503 Service Unavailable`: model bundle is missing or incompatible.
- `500 Internal Server Error`: unexpected prediction error. Details are logged in the backend console.

Example invalid request:

```json
{
  "error": "Send a JSON object containing a 'url' field."
}
```

## Test with PowerShell

With the backend running, check health:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Submit a URL:

```powershell
$body = @{ url = 'https://github.com' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/predict' -Method Post -ContentType 'application/json' -Body $body
```

Do not interpret the score as a verified probability of real-world maliciousness. It is the model score learned from the training data.
