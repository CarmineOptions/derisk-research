notebook:
	/bin/python3 -m notebook --ip=0.0.0.0

app:
	streamlit run app.py

setup:
	./setup.sh