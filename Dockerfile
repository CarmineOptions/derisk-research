# Build project
FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# download correct persistent-state
RUN export LATEST_BLOCK=$(cat /app/persistent-state-keeper.txt) \
    && export DOWNLOAD_URL="https://storage.cloud.google.com/derisk-persistent-state/persistent-state-$LATEST_BLOCK.pckl" \
    && wget $DOWNLOAD_URL

CMD ["streamlit", "run", "./webapp.py"]
