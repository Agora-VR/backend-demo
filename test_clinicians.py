from time import sleep

import requests

response = requests.post(
    "http://localhost:8080/authenticate",
    # json={"user_name": "clin123", "user_pass": "password123"})
    json={"user_name": "tadmozeltov", "user_pass": "pudding"})

token = response.text

user_response = requests.get(
    "http://localhost:8080/user/clinicians",
    headers={"Authorization": f"Bearer {token}"}
)

if user_response.ok:
    print(user_response.json())
else:
    print(user_response.text)


