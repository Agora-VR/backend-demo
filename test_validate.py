from time import sleep

import requests

response = requests.post(
    "http://localhost:8080/authenticate",
    json={"user_name": "tadmozeltov", "user_pass": "pudding"})

token = response.text

# print(token)

user_response = requests.get(
    "http://localhost:8080/user/tadmozeltov",
    headers={"Authorization": f"Bearer {token}"}
)

if user_response.ok:
    print(user_response.json())
else:
    print(user_response.text)

sleep(8)

second_response = requests.get(
    "http://localhost:8080/user/tadmozeltov",
    headers={"Authorization": f"Bearer {token}"}
)

if second_response.ok:
    print(second_response.json())
else:
    print(second_response.text)