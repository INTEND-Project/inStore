import csv
import json
import time
from sys import argv

import requests

"""

def get_container_stats(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    stats = container.stats(stream=False)
    return stats


def monitor_resource_usage(container_name, interval, event, file_name):
    start_time = time.time()
    while not event.is_set():
        with open("resources.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            stats = get_container_stats(container_name)
            print(f"Resource usage at {time.time() - start_time:.2f} seconds: {stats}")
            writer.writerow([time.time(), stats[""]])
            time.sleep(interval)
"""


def load_prompts(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


def send_requests(prompts):
    with open("results.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["prompt", "summary", "commands", "tool_calls", "time_taken", "timestamp"])

        for prompt in prompts["prompts"]:
            data = json.dumps({"expression": prompt})
            start = time.time()
            print(f"{start}: Sending prompt: {prompt}")
            res = requests.post(
                url="http://0.0.0.0:5001/intent",
                data=data,
                headers={
                    "Content-Type": "application/json",
                },
            )
            end = time.time()
            response = res.json()
            writer.writerow(
                [prompt, response["reply"], response["cmds"], response["tool_calls"], f"{end - start}", f"{start}"]
            )
            time.sleep(60.0)  # Prevents going over usage limits (e.g., gemini)


if __name__ == "__main__":
    prompts = load_prompts(argv[1])
    send_requests(prompts)
