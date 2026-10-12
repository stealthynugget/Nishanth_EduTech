# Data

| Folder | Contents | In git |
|---|---|---|
| `sample_data/` | A real slice of OULAD in the original seven-table format (fixed students from every module presentation, all their rows; reference tables complete). Made by `scripts/make_sample_data.py`. | yes |
| `raw/` | The full OULAD CSV files: `assessments.csv, courses.csv, studentAssessment.csv, studentInfo.csv, studentRegistration.csv, studentVle.csv, vle.csv` | no |
| `processed/` | Features and weekly activity written by `python -m src.cli prepare` | no |

Download the full dataset from <https://analyse.kmi.open.ac.uk/open_dataset> (Kuzilek, Hlosta and Zdrahal 2017,
*Scientific Data* 4:170171, CC BY 4.0) and place the seven CSV files in `data/raw/`.

Run the whole pipeline on the sample instead (about a minute):

```bash
SSA_HOME=.sample SSA_RAW_DIR=data/sample_data python -m src.cli build --no-dense
```

`python -m src.cli demo-data` writes a synthetic fixture instead (used by the tests); the quality gate then marks results
as non-official. Field descriptions and preprocessing: `docs/Dataset_Details.pdf`.
