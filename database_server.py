"""
This script uses two dependencies:

    + aiohttp (https://docs.aiohttp.org/en/stable/index.html)
    + asyncpg (https://magicstack.github.io/asyncpg/current/index.html)

These can be installed by running:

    pip install aiohttp aiohttp_cors asyncpg Authlib

The database I have running is called "postgres", is using a user with
name "postgres" and password "pg". I also created a table under the
"public" schema called "user" which has a "user_id" and "user_name" column
"""
from datetime import datetime
from hashlib import pbkdf2_hmac
from os import urandom

from asyncpg import create_pool
from aiohttp import web
import aiohttp_cors
from authlib.jose import errors, jwt
from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def get_key_with_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key


def load_keys(password):
    with open('private.pem', 'rb') as f:
        private_key = load_pem_private_key(
            f.read(), password=password.encode(), backend=default_backend())

    with open('public.pem', 'rb') as f:
        public_key = f.read()

    return public_key, private_key


def validate_request(request):
    try:
        authorization_value = request.headers["Authorization"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="No authorization header provided!")

    auth_type, auth_token = authorization_value.split(" ")

    if auth_type != "Bearer":
        raise web.HTTPUnprocessableEntity(text="Invalid authentication method!")

    tokens = request.app["tokens"]

    if auth_token not in tokens.values():
        raise web.HTTPUnprocessableEntity(text="Invalidated authentication token used!")

    claims = jwt.decode(auth_token, request.app["public_key"])

    try:
        claims.validate()
        return claims
    except errors.ExpiredTokenError:
        del request.app["tokens"][get_key_with_value(tokens, auth_token)]

        raise web.HTTPUnprocessableEntity(text="Provided token is expired!")


routes = web.RouteTableDef()


async def setup_app(app):
    """
    An example of a cleanup context in aiohttp

    https://docs.aiohttp.org/en/stable/web_advanced.html#cleanup-context
    """
    # On server startup
    # Using a static password for demo purposes
    app["pg_pool"] = await create_pool(
        database="agora", user="postgres", password="pg")

    yield

    # On server shutdown (cleanup)
    await app['pg_pool'].close()


@routes.get("/users")
async def get_users(request):
    """ Get list of users """
    async with request.app["pg_pool"].acquire() as connection:
        results = await connection.fetch("SELECT user_name, user_type_id FROM users")

        return web.json_response([dict(result.items()) for result in results])


# @routes.get("/user/{user_name}")
# async def get_user(request):
#     """ Get info on singular user """
#     print(validate_request(request))

#     user_name = request.match_info["user_name"]

#     async with request.app["pg_pool"].acquire() as connection:
#         # Creating a prepared statement where "$1" is replaced by first argument
#         statement = await connection.prepare("SELECT user_name, user_type_id FROM users WHERE user_name = $1")

#         result = await statement.fetchrow(user_name)

#         if result:
#             return web.json_response(dict(result.items()))
#         else:
#             raise web.HTTPUnprocessableEntity(text=f"User \"{user_name}\" not registered!")


@routes.post("/register")
async def post_user(request):
    data = await request.json()  # Use this like a dictionary

    # Try to get the user_name value from the post data
    try:
        user_name, user_pass, user_type = data["user_name"], data["user_pass"], data["user_type"]
        user_full_name = data["user_full_name"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="Not all require parameters passed!")

    try:
        user_type_id = request.app["types"][user_type]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text=f"Invalid user type '{user_type}' provided!")

    password_salt = urandom(32)

    password_hash = pbkdf2_hmac("sha256", user_pass.encode(), password_salt, 100000)

    async with request.app["pg_pool"].acquire() as connection:
        # Validate if the user already exists
        validate_stmt = await connection.prepare("SELECT user_id FROM users WHERE user_name = $1")

        # If the user is already registered
        if await validate_stmt.fetchval(user_name):
            raise web.HTTPUnprocessableEntity(text=f"User '{user_name}' already registered!")

        await connection.execute("""
            INSERT INTO users (user_type_id, user_name, user_full_name, user_hash, user_salt)
            VALUES ($1, $2, $3, $4, $5)""",
            user_type_id, user_name, user_full_name, password_hash, password_salt)

        return web.Response(text=f"User '{user_name}' successfully registered!")


