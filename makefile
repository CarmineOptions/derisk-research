notebook:
	/bin/python3 -m notebook --ip=0.0.0.0

app:
	streamlit run webapp.py

mock_app:
	streamlit run mock_app.py