import datetime as dt
import json
import os
import requests
import subprocess
import yaml


def process_endpoint_block(
    endpoint_config, interval_start, interval_end, metrics_token
):
    metrics = {}

    for metric_name, query in config["queries"].items():
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

    requests.post(
        url=config["endpoint"],
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
    with open("/opt/config.yaml") as f:
        config = yaml.safe_load(f)

    metrics_token = os.environ.get("METRICS_WEBHOOK_TOKEN")
    one_hour_ago = dt.datetime.now() - dt.timedelta(hours=1)
    interval_start = one_hour_ago.strftime("%Y-%m-%dT%H:00:00Z")
    interval_end = one_hour_ago.strftime("%Y-%m-%dT%H:59:59Z")

    process_endpoint_block(config, interval_start, interval_end, metrics_token)
