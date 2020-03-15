from json import dumps

import requests

url = "http://localhost:8080/store2"

files = {
    "metadata": (None, dumps({"session_id": 2, "type": "session_audio"}), "application/json"),
    "file": ("wheres_my_juul.ogg", open("wheres_my_juul.ogg", "rb"), "audio/ogg"),
}

response = requests.post(url, files=files)

print(response.text)