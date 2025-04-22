import psycopg2
import pandas as pd

from database.query import *
from config.config import *


class DataService:
    def __init__(self) -> None:
        if (
            db_params["host"]
            and db_params["port"]
            and db_params["database"]
            and db_params["user"]
            and db_params["password"]
        ):
            self.connection = psycopg2.connect(**db_params)
            self.is_file = False
        else:
            self.is_file = True

    def get_financial_data(
        self,
        from_year: str,
        to_year: str,
        included_code: list[str],
    ) -> pd.DataFrame:

        cursor = self.connection.cursor()
        cursor.execute(
            financial_info_query,
            (
                from_year,
                str(to_year),
                tuple(included_code),
            ),
        )

        queries = [query for query in cursor]
        cursor.close()

        columns = ["year", "tickersymbol", "value", "code"]
        return pd.DataFrame(queries, columns=columns)

    def get_daily_data(
        self,
        from_date: str,
        to_date: str,
    ) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cursor.execute(daily_data_query, (from_date, to_date))

        queries = [query for query in cursor]
        cursor.close()

        columns = ["year", "date", "tickersymbol", "close"]
        return pd.DataFrame(queries, columns=columns)

    def get_index_data(
        self,
        from_date: str,
        to_date: str,
    ) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cursor.execute(index_query, (from_date, to_date))

        queries = [query for query in cursor]
        cursor.close()

        columns = ["date", "open", "close"]
        return pd.DataFrame(queries, columns=columns)


data_service = DataService()
