FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./data ./data
COPY ./hashstack_data ./hashstack_data
COPY ./nostra_data ./nostra_data
COPY comparison_stats.csv .
COPY ./src ./src
COPY app.py .
COPY update_data.py .

CMD ["streamlit", "run", "app.py"]
