import time
from datetime import datetime
from decimal import Decimal
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt

from database.data_service import DataService
from filter.financial import Financial
from metrics.metric import Metric
from visualization import plot_portfolio_allocation

from utils import get_date, first_date_of_month, round_lot


class Backtesting:
    def __init__(
        self,
        buy_fee: Decimal,
        sell_fee: Decimal,
        from_date_str: str,
        to_date_str: str,
        capital: Decimal,
        path="temp.csv",
    ):
        self.path = path
        self.buy_fee = buy_fee
        self.sell_fee = sell_fee
        self.code = [
            72,  # NET_PROFIT_AFTER_TAX_ATTRIBUTE_TO_SHAREHOLDER = 72
            4110,  # OWNER_CAPITAL = 4110
            308,  #  DIVIDENDS_PAID
        ]
        self.from_date_str = from_date_str
        self.to_date_str = to_date_str
        self.data_service = DataService()
        self.portfolio: Dict[str, Decimal] = {"CASH": capital}
        self.old_price: Dict[str, Decimal] = {}
        self.period_returns: List[Decimal] = []
        self.ac_returns: List[Decimal] = []
        self.suspended_stock = []
        self.assets: List[Decimal] = [capital]
        self.capital = capital
        self.allocation = []
        self.tracking_dates = []

        self.start, self.from_date, self.to_date, self.end = get_date(
            from_date_str, to_date_str, look_back=252, forward_period=40
        )

    @staticmethod
    def get_vnindex(self):
        return self.data_service.get_index_data(self.start_date_str, self.end)

    def total_asset(self, current_stocks: pd.DataFrame) -> datetime:
        total_asset = self.portfolio["CASH"]
        for _, row in current_stocks.iterrows():
            total_asset += (
                Decimal(row["prev_close"]) * self.portfolio[row["tickersymbol"]]
            )
        return total_asset

    def sell_stocks(
        self, current_stocks: pd.DataFrame, target_stocks: pd.DataFrame
    ) -> Decimal:
        total_cash = self.portfolio["CASH"]
        for _, row in current_stocks.iterrows():
            target_stock = (
                target_stocks[target_stocks["tickersymbol"] == row["tickersymbol"]][
                    "amt"
                ].iloc[0]
                if target_stocks["tickersymbol"].isin([row["tickersymbol"]]).any()
                else 0
            )

            required_stock = target_stock - self.portfolio[row["tickersymbol"]]

            if required_stock < 0:
                total_cash += (
                    Decimal(row["prev_close"])
                    * -required_stock
                    * (Decimal('1.0') - self.sell_fee)
                )
                self.portfolio[row["tickersymbol"]] += required_stock
                if self.portfolio[row["tickersymbol"]] == 0:
                    del self.portfolio[row["tickersymbol"]]

                target_stock = target_stocks.drop(
                    target_stocks[
                        target_stocks["tickersymbol"] == row["tickersymbol"]
                    ].index,
                    inplace=True,
                )
        target_stocks["amt"] = float(total_cash) / (
            len(target_stocks)
            * target_stocks["prev_close"].copy()
            * (1 + float(self.buy_fee))
        )
        target_stocks["amt"] = target_stocks["amt"].apply(round_lot)
        target_stocks = target_stocks[target_stocks["amt"] > 0].copy()

        return total_cash, target_stocks

    def rebalancing(self, group: pd.DataFrame) -> Decimal:
        """
            Buy and return current asset

        Args:
            group (pd.DataFrame)

        Returns:
            Decimal
        """
        qualified_stocks = group[
            (group['pe'].between(0, 15)) & (group['dy'] > 0.01)
        ].copy()
        stock_list = [symbol for symbol in self.portfolio if symbol != "CASH"]
        current_stocks = group[group["tickersymbol"].isin(stock_list)].copy()
        total_asset = self.total_asset(current_stocks)

        qualified_stocks["amt"] = float(total_asset) / (
            len(qualified_stocks) * qualified_stocks["prev_close"].copy()
        )
        qualified_stocks["amt"] = qualified_stocks["amt"].apply(round_lot)
        total_cash, qualified_stocks = self.sell_stocks(
            current_stocks, qualified_stocks
        )

        new_asset = Decimal('0.0')
        allocation = {"holdings": {}}
        for _, row in qualified_stocks.iterrows():
            self.old_price[row["tickersymbol"]] = row["close"]
            current_qty = (
                self.portfolio[row["tickersymbol"]]
                if row["tickersymbol"] in self.portfolio
                else 0
            )
            remained_amt = row["amt"] - current_qty
            if remained_amt == 0:
                continue

            self.portfolio[row["tickersymbol"]] = row["amt"]
            new_asset += Decimal(row["amt"]) * Decimal(row["close"])
            allocation["holdings"][row["tickersymbol"]] = Decimal(row["amt"]) * Decimal(
                row["close"]
            )
            total_cash -= (
                remained_amt
                * Decimal(row["prev_close"])
                * (Decimal('1.0') + self.sell_fee)
            )

        self.portfolio["CASH"] = total_cash
        new_asset += self.portfolio["CASH"]
        allocation["cash_remaining"] = self.portfolio["CASH"]
        allocation["date"] = group["date"].iloc[0]
        self.allocation.append(allocation)

        return new_asset

    def daily_update_asset(self, group: pd.DataFrame):
        asset = Decimal('0.0')
        for symbol, value in self.portfolio.items():
            if symbol == "CASH":
                asset += value
            else:
                try:
                    price = group[group['tickersymbol'] == symbol]["close"].iloc[0]
                    asset += value * Decimal(price)
                    self.old_price[symbol] = price
                except:
                    self.suspended_stock.append(
                        [group["date"].iloc[0], symbol, self.old_price[symbol]]
                    )
                    asset += value * Decimal(self.old_price[symbol])

        return asset

    def update_period_return(self, group: pd.DataFrame, is_rebalancing: bool):
        current_asset = self.assets[-1]
        updated_asset = (
            self.rebalancing(group)
            if is_rebalancing
            else self.daily_update_asset(group)
        )
        self.period_returns.append(updated_asset / current_asset - 1)
        self.ac_returns.append(updated_asset / self.capital - 1)
        self.assets.append(updated_asset)

    def load_data(self, from_date_str, to_date_str):
        start, from_date, to_date, end = get_date(
            from_date_str, to_date_str, look_back=252, forward_period=40
        )
        financial_data = self.data_service.get_financial_data(
            from_date.year - 1, to_date.year - 1, self.code
        )

        daily_data = self.data_service.get_daily_data(from_date, end)
        daily_data['prev_close'] = (
            daily_data.groupby('tickersymbol')['close'].shift(1).dropna()
        )

        daily_data["date"] = pd.to_datetime(daily_data["date"]).dt.date
        daily_data = daily_data.astype({"close": float, "prev_close": float})
        financial = Financial(from_date=start, to_date=to_date, data=financial_data)
        financial_filtered_data = pd.merge(
            financial.eps(), financial.dps(), on=["year", "tickersymbol"], how="outer"
        ).fillna(0)

        backtesting_data = pd.merge(
            daily_data,
            financial_filtered_data,
            on=["year", "tickersymbol"],
            how="outer",
        )
        backtesting_data["pe"] = (
            backtesting_data["prev_close"].copy()
            * 1000
            / backtesting_data["eps"].copy()
        )
        backtesting_data["dy"] = (
            backtesting_data["dps"].copy()
            * -1
            / (backtesting_data["prev_close"].copy() * 1000)
        )
        backtesting_data = backtesting_data[~backtesting_data["date"].isna()].copy()
        backtesting_data.to_csv(self.path)
        print("Data is loaded...")

    def run(self):
        backtesting_data = pd.read_csv(self.path)
        backtesting_data["date"] = pd.to_datetime(backtesting_data["date"]).dt.date
        backtesting_data = backtesting_data.astype(
            {
                "close": float,
                "prev_close": float,
                "eps": float,
                "dps": float,
                "pe": float,
                "dy": float,
            }
        )

        start = time.time()
        grouped_data = backtesting_data.groupby(["date"])
        rebalancing_dates = first_date_of_month(self.from_date_str, self.to_date_str)
        is_rebalancing = False
        for date, group in grouped_data:
            is_rebalancing = (
                (not is_rebalancing and date[0] >= rebalancing_dates.queue[0])
                if not rebalancing_dates.empty()
                else False
            )
            self.update_period_return(group, is_rebalancing)
            if is_rebalancing:
                is_rebalancing = False
                rebalancing_dates.get()

            self.tracking_dates.append(date)
        end = time.time()

        print(f"Total time: {end - start}")


