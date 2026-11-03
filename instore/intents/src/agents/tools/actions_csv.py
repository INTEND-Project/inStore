import csv

from pkg.interfaces import Action

# The recommendation engine tool writes the actions to this file and the video mover and create_intent tools read them
RECOMMENDATIONS_CSV_PATH = "/root/recommendations.csv"


def write_actions_csv(actions: list[Action], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for a in actions:
            writer.writerow([a.type, a.content_id, a.source, a.destination])


def read_actions_csv(path: str) -> list[Action]:
    with open(path, "r", newline="", encoding="utf-8") as f:
        return [
            Action(type=row[0], content_id=row[1], source=row[2], destination=row[3])
            for row in csv.reader(f)
            if row
        ]
