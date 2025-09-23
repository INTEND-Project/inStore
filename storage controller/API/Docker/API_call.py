import json
import requests



url_upstream = 'http://192.168.88.129:30500/LoadData'

upstream_data = {
    "partition_id":"0",
    "action": "delete",
    "filename": "minio-dev.yaml" ,
    "source": "demo",
    "destination": "demo",
    "scheduled_time":"2024-09-04 10:50:52.433000-0800"
}

response_upstream = requests.post(url_upstream, headers={'Content-Type': 'application/json'}, data=json.dumps(upstream_data))

print(response_upstream.content)
