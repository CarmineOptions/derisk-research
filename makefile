notebook:
	cd apps/legacy_app && /bin/python3 -m notebook --ip=0.0.0.0

app:
	cd apps/legacy_app && streamlit run app.py

setup:
	cd apps/legacy_app && ./setup.sh

test_data_handler:
	pytest apps/data_handler

test_shared:
	pytest apps/shared

test_dashboard_app:
	cd apps/dashboard_app && poetry run pytest
