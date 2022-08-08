import datetime as dt
import json
import os
from typing import Any, List
import requests
import subprocess
import yaml
from dataclasses import dataclass


@dataclass
class Config:
    interval_start: str = ''
    interval_end: str = ''
    metrics_token: str = os.environ.get("METRICS_WEBHOOK_TOKEN")

    def __post_init__(self):
        one_hour_ago = dt.datetime.now() - dt.timedelta(hours=1)
        self.interval_start = one_hour_ago.strftime("%Y-%m-%dT%H:00:00Z")
        self.interval_end = one_hour_ago.strftime("%Y-%m-%dT%H:59:59Z")


def load_endpoint(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def process_endpoint(endpoint, config):
    metrics = query_metrics(endpoint["queries"], config)
    post_metrics(endpoint["endpoint"], config, metrics)


def query_metrics(queries, config):
    metrics = {}

    for metric_name, query in queries.items():
        output = json.loads(
            subprocess.check_output(
                [
                    "/logcli-linux-amd64",
                    "instant-query",
                    "--now",
                    config.interval_end,
                    f"sum(count_over_time({query} [1h]))",
                ]
            )
        )
        metrics[metric_name] = output[0]["value"][1] if output else 0

    return metrics


def post_metrics(endpoint, config, metrics):
    response = requests.post(
        url=endpoint,
        json={
            "startInterval": config.interval_start,
            "endInterval": config.interval_end,
            **metrics,
        },
        headers={
            "xc-token": config.metrics_token,
        },
    )
    response.raise_for_status()


if __name__ == "__main__":
    config = Config()
    endpoint = load_endpoint("/opt/config.yaml")
    process_endpoint(endpoint, config)
