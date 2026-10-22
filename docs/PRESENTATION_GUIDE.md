# Presentation Guide

## Suggested live demonstration

1. Explain that the project is an educational phishing URL detector using a local machine learning model.
2. Show the architecture: labeled URL data, feature extraction, model training, Flask API, and web or extension interface.
3. Open the web page or the PhishGuard extension.
4. Confirm the backend is ready using `http://127.0.0.1:5000/health`.
5. Analyze a familiar legitimate URL and a deliberately suspicious-looking test URL. Describe the outputs as model predictions, not verified safety verdicts.
6. Show the domain findings and URL structure findings separately.
7. Present the actual accuracy, precision, recall, F1 score, false positive rate, and confusion matrix produced by your full local training run.
8. Explain the key limitations and what future work could add, such as authorized live reputation checks or more robust temporal evaluation.

## Questions you should be ready to answer

**Why not use only URL length and special characters?**

Those features are coarse. PhishGuard also uses hostname parsing, domain and suffix structure, selected suspicious patterns, and character n-grams from the hostname and URL path/query.

**Does the score prove a site is dangerous?**

No. It is a score from the trained classifier. It is not a live blacklist result, and it is not guaranteed to be calibrated to real-world risk.

**Does it scan website contents?**

No. It analyzes the URL string. It does not inspect the site's HTML, scripts, redirects, downloads, DNS records, or domain registration history.

**Does the extension block phishing?**

No. The current extension is a manual checker. It displays a warning or result after a user invokes the popup; it does not automatically block navigation.

**Why split by domain for evaluation?**

A random URL split can put different URLs from the same domain in training and testing. Grouping by registered domain provides a harder and more informative test of performance on unseen domains.

**Why can false positives still happen?**

The model depends on dataset labels and coverage, while legitimate and malicious URL patterns often overlap. Domain reputation and page behavior are not checked by the offline model.

## Academic reporting reminder

Only report metrics printed by the actual full training run for the dataset version used in your presentation. Label limitations honestly and cite the dataset source once verified.
