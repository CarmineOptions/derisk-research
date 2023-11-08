FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./data ./data
COPY ./hashstack_data ./hashstack_data
COPY ./nostra_data ./nostra_data
COPY ./nostra_uncapped_data ./nostra_uncapped_data
COPY general_stats.csv .
COPY supply_stats.csv .
COPY collateral_stats.csv .
COPY debt_stats.csv .
COPY utilization_stats.csv .
COPY ./src ./src
COPY app.py .
COPY update_data.py .

CMD ["streamlit", "run", "app.py"]