if __name__ == "__main__":
    start_date_str = "2022-03-01"
    end_date_str = "2024-01-01"

    smart_beta = Backtesting(
        buy_fee=Decimal('0.00035'),
        sell_fee=Decimal('0.00035'),
        from_date_str=start_date_str,
        to_date_str=end_date_str,
        capital=Decimal("25e6"),
    )

    # # Uncomment this for loading data
    # smart_beta.load_data(start_date_str, end_date_str)

    start, from_date, to_date, end = get_date(
        start_date_str, end_date_str, look_back=252, forward_period=40
    )

    vnindex_data = smart_beta.data_service.get_index_data(start_date_str, end)
    vnindex_data["prev_close"] = vnindex_data["close"].copy().shift(1)
    vnindex_data.loc[0, "prev_close"] = vnindex_data.loc[0, "close"]
    vnindex_data["return"] = (
        vnindex_data["close"].copy() - vnindex_data["prev_close"]
    ) / vnindex_data["prev_close"].copy()
    vnindex_data["ac_return"] = (
        vnindex_data["close"].copy() - vnindex_data["close"].iloc[0]
    ) / vnindex_data["close"].iloc[0]
    vnindex_data["return"] = vnindex_data["return"].apply(lambda x: Decimal(str(x)))

    smart_beta.run()
    metric = Metric(smart_beta.period_returns, vnindex_data["return"].to_list())
    # print(f"Sharpe ratio {metric.sharpe_ratio(Decimal('0.03'))}")
    # print(f"Information ratio {metric.information_ratio()}")
    mdd, dds = metric.maximum_drawdown()
    print(f"MDD {mdd}")

    # print(f"Longest DD {metric.longest_drawdown()}")

    # plot_portfolio_allocation(smart_beta.allocation[50:60])

    plt.figure(figsize=(10, 6))
    plt.plot(
        smart_beta.tracking_dates,
        dds,
        label="Portfolio",
        color='black',
    )
    # plt.plot(
    #     vnindex_data["date"],
    #     vnindex_data["ac_return"],
    #     label="VNINDEX",
    #     color='red',
    # )

    # Adding titles and labels
    plt.title('Asset Value Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Asset Value')
    plt.grid(True)

    # Show the plot
    plt.tight_layout()  # Ensures everything fits nicely
    plt.show()
