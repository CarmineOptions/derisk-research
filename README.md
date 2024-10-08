# DeRisk Starknet

Monorepo with components required for the implementation of DeRisk on Starknet.

## Contributor guidelines

See [our contributor guidelines](https://github.com/CarmineOptions/derisk-research/blob/master/CONTRIBUTING.md).

## Install project
For setting up the project, run the following command:

```
make setup
```
It will install all dependencies, activate the virtual environment, and set up the pre-commit hooks.

## Start Jupyter notebook

Command to start Jupyter notebook is in the `makefile`, simply run:

```
make notebook
```

## Start Streamlit app

If you have all requirements installed, just run:

```
make app
```

## Update data

The Streamlit app runs a process for updating all necessary data shown on the frontend in the background. The process saves the outputs to a GCP storage from which the Streamlit app loads and visualizes the outputs. To run the data-updating process manually, without running the Streamlit app, use the following command:

```
python3 update_data.py
```
