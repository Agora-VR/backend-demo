from authlib.jose import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from time import sleep

# private_password = input("Enter private key password: ")
private_password = "ButgersBuses"

with open('private.pem', 'rb') as f:
    private_key = load_pem_private_key(
        f.read(), password=private_password.encode(), backend=default_backend())

with open('public.pem', 'rb') as f:
    public_key = f.read()

current_datetime = datetime.utcnow()
expiration_delta = timedelta(seconds=5)

payload = {'iss': 'Project Agora', 'exp': current_datetime + expiration_delta}
header = {'alg': 'RS256'}

s = jwt.encode(header, payload, private_key)

print(s)

claims = jwt.decode(s, public_key)

print(claims, claims.validate())

sleep(10)

print(claims, claims.validate())