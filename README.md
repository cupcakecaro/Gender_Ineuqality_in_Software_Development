# Gender_Ineuqality_in_Software_Development

Master thesis: The Role of Gender Equality Contexts in Women's Tech Careers: A Quantitative Cross-Country Comparison of Low-Code/No-Code and Traditional Development Roles.

## Setup
1. Create .env file by copying .env.example (`cp .env.example .env`)
2. Fill in the value for GEMINI_API_KEY with your API key (you can typicaly get one by visiting [aistudio.google.com](https://aistudio.google.com) and then clicking *Get API key* in the bottom left)

## Main Entry Point

The canonical workflow is the notebook in notebooks/pipeline.ipynb. This notebook runs the end-to-end LLM-based parsing, classification, and analysis pipeline used in the thesis.

## Repository Structure

- notebooks/pipeline.ipynb: main, LLM-based pipeline (use this)
- src/utils.py: shared utilities used by the notebook
- src/legacy/: legacy rule-based parser and preprocessing (not used by the current workflow)

## Legacy Rule-Based Parser

The legacy rule-based parser remains available for reference and validation only. It is not used by the main pipeline.

- src/legacy/run_parser.py: legacy CLI entry point
- src/legacy/parsing/experience_parser.py: rule-based segmentation and field extraction
- src/legacy/preprocessing/clean_raw.py: legacy text cleanup helpers