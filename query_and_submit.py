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
    interval_start: str = ""
    interval_end: str = ""
    interval_end_excl: str = ""
    metrics_token: str = os.environ.get("METRICS_WEBHOOK_TOKEN")

    def __post_init__(self):
        now = dt.datetime.now()
        one_hour_ago = now - dt.timedelta(hours=1)
        self.interval_start = one_hour_ago.strftime("%Y-%m-%dT%H:00:00Z")
        self.interval_end = one_hour_ago.strftime("%Y-%m-%dT%H:59:59Z")
        self.interval_end_excl = now.strftime("%Y-%m-%dT%H:00:00Z")


def load_endpoints(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def process_endpoints(endpoints, config):
    for endpoint in endpoints:
        process_endpoint(endpoint, config)


def process_endpoint(endpoint, config):
    query_function = QUERY_FUNCTIONS_BY_TYPE[endpoint["type"]]
    data = query_function(endpoint, config)
    post_data(endpoint["endpoint"], config, data)


def query_metric_counts(endpoint, config):
    metrics = {}

    for metric_name, query in endpoint["queries"].items():
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

    return {
        "startInterval": config.interval_start,
        "endInterval": config.interval_end,
        **metrics,
    }


def query_rows_from_labels(endpoint, config):
    query = endpoint["query"]
    logcli_output = subprocess.check_output(
        [
            "/logcli-linux-amd64",
            "query",
            "--quiet",
            "--output=jsonl",
            "--limit=500000",
            "--from",
            config.interval_start,
            "--to",
            config.interval_end_excl,
            f'{query} | line_format ""',
        ]
    )

    intervals = {
        "startInterval": config.interval_start,
        "endInterval": config.interval_end,
    }
    label_mapping = endpoint["labelMapping"]
    timestamp_mapping = endpoint.get("timestampMapping")

    data = []
    for line in logcli_output.decode("utf-8").strip().split("\n"):
        row = json.loads(line)
        timestamp = {timestamp_mapping: row["timestamp"]} if timestamp_mapping else {}
        data.append(
            {
                **{
                    label_mapping[label]: value
                    for label, value in row["labels"].items()
                    if label in label_mapping
                },
                **timestamp,
                **intervals,
            }
        )

    return data


QUERY_FUNCTIONS_BY_TYPE = {
    "metricCounts": query_metric_counts,
    "rowsFromLabels": query_rows_from_labels,
}


def post_data(endpoint, config, data):
    response = requests.post(
        url=endpoint,
        json=data,
        headers={
            "xc-token": config.metrics_token,
        },
    )
    response.raise_for_status()


if __name__ == "__main__":
    config = Config()
    endpoints = load_endpoints("/opt/config.yaml")
    process_endpoints(endpoints, config)