@routes.post("/authenticate")
async def authenticate_user(request):
    data = await request.json()

    try:
        user_name, user_pass = data["user_name"], data["user_pass"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="Not all keys provided!")

    async with request.app["pg_pool"].acquire() as connection:
        user_stmt = await connection.prepare("SELECT * FROM users NATURAL JOIN user_types WHERE user_name = $1")

        user_result = await user_stmt.fetchrow(user_name)

        if user_result is None:
            raise web.HTTPUnprocessableEntity(text="Invalid credential provided!")

        user_data = dict(user_result.items())

    user_hash, user_salt = user_data["user_hash"], user_data["user_salt"]

    password_hash = pbkdf2_hmac("sha256", user_pass.encode(), user_salt, 100000)

    # If the hashes don't match
    if password_hash != user_hash:
        raise web.HTTPUnprocessableEntity(text="Invalid credential provided!")

    private_key = request.app["private_key"]

    current_datetime = datetime.utcnow()
    expiration_delta = timedelta(minutes=20)

    user_id = user_data["user_id"]

    payload = {
        'iss': "Agora VR",
        'exp': current_datetime + expiration_delta,
        'agora': {
            'user_id': user_id,
            'user_name': user_data["user_name"],
            'user_type': user_data["user_type_name"],
        },
    }

    token = jwt.encode({'alg': "RS256"}, payload, private_key)

    request.app["tokens"][user_id] = token.decode()

    return web.Response(body=token)


@routes.get("/user/clinicians")
async def get_clinicians(request):
    session = validate_request(request)["agora"]

    user_id, user_type = session["user_id"], session["user_type"]

    if user_type not in request.app["types"] or user_type != "patient":
        raise web.HTTPUnprocessableEntity(text="Client is not a valid user type for endpoint!")

    async with request.app["pg_pool"].acquire() as connection:
        clinician_stmt = await connection.prepare("""
            SELECT user_id, user_name, user_full_name
            FROM serves JOIN users ON users.user_id = serves.clinician_id
            WHERE serves.patient_id = $1""")

        results = await clinician_stmt.fetch(user_id)

        return web.json_response([dict(result.items()) for result in results])


@routes.get("/user/patients")
async def get_patients(request):
    session = validate_request(request)["agora"]

    user_id, user_type = session["user_id"], session["user_type"]

    if user_type not in request.app["types"] or user_type != "clinician":
        raise web.HTTPUnprocessableEntity(text="Client is not a valid user type for this endpoint!")

    async with request.app["pg_pool"].acquire() as connection:
        clinician_stmt = await connection.prepare("""
            SELECT user_id, user_name, user_full_name
            FROM serves JOIN users ON users.user_id = serves.patient_id
            WHERE serves.clinician_id = $1""")

        results = await clinician_stmt.fetch(user_id)

        return web.json_response([dict(result.items()) for result in results])


@routes.get("/user/register_form")
async def get_register_form(request):
    session = validate_request(request)["agora"]

    user_type = session["user_type"]

    async with request.app["pg_pool"].acquire() as connection:
        statement = await connection.prepare("""
            SELECT forms.*
            FROM user_types JOIN forms ON user_type_form_name = form_name
            WHERE user_type_name = $1""")

        result = await statement.fetchrow(user_type)

        if result:
            return web.json_response(dict(result.items()))


@routes.post("/user/register_form")
async def post_register_form(request):
    session = validate_request(request)["agora"]

    data = await request.json()

    try:
        form_name, form_data = data["name"], data["results"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="Not all keys provided!")

    async with request.app["pg_pool"].acquire() as connection:
        await connection.execute("""
            INSERT INTO responses (response_owner_id, response_form_name, response_datetime, response_data)
            VALUES ($1, $2, $3, $4)""",
            session["user_id"], form_name, datetime.utcnow(), form_data)

        return web.Response(text="Form response registered successfully!")


if __name__ == "__main__":
    app = web.Application()

    app["public_key"], app["private_key"] = load_keys("EmotionComedian")

    app["tokens"] = {}

    app["types"] = {
        "patient": 1,
        "clinician": 2,
        "caregiver": 3,
    }

    cors = aiohttp_cors.setup(app, defaults={
        "http://localhost:5000": aiohttp_cors.ResourceOptions(
            allow_credentials=False,
            expose_headers="*",
            allow_headers="*",
        ),
    })

    app.add_routes(routes)

    for route in app.router.routes():
        cors.add(route)

    app.cleanup_ctx.append(setup_app)

    web.run_app(app)
