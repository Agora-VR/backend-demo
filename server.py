from json.decoder import JSONDecodeError

from aiohttp import web


def check_required_keys(dictionary, *keys):
    return all(key in dictionary for key in keys)


routes = web.RouteTableDef()


@routes.view("/test")
class MyView(web.View):
    async def get(self):
        return web.Response(text="Hello, World!")

    async def post(self):
        try:
            data = await request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        if "name" not in data:
            raise web.HTTPUnprocessableEntity(text="Payload missing 'name' parameter")

        return web.Response(text=f"Hello, {data['name']}!")


@routes.post("/register")
async def register_post(request):
    try:
        data = await request.json()
    except JSONDecodeError:
        raise web.HTTPUnsupportedMediaType(text="Payload is not JSON")

    if not check_required_keys(data, "user_name", "user_pass"):
        raise web.HTTPUnprocessableEntity(text="Payload missing required parameter(s)")

    user_name, user_pass = data["user_name"], data["user_pass"]

    user_dict = request.app["users"]

    if user_name in user_dict:
        raise web.HTTPUnprocessableEntity(text="User name already registered")

    user_dict[user_name] = user_pass

    raise web.HTTPCreated(text="User created")


@routes.post("/login")
async def login_post(request):
    try:
        data = await request.json()
    except JSONDecodeError:
        raise web.HTTPUnsupportedMediaType(text="Payload could not be parsed as JSON")

    if not check_required_keys(data, "user_name", "user_pass"):
        raise web.HTTPUnprocessableEntity(text="Payload missing required parameter(s)")

    user_name, user_pass = data["user_name"], data["user_pass"]

    user_dict = request.app["users"]

    if user_name not in user_dict or user_pass != user_dict[user_name]:
        raise web.HTTPUnauthorized(text="Invalid user name and/or password")

    return web.json_response({"token": "abcdefghijklmnopqrstuvwxyz"})


if __name__ == "__main__":
    app = web.Application()

    app["users"] = {}

    app.add_routes(routes)

    web.run_app(app)
