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
make
```
