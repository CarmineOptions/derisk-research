# Build project
FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# persistent state is downloaded from GCP bucket
RUN wget https://storage.cloud.google.com/derisk-persistent-state/persistent-state.pckl

CMD ["streamlit", "run", "./webapp.py"]
