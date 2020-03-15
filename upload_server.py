from pathlib import Path
from string import ascii_uppercase, digits
from random import choices
from tempfile import NamedTemporaryFile

from aiohttp import hdrs, web


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


@routes.post("/store2")
async def store_file_with_metadata(request):
    reader = await request.multipart()

    metadata_part = await reader.next()

    try:
        metadata_content_type = metadata_part.headers[hdrs.CONTENT_TYPE]
    except KeyError:
        raise web.HTTPUnprocessableEntity(text="No content type provided!")

    if metadata_part.headers[hdrs.CONTENT_TYPE] != "application/json":
        raise web.HTTPUnprocessableEntity(text="First part of request must be JSON!")

    print("metadata:", await metadata_part.json())

    file_part = await reader.next()

    # upload_name = Path(file_part.filename)

    # print("Uploading:", file_part.filename, file_part.headers[hdrs.CONTENT_TYPE])

    size = 0

    with NamedTemporaryFile(dir=request.app["storage_path"], delete=False) as tmp_file:
        while chunk := await file_part.read_chunk():
            size += len(chunk)

            tmp_file.write(chunk)

    tmp_path = Path(tmp_file.name)

    print("Wrote to:", tmp_path.name)

    return web.Response(text=f"Successfully stored file of size {size} bytes")


if __name__ == "__main__":
    app = web.Application()

    storage_path = Path("storage")

    if not storage_path.is_dir():
        storage_path.mkdir()

    app["storage_path"] = storage_path

    app.add_routes(routes)

    web.run_app(app)
