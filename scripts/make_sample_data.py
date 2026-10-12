"""Write data/sample_data/: a small, real slice of OULAD in the original seven-table format.

A fixed number of students is drawn (seed 42) from every module presentation, and every row that belongs to them is kept
in the four student tables; the three reference tables (courses, assessments, vle) are copied whole. The pipeline runs on
it unchanged (`SSA_RAW_DIR=data/sample_data`), which makes it a quick end-to-end check of a fresh install. It is far too
small for the reported metrics, which come from the full dataset.

    python scripts/make_sample_data.py --per-presentation 40
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = ["code_module", "code_presentation", "id_student"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--out", default=str(ROOT / "data" / "sample_data"))
    ap.add_argument("--per-presentation", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    info = pd.read_csv(raw / "studentInfo.csv")
    smallest = int(info.groupby(["code_module", "code_presentation"]).size().min())
    picked = info.groupby(["code_module", "code_presentation"]).sample(n=min(a.per_presentation, smallest), random_state=a.seed)
    keys = picked[KEY]
    students = set(picked["id_student"])
    picked.to_csv(out / "studentInfo.csv", index=False)
    pd.read_csv(raw / "studentRegistration.csv").merge(keys, on=KEY).to_csv(out / "studentRegistration.csv", index=False)

    assessments = pd.read_csv(raw / "assessments.csv")
    sa = pd.read_csv(raw / "studentAssessment.csv")
    sa = sa.merge(assessments[["id_assessment", "code_module", "code_presentation"]], on="id_assessment").merge(keys, on=KEY)
    sa[["id_assessment", "id_student", "date_submitted", "is_banked", "score"]].to_csv(out / "studentAssessment.csv", index=False)

    chunks = []
    for c in pd.read_csv(raw / "studentVle.csv", chunksize=1_000_000):
        c = c[c["id_student"].isin(students)]
        chunks.append(c.merge(keys, on=KEY))
    pd.concat(chunks).to_csv(out / "studentVle.csv", index=False)

    for name in ("courses.csv", "assessments.csv", "vle.csv"):
        pd.read_csv(raw / name).to_csv(out / name, index=False)
    sizes = {p.name: f"{sum(1 for _ in open(p, encoding='utf-8')) - 1:,} rows" for p in sorted(out.glob("*.csv"))}
    print(f"{len(picked):,} enrolments from {picked.groupby(['code_module', 'code_presentation']).ngroups} presentations")
    for k, v in sizes.items():
        print(f"  {k:28s} {v}")


if __name__ == "__main__":
    main()
