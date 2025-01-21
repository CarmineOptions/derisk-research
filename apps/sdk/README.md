# How to install project

1. In `sdk` folder run next commands:
   - Add environment: `python -m venv .venv`
   - Activate environment: `source .venv/bin/activate`
   - Install requirements: `poetry install`
   - Activate poetry shell: `poetry shell`

2. In `sdk` folder run next commands to run the project:
   - Run the project: `poetry run uvicorn main:app --reload`
    