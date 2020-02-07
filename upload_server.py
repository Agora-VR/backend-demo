from pathlib import Path
from string import ascii_uppercase, digits
from random import choices

from aiohttp import web


routes = web.RouteTableDef()


def get_random_string(size=32, chars=(ascii_uppercase + digits)):
    """ Get a random string of uppercase characters and numbers """
    return "".join(choices(chars, k=size))


@routes.post("/store")
async def store_file(request):
    reader = await request.multipart()

    field = await reader.next()

    upload_name = Path(field.filename)

    print("Uploading:", field.filename)

    file_name = get_random_string()

    write_path = Path(".", file_name + upload_name.suffix)

    size = 0

    with open(write_path, "wb") as f:
        while True:
            chunk = await field.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    print("Wrote to:", write_path)

    return web.Response(text=f"Stored file {write_path} of size {size} bytes\n")


if __name__ == "__main__":
    app = web.Application()

    app.add_routes(routes)

    web.run_app(app)
