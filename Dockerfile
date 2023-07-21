# Build project
FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY mock_app.py histogram.py ETH-USDC.csv ETH-USDT.csv ETH-DAI.csv wBTC-USDC.csv wBTC-USDT.csv wBTC-DAI.csv histogram.csv large_loans_sample.csv small_loans_sample.csv ./

CMD ["streamlit", "run", "./mock_app.py"]
