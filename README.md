# backend-demo

## Requirements

* [postgresql server](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
* [Python 3.8](https://www.python.org/downloads/)

I also recommend using the
[Powershell Preview](https://github.com/PowerShell/PowerShell/releases/tag/v7.0.0-rc.2)
for use in Visual Studio Code.

## Create a Virtual Environment

To run these scripts, it is best to create a virtual environment and install
the dependencies in it.

First, create the virtual environment:

```
py -m venv .venv
```

Next, enter the virtual environment. Once you are in, you should see green
text at the beginning of your prompt saying `(.venv)`

```
.\.venv\Scripts\Activate.ps1
```

Now, install the dependencies with pip:

```
pip install aiohttp asyncpg
```

## Running the Script

Before running the script, be sure to enter the virtual environment. Again,
the green text is an indicator of whether you are in the virtual environment
or not. If you don't seen green text, run:

```
.\.venv\Scripts\Activate.ps1
```

Next, run the script:

```
python .\database_server.py
```

Assuming your local Postgresql database server is running and has an
`agora` database inside, the server should be running on port 8080.

