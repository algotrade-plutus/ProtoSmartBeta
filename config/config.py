import os
import json
from dotenv import load_dotenv


load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")
database = os.getenv("DATABASE")
user = os.getenv("USER_DB")
password = os.getenv("PASSWORD")

db_params = {
    "host": host,
    "port": port,
    "database": database,
    "user": user,
    "password": password,
}

backtesting_config = None
with open("parameter/backtesting_parameter.json", 'r') as f:
    backtesting_config = json.load(f)

optimization_config = None
with open("parameter/optimization_parameter.json", 'r') as f:
    optimization_config = json.load(f)
