"""Verify the safe aggregate release without requiring restricted row-level data."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES = {
    "results/figures/final_figure1_original.jpg":
        "e998390838411c3c2e0441a4d3b94c4bc3918a7779c2d84959796162965a7541",
    "results/figures/final_figure2_original.jpg":
        "46f8e320fc4145c21fc6dd519ecd2ea79e0fd2b053cb5e6a1ff76c65f9d83ddc",
}
REQUIRED = [
    "README.md",
    "PUBLIC_RELEASE_AUDIT.md",
    "Handoff.md",
    "CITATION.cff",
    "LICENSE",
    "requirements.txt",
    "data/README.md",
    "paper/Resource_Shock_Story_MIT_Sloan_Revised.docx",
    "paper/Resource_Shock_Story_MIT_Sloan_Revised.pdf",
    "results/tables/main_results_table.csv",
    "assets/RupayanHalder.jpeg",
    "assets/SoccerSolverLogo.png",
]
HEADLINE_TOKENS = [
    "1.81 [1.44, 2.57]",
    "0.57 [0.38, 0.70]",
    "-1.27 [-1.87, -0.93]",
    "78.38 [51.95, 141.63]",
    "39.36 [19.58, 70.39]",
    "107.13 [62.58, 179.64]",
    "rank-biserial r=0.76, Mann-Whitney p=0.019",
    "2.62 [2.29, 3.04]",
    "1.36 [1.24, 1.77]",
    "rank-biserial r=-0.82, Mann-Whitney p=0.006",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    failures: list[str] = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            failures.append(f"required normal file missing: {relative}")

    figure_files = sorted(p for p in (ROOT / "results/figures").iterdir() if p.is_file())
    if [p.relative_to(ROOT).as_posix() for p in figure_files] != sorted(FIGURES):
        failures.append("results/figures must contain exactly the two locked figures")
    for relative, expected in FIGURES.items():
        path = ROOT / relative
        if path.is_file() and sha256(path) != expected:
            failures.append(f"locked figure hash mismatch: {relative}")

    aggregate = (ROOT / "results/tables/main_results_table.csv").read_text(encoding="utf-8")
    for token in HEADLINE_TOKENS:
        if token not in aggregate:
            failures.append(f"headline aggregate token missing: {token}")

    for path in ROOT.rglob("*"):
        if path.is_symlink():
            failures.append(f"symlink present: {path.relative_to(ROOT)}")

    if failures:
        print("RELEASE VERIFICATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("RELEASE VERIFICATION: PASS")
    print("Locked figures: 2/2 exact")
    print("Headline aggregate checks: 10/10")
    print("Required files and assets: present")
    print("Symlinks: none")
    print("Reproducibility status: conditional on authorized row-level data access")


if __name__ == "__main__":
    main()
