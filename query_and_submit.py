import datetime as dt
import json
import os
import requests
import subprocess
import yaml


def load_config(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def process_endpoint_block(
    endpoint_config, interval_start, interval_end, metrics_token
):
    metrics = query_metrics(endpoint_config["queries"], interval_start, interval_end)
    post_metrics(endpoint_config["endpoint"], interval_start, interval_end, metrics)


def query_metrics(query_config, interval_start, interval_end):
    metrics = {}

    for metric_name, query in query_config.items():
        output = json.loads(
            subprocess.check_output(
                [
                    "/logcli-linux-amd64",
                    "instant-query",
                    "--now",
                    interval_end,
                    f"sum(count_over_time({query} [1h]))",
                ]
            )
        )
        metrics[metric_name] = output[0]["value"][1] if output else 0

    return metrics


def post_metrics(endpoint, interval_start, interval_end, metrics):
    requests.post(
        url=endpoint,
        json={
            "startInterval": interval_start,
            "endInterval": interval_end,
            **metrics,
        },
        headers={
            "xc-token": metrics_token,
        },
    )


if __name__ == "__main__":
    config = load_config("/opt/config.yaml")
    metrics_token = os.environ.get("METRICS_WEBHOOK_TOKEN")
    one_hour_ago = dt.datetime.now() - dt.timedelta(hours=1)
    interval_start = one_hour_ago.strftime("%Y-%m-%dT%H:00:00Z")
    interval_end = one_hour_ago.strftime("%Y-%m-%dT%H:59:59Z")

    process_endpoint_block(config, interval_start, interval_end, metrics_token)
