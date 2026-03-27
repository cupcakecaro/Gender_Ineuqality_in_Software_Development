# AGENTS.md

## Project Overview

Master's thesis studying gender inequality in software development — specifically career progression of women in traditional vs. low-code/no-code (LCNC) roles, compared across Sweden, Romania, and Germany using the European Gender Equality Index.

## Commands

- Install dependency: `uv add <package>`
- Run a script: `uv run <path/to/script.py>`
- Credentials: stored in `.env` (never commit this file)

## Repository Layout

```
data/raw/raw_profiles.csv       # Source data (profile_id, country, experience)
data/processed/                 # Cleaned and classified outputs
src/experience_parser.py        # Parses raw experience text into structured records
src/analysis/classify_jobs_*.py # LLM/rules-based job classifiers
src/preprocessing/clean_raw.py  # Raw data cleaning
Prompts/                        # Prompt templates for classification tasks
notebooks/                      # Exploratory analysis notebooks
Masterthesis/                   # LaTeX thesis source
```

## Data Rules

- Raw data is in `data/raw/raw_profiles.csv` with columns: `profile_id`, `country`, `experience`
- Data was manually collected — never suggest automating LinkedIn scraping, login, or any bypass of platform protections
- Do not collect or store personal identifiers; follow GDPR principles
- New processed outputs go in `data/processed/`

## Classification Guidelines

- Prefer LLM-based classification using structured prompts (see `Prompts/`)
- Always validate on a labeled sample before running on the full dataset; report accuracy, precision, and recall
- Use `data/labelled/` for ground-truth examples
- Prompt templates must be version-controlled and reproducible
- Prefer transparent methods over complex black-box approaches

## Theoretical Frame

When suggesting analyses or interpreting results, reason within this framework:
- **Glass ceiling / gender inequality theory** — barriers to women's advancement
- **Occupational segregation** — horizontal and vertical segregation by role type
- **Institutional theory** — country-level gender norms moderate individual outcomes
- **Career trajectory modeling** — time-to-promotion, seniority transitions

Country benchmarks use the EIGE Gender Equality Index (Sweden = high, Romania = lower, Germany = baseline).

## Code Standards

- Write reproducible, well-documented Python
- Prefer methodological rigor and clarity over engineering complexity
- Add docstrings to all functions
- Do not introduce unnecessary dependencies
