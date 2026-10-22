# Contributing

Thank you for your interest in improving PhishGuard.

## Before proposing changes

- Run the test suite with `python -m unittest discover -v`.
- Keep training and inference feature extraction consistent.
- Do not claim performance improvements without evaluating on held-out domains and reporting actual metrics.
- Add tests for URL parsing, domain edge cases, API handling, and extension behavior when relevant.
- Do not commit `.venv/`, secrets, generated model files, or the dataset until its provenance and redistribution rights have been verified.
- Keep browser extension permissions minimal and document any permission changes.

## Scope

This repository is an educational prototype. Changes should not describe the application as a guaranteed malware scanner, live reputation service, or automatic phishing blocker unless those capabilities are actually implemented and tested.
