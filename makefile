notebook:
	/bin/python3 -m notebook --ip=0.0.0.0

app:
	streamlit run webapp.py

vis_app:
	streamlit run visualisation_app.py
