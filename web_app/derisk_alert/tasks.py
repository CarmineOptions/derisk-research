from .celery_conf import app


@app.task(name="check_data_changes")
def check_data_changes():
    # TODO Add checking data changes logic
    return "Checking data changes..."
