"""
Data service
"""

import psycopg2
import pandas as pd

from database.query import DAILY_DATA_QUERY, FINANCIAL_INFO_QUERY, INDEX_QUERY
from config.config import db_params


class DataService:
    """
    Class data service
    """

    def __init__(self) -> None:
        """
        Initiate database secret
        """
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
        """
        Get financial data frame

        Args:
            from_year (str): _description_
            to_year (str): _description_
            included_code (list[str]): _description_

        Returns:
            pd.DataFrame: _description_
        """
        cursor = self.connection.cursor()
        cursor.execute(
            FINANCIAL_INFO_QUERY,
            (
                from_year,
                str(to_year),
                tuple(included_code),
            ),
        )

        queries = list(cursor)
        cursor.close()

        columns = ["year", "tickersymbol", "value", "code"]
        return pd.DataFrame(queries, columns=columns)

    def get_daily_data(
        self,
        from_date: str,
        to_date: str,
    ) -> pd.DataFrame:
        """
        Get daily data frame

        Args:
            from_date (str): _description_
            to_date (str): _description_

        Returns:
            pd.DataFrame: _description_
        """
        cursor = self.connection.cursor()
        cursor.execute(DAILY_DATA_QUERY, (from_date, to_date))

        queries = list(cursor)
        cursor.close()

        columns = ["year", "date", "tickersymbol", "close"]
        return pd.DataFrame(queries, columns=columns)

    def get_index_data(
        self,
        from_date: str,
        to_date: str,
    ) -> pd.DataFrame:
        """
        Get index data frame

        Args:
            from_date (str): _description_
            to_date (str): _description_

        Returns:
            pd.DataFrame: _description_
        """
        cursor = self.connection.cursor()
        cursor.execute(INDEX_QUERY, (from_date, to_date))

        queries = list(cursor)
        cursor.close()

        columns = ["date", "open", "close"]
        return pd.DataFrame(queries, columns=columns)


data_service = DataService()
