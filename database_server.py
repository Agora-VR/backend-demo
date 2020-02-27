"""
This script uses two dependencies:

    + aiohttp (https://docs.aiohttp.org/en/stable/index.html)
    + asyncpg (https://magicstack.github.io/asyncpg/current/index.html)

These can be installed by running:

    pip install aiohttp asyncpg

The database I have running is called "postgres", is using a user with
name "postgres" and password "pg". I also created a table under the
"public" schema called "user" which has a "user_id" and "user_name" column
"""
from hashlib import pbkdf2_hmac
from os import urandom

from asyncpg import create_pool
from aiohttp import web
import aiohttp_cors


routes = web.RouteTableDef()

user_types = {
    "patient": 1,
    "clinician": 2,
    "caretaker": 3,
}


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


@routes.get("/user/{user_name}")
async def get_user(request):
    """ Get info on singular user """
    user_name = request.match_info["user_name"]

    async with request.app["pg_pool"].acquire() as connection:
        # Creating a prepared statement where "$1" is replaced by first argument
        statement = await connection.prepare("SELECT user_name, user_type_id FROM users WHERE user_name = $1")

        result = await statement.fetchrow(user_name)

        if result:
            return web.json_response(dict(result.items()))
        else:
            raise web.HTTPUnprocessableEntity(text=f"User \"{user_name}\" not registered!")


@routes.post("/register")
async def post_user(request):
    data = await request.json()  # Use this like a dictionary

    # Try to get the user_name value from the post data
    try:
        user_name, user_pass, user_type = data["user_name"], data["user_pass"], data["user_type"]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="Not all require parameters passed!")

    try:
        user_type_id = user_types[user_type]
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

        await connection.execute(
            "INSERT INTO users (user_type_id, user_name, user_hash, user_salt) VALUES ($1, $2, $3, $4);",
            user_type_id, user_name, password_hash, password_salt)

        return web.Response(text=f"User '{user_name}' successfully registered!")


if __name__ == "__main__":
    app = web.Application()

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False,
            expose_headers="*",
            allow_headers="*",
        ),
    })

    app.add_routes(routes)

    for route in app.router.routes():
        print(route)
        cors.add(route, {
            "http://localhost:5000": aiohttp_cors.ResourceOptions(
                allow_credentials=False,
                expose_headers="*",
                allow_headers="*",
            )
        })

    app.add_routes([web.static("/", "static")])

    app.cleanup_ctx.append(setup_app)

    web.run_app(app)
