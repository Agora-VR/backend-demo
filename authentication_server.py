from json import dumps

from aiohttp import web
from authlib.jose import jwt
from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def load_keys(password):
    with open('private.pem', 'rb') as f:
        private_key = load_pem_private_key(
            f.read(), password=password.encode(), backend=default_backend())

    with open('public.pem', 'rb') as f:
        public_key = f.read()

    return public_key, private_key


routes = web.RouteTableDef()


@routes.post("/api/register")
async def register_user(request):
    data = await request.json()

    try:
        user_name, user_pass = data["user_name"], data["user_pass"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="Not all keys provided!")

    users = request.app["user_pass"]

    if user_name in users:
        raise web.HTTPUnprocessableEntity(text=f"User {user_name} already exists!")

    users[user_name] = user_pass

    return web.Response(text=f"User {user_name} successfully registered!")


@routes.post("/api/authenticate")
async def authenticate_user(request):
    data = await request.json()

    try:
        user_name, user_pass = data["user_name"], data["user_pass"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="Not all keys provided!")
    
    users = request.app["user_pass"]

    if user_name in users and users[user_name] == user_pass:
        private_key = request.app["private_key"]

        current_datetime = datetime.utcnow()
        expiration_delta = timedelta(seconds=15)

        payload = {'iss': 'Project Agora', 'exp': current_datetime + expiration_delta}
        header = {'alg': 'RS256'}

        return web.Response(text=jwt.encode(header, payload, private_key).decode())
    else:
        raise web.HTTPUnprocessableEntity(text="Invalid username/password combination")


if __name__ == "__main__":
    app = web.Application()

    app["user_pass"] = {}

    app["user_token"] = {}

    # Change the string argument to your key pair's password
    app["public_key"], app["private_key"] = load_keys("ButgersBuses")

    app.add_routes(routes)

    # app.add_routes([web.static("/", "static")])

    # app.cleanup_ctx.append(setup_app)

    web.run_app(app)
