"""
Financial module for loading financial data
"""

from datetime import datetime
import pandas as pd


class Financial:
    """
    Financial data class
    """

    def __init__(self, from_date: datetime, to_date: datetime, data: pd.DataFrame):
        """

        Args:
            from_date (datetime): _description_
            to_date (datetime): _description_
            data (pd.DataFrame): _description_
        """
        self.from_date = from_date
        self.to_date = to_date
        self.data = data

    def total_share(self) -> pd.DataFrame:
        """
        Get total share data frame

        Returns:
            pd.DataFrame
        """
        owner_capital = (
            self.data[self.data["code"] == 4110].copy().drop(columns=["code"])
        )

        outstanding_share = owner_capital.copy()
        outstanding_share["value"] = outstanding_share["value"].copy() / 10000
        outstanding_share = outstanding_share.rename(
            columns={"value": "outstanding_share"}
        )
        return outstanding_share.copy()

    def eps(self) -> pd.DataFrame:
        """
        Get eps dataframe

        Returns:
            pd.DataFrame
        """
        earning = (
            self.data[self.data["code"] == 72]
            .copy()
            .rename(columns={"value": "earning"})
            .drop(columns=["code"])
        )

        eps = pd.merge(
            earning, self.total_share(), on=["year", "tickersymbol"]
        ).sort_values(by=["year", "tickersymbol"])
        eps["eps"] = eps["earning"].copy() / eps["outstanding_share"].copy()
        eps = eps[["year", "tickersymbol", "eps"]].dropna()
        return eps.astype({"eps": float})

    def dps(self) -> pd.DataFrame:
        """
        Get dps dataframe

        Returns:
            pd.DataFrame
        """
        dividends_paid = (
            self.data[self.data["code"] == 308]
            .copy()
            .rename(columns={"value": "dividends_paid"})
            .drop(columns=["code"])
        )

        dps = pd.merge(dividends_paid, self.total_share(), on=["year", "tickersymbol"])
        dps["dps"] = dps["dividends_paid"].copy() / dps["outstanding_share"].copy()
        dps = dps[["year", "tickersymbol", "dps"]].dropna()
        return dps.astype({"dps": float})
