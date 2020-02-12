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

from asyncpg import create_pool
from aiohttp import web


routes = web.RouteTableDef()


async def setup_app(app):
    """
    An example of a cleanup context in aiohttp

    https://docs.aiohttp.org/en/stable/web_advanced.html#cleanup-context
    """
    # On startup
    # Using a static password for demo purposes
    app["pg_pool"] = await create_pool(
        database="agora", user="postgres", password="pg")

    yield

    # On cleanup
    await app['pg_pool'].close()


@routes.get("/users")
async def get_users(request):
    """ Get list of users """
    async with request.app["pg_pool"].acquire() as connection:
        results = await connection.fetch("SELECT * FROM users")

        return web.json_response([dict(result.items()) for result in results])


@routes.get("/user/{user_name}")
async def get_user(request):
    """ Get info on singular user """
    user_name = request.match_info["user_name"]

    async with request.app["pg_pool"].acquire() as connection:
        # Creating a prepared statement where "$1" is replaced by first argument
        statement = await connection.prepare("SELECT * FROM users WHERE user_name = $1")

        result = await statement.fetchrow(user_name)

        if result:
            return web.json_response(dict(result.items()))
        else:
            raise web.HTTPUnprocessableEntity(text=f"User \"{user_name}\" not registered!")


"""
@routes.post("/register")
async def post_user(request):
    data = await request.post()  # Use this like a dictionary

    async with request.app["pg_pool"].acquire() as connection:
"""


if __name__ == "__main__":
    app = web.Application()

    app.add_routes(routes)

    app.cleanup_ctx.append(setup_app)

    web.run_app(app)
