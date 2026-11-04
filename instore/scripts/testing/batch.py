import argparse
import csv
import json
import os
import subprocess
import sys
import time
import uuid
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


def send_requests(env, category, wait_interval, prompts):
    with open(f"{category}_results.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["env", "prompt", "summary", "commands", "tool_calls", "time_taken", "timestamp"])

        i = 0
        retry = 0
        while i < len(prompts["prompts"]):
            prompt = prompts["prompts"][i]
            parts = prompt.split(" :")
            simulated_time = parts[0]
            prompt = parts[1]
            data = json.dumps({"expression": prompt, "id": str(uuid.uuid4())})
            start = time.time()
            print(f"{start}: Sending prompt: {prompt}")
            res = requests.post(
                url="http://0.0.0.0:5001/intent",
                data=data,
                headers={
                    "Content-Type": "application/json",
                },
                timeout=600,
            )
            print(res)
            end = time.time()
            try:
                if res.status_code == 429:
                    print("----Quota----")
                    return
                res.raise_for_status()
                response = res.json()

                writer.writerow(
                    [
                        env,
                        prompt,
                        response["reply"],
                        response["cmds"],
                        response["tool_calls"],
                        f"{end - start}",
                        f"{simulated_time}",
                    ]
                )
            except requests.exceptions.HTTPError as e:

                if retry < 3:
                    retry = retry + 1
                    continue
                else:

                    retry = 0
                    writer.writerow(
                        [
                            env,
                            prompt,
                            e,
                            [],
                            [],
                            f"{end - start}",
                            f"{simulated_time}",
                        ]
                    )
                    print(e)
            if int(wait_interval) > 0:
                print(f"waiting for {wait_interval}")
                time.sleep(int(wait_interval))  # Prevents going over usage limits (e.g., gemini)

            i = i + 1


def run_isolated_experiment(compose: str, category: str, wait: str, env: str, prompt_file_name):
    res = subprocess.run(f"docker compose -f {compose} down -v", shell=True)
    if res.returncode != 0:
        print(f"an error has occured: {res.stderr}")
        sys.exit(1)
    res = subprocess.run(
        f"ANALYTICS_ENV={env} docker compose -f {compose} up --force-recreate --build intent_manager -d",
        shell=True,
    )
    if res.returncode != 0:
        print(f"an error has occured: {res.stderr}")
        sys.exit(1)

    time.sleep(30)  # Ensure containers are running

    prompts = load_prompts(category + "/" + prompt_file_name)
    send_requests(env, category, wait, prompts)
    subprocess.run(f"docker compose -f {compose} down -v", shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="InStorage Tester")
    parser.add_argument("category")
    parser.add_argument("-w", "--wait", required=True)
    parser.add_argument("-c", "--compose", required=True)
    args = parser.parse_args()
    env_files = list(os.listdir("./environments"))
    for env in ["env1.json", "env3.json"]:  #  Edit here if needed
        if args.category == "optimization":
            prompt_files = list(os.listdir("./optimization"))
            for prompt_file in prompt_files:
                run_isolated_experiment(args.compose, args.category, args.wait, env, prompt_file)
        else:
            run_isolated_experiment(args.compose, args.category, args.wait, env, "/prompts.json")
