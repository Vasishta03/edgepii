# Manuscript status

`ieee/main.tex` is an IEEE conference-style research draft generated from the completed three-seed pilots, reduced scaling study, validation-locked privacy evaluation and measured resource profiles. Author/institution fields remain placeholders, so it is not submission-ready.

Run `python3 scripts/paper_tables.py` from the repository root to update tables from completed result JSON files. Do not enter invented values manually. Run `scripts/summarize.py` in the project environment for measured CSV/Markdown summaries and figures.

Before submission: replace author/institution placeholders, confirm venue formatting and expand the bibliography if required. The draft explicitly states the reduced CPU matrix, retained-subset CAPID evaluation, approximate near-duplicate audit, absent QA utility measurement, and infeasible 5% leakage target.

Compilation status: system `pdflatex` succeeded in two passes on 2026-10-29. All three final rendered pages were inspected after tightening float spacing; no content is clipped and the bibliography remains on page three. The built-in editor compiler timed out without diagnostics, so the verified PDF is the local `ieee/main.pdf`.
