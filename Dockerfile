FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./src ./src
COPY app.py .
COPY update_data.py .

CMD ["streamlit", "run", "app.py"]
