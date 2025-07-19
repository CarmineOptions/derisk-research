FROM python:3.11-slim

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"

WORKDIR /app
RUN pip install --no-cache-dir requests python-dotenv

COPY dashboard_app/app/telegram_app/telegram/webhook_simulator.py ./sim.py

CMD ["python", "sim.py"]