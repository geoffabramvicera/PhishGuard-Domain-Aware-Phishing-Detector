# Training dataset instructions

The application can make predictions only after a compatible `phishing_model.pkl` has been trained or otherwise obtained from a trusted source. To train this project, place the authorized `phishing_dataset.csv` file in the project root.

Required columns:

- `url`: URL string
- `label`: `legitimate` or `phishing`

The raw CSV is excluded from Git by default because the original project's copy did not document its origin or redistribution terms. Before committing the file to a public repository, verify the source license and required attribution. See [Dataset and evaluation](docs/DATASET_AND_EVALUATION.md).
