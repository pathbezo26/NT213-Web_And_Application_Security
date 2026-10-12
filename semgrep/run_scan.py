"""Quet Semgrep tren testcases_php/ va cham TP/FP/FN/TN (Exp.1).

Nhan chuan lay theo THU MUC:
    testcases_php/vulnerable/  -> rule PHAI bao (expected = vulnerable)
    testcases_php/safe/        -> rule KHONG duoc bao (expected = safe)

Dau ra (schema RIENG cho Semgrep, KHONG co confidence):
    semgrep/results/exp1_semgrep_<version>.csv
        file, line, rule_id, matched, true_label, outcome

Chay (tu thu muc goc du an):
    python semgrep/run_scan.py --version v0
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = HERE / "rules"
CASES = HERE / "testcases_php"
OUT = HERE / "results"


def run_semgrep():
    cmd = ["semgrep", "--config", str(RULES), "--json", "--metrics=off",
           "--quiet", str(CASES)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        sys.exit(f"Semgrep loi (exit {proc.returncode}):\n{proc.stderr}")
    flagged = {}  # ten file -> (dong dau tien, rule_id)
    for r in json.loads(proc.stdout)["results"]:
        name = Path(r["path"]).name
        flagged.setdefault(name, (r["start"]["line"], r["check_id"].split(".")[-1]))
    return flagged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v0")
    args = ap.parse_args()

    flagged = run_semgrep()
    rows, c = [], {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for label, folder in (("vulnerable", CASES / "vulnerable"),
                          ("safe", CASES / "safe")):
        for php in sorted(folder.glob("*.php")):
            hit = php.name in flagged
            line, rule = flagged.get(php.name, (0, "-"))
            outcome = {("vulnerable", True): "TP", ("vulnerable", False): "FN",
                       ("safe", True): "FP", ("safe", False): "TN"}[(label, hit)]
            c[outcome] += 1
            rows.append([php.name, line, rule, int(hit), label, outcome])

    OUT.mkdir(exist_ok=True)
    out = OUT / f"exp1_semgrep_{args.version}.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "line", "rule_id", "matched", "true_label", "outcome"])
        w.writerows(rows)

    print(f"{'file':42}{'nhan':12}ket qua")
    for r in rows:
        print(f"{r[0]:42}{r[4]:12}{r[5]}")
    tp, fp, fn, tn = c["TP"], c["FP"], c["FN"], c["TN"]
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    print(f"\nTP={tp} FP={fp} FN={fn} TN={tn} | Precision={prec:.2f} Recall={rec:.2f}")
    print(f"Da ghi: {out.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
