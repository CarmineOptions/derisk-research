# DeRisk Starknet

Monorepo with components required for the implementation of DeRisk on Starknet.

## Contributor guidelines

See [our contributor guidelines](https://github.com/CarmineOptions/derisk-research/blob/master/CONTRIBUTING.md).

## Install dependencies

Python dependencies are managed with `poetry`, install them with this command:

```
poetry install
```

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
