# Build project
FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./data ./data
COPY ./hashstack_data ./hashstack_data
COPY ./src ./src
COPY app.py .
COPY update_data.py .

CMD ["streamlit", "run", "app.py"]
