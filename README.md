### Connect to the VM

Ask the admin to add your `ssh` public key and get your `NAME` and `VM_IP_ADDRESS`. Then run:

```
ssh [NAME]@[VM_IP_ADDRESS]
```

### Install dependencies

Python dependencies are listed in the `requirements.txt` file, install them with this command:

```
pip install -r requirements.txt
```

### Start Jupyter notebook

Command to start Jupyter notebook is in the `makefile`, simply run:

```
make notebook
```

### Start Streamlit app

If you have all requirements installed, just run:

```
make app
```

### Update Persistent State

*Streamlit* uses state stored in a *pickle* file to speed up initial loading process. The pickle file is stored in a GCP bucket, to create new persistent state file and upload it to the GCP bucket, run the following command:

```
python3 persistent_state.py N
```

Where `N` is the block number that the state should be stored up to. Check the current latest block on [Starkscan/blocks](https://starkscan.co/blocks) and make sure not to use `N` higher than the last block!
