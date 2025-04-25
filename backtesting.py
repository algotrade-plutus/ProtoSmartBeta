"""
This is main module for strategy backtesting
"""

from decimal import Decimal
from typing import List, Dict, Tuple
import pandas as pd
import matplotlib.pyplot as plt

from config.config import BACKTESTING_CONFIG
from database.data_service import DataService
from filter.financial import Financial
from metrics.metric import Metric

from utils import get_date, first_date_of_months, round_lot


def create_bt_instance(process_data=True, is_data=True):
    """
    Create backtesting instance

    Returns:
        _type_: smart_beta, grouped_data, rebalancing_dates
    """
    start_date_str = (
        BACKTESTING_CONFIG["is_from_date_str"]
        if is_data
        else BACKTESTING_CONFIG["os_from_date_str"]
    )
    end_date_str = (
        BACKTESTING_CONFIG["is_end_date_str"]
        if is_data
        else BACKTESTING_CONFIG["os_to_date_str"]
    )

    bt = Backtesting(
        buy_fee=Decimal(BACKTESTING_CONFIG["buy_fee"]),
        sell_fee=Decimal(BACKTESTING_CONFIG["sell_fee"]),
        from_date_str=start_date_str,
        to_date_str=end_date_str,
        capital=Decimal(BACKTESTING_CONFIG["capital"]),
        path="data/is/pe_dps.csv" if is_data else "data/os/pe_dps.csv",
        index_path="data/is/vnindex.csv" if is_data else "data/os/vnindex.csv",
    )

    data, dates = bt.process_data() if process_data else (None, None)
    return bt, data, dates


class Backtesting:
    """
    Backtesting main class
    """

    def __init__(
        self,
        buy_fee: Decimal,
        sell_fee: Decimal,
        from_date_str: str,
        to_date_str: str,
        capital: Decimal,
        path="data/is/pe_dps.csv",
        index_path="data/is/vnindex.csv",
    ):
        """
        Initiate required data

        Args:
            buy_fee (Decimal)
            sell_fee (Decimal)
            from_date_str (str)
            to_date_str (str)
            capital (Decimal)
            path (str, optional). Defaults to "data/is/pe_dps.csv".
            index_path (str, optional). Defaults to "data/is/vnindex.csv".
        """
        self.path = path
        self.index_path = index_path
        self.buy_fee = buy_fee
        self.sell_fee = sell_fee
        self.from_date_str = from_date_str
        self.to_date_str = to_date_str
        self.from_date_str = from_date_str
        self.to_date_str = to_date_str
        self.data_service = DataService()
        self.metric = None
        self.code = [
            72,  # NET_PROFIT_AFTER_TAX_ATTRIBUTE_TO_SHAREHOLDER = 72
            4110,  # OWNER_CAPITAL = 4110
            308,  #  DIVIDENDS_PAID
        ]

        self.capital = capital
        self.portfolio: Dict[str, Decimal] = {"CASH": capital}
        self.period_returns: List[Decimal] = []
        self.ac_returns: List[Decimal] = []
        self.assets: List[Decimal] = [capital]

        self.old_price: Dict[str, Decimal] = {}
        self.suspended_stock = []
        self.allocation = []

        # Date tracking
        self.rebalancing_dates = []
        self.tracking_dates = []
        self.vnindex_data = None

        self.start, self.from_date, self.to_date, self.end = get_date(
            from_date_str, to_date_str, look_back=252, forward_period=40
        )

    def load_vnindex(self) -> pd.DataFrame:
        """
        Load VNINDEX from csv

        Returns:
            pd.DataFrame
        """
        df = pd.DataFrame(
            self.get_vnindex(),
            columns=["date", "open", "close", "prev_close", "return", "ac_return"],
        )
        df.to_csv(self.index_path)
        return df

    def get_vnindex(self) -> pd.DataFrame:
        """
        Get VNINDEX price

        Returns:
            pd.DataFrame
        """

        _, _, _, end = get_date(
            self.from_date_str, self.to_date_str, look_back=252, forward_period=40
        )

        vnindex_data = self.data_service.get_index_data(
            self.from_date_str, end.strftime("%Y-%m-%d")
        )
        vnindex_data["prev_close"] = vnindex_data["close"].copy().shift(1)
        vnindex_data.loc[0, "prev_close"] = vnindex_data.loc[0, "close"]
        vnindex_data["return"] = (
            vnindex_data["close"].copy() - vnindex_data["prev_close"]
        ) / vnindex_data["prev_close"].copy()
        vnindex_data["ac_return"] = (
            vnindex_data["close"].copy() - vnindex_data["close"].iloc[0]
        ) / vnindex_data["close"].iloc[0]
        vnindex_data["return"] = vnindex_data["return"].apply(lambda x: Decimal(str(x)))

        return vnindex_data

    def total_asset(self, current_stocks: pd.DataFrame) -> Decimal:
        """
        Get total asset

        Args:
            current_stocks (pd.DataFrame)

        Returns:
            Decimal
        """
        total_asset = self.portfolio["CASH"]
        for _, row in current_stocks.iterrows():
            total_asset += (
                Decimal(row["prev_close"]) * self.portfolio[row["tickersymbol"]]
            )
        return total_asset

    def sell_stocks(
        self, current_stocks: pd.DataFrame, target_stocks: pd.DataFrame
    ) -> Tuple[Decimal, Decimal, pd.DataFrame]:
        """
        Sell stock before going to buy phase

        Args:
            current_stocks (pd.DataFrame)
            target_stocks (pd.DataFrame)

        Returns:
            Tuple[Decimal, Decimal, pd.DataFrame]: cash, total stock price, target portfolio
        """
        total_cash = self.portfolio["CASH"]
        stock_asset = Decimal('0.0')
        selling_data = []
        for _, row in current_stocks.iterrows():
            target_qty = (
                target_stocks[target_stocks["tickersymbol"] == row["tickersymbol"]][
                    "qty"
                ].iloc[0]
                if target_stocks["tickersymbol"].isin([row["tickersymbol"]]).any()
                else 0
            )

            required_qty = target_qty - self.portfolio[row["tickersymbol"]]

            if required_qty <= 0:
                selling_data.append(
                    [
                        row["tickersymbol"],
                        -1 * required_qty,
                        self.portfolio[row["tickersymbol"]],
                        row["prev_close"] * required_qty * -1,
                    ]
                )
                total_cash += (
                    Decimal(row["prev_close"])
                    * -required_qty
                    * (Decimal('1.0') - self.sell_fee)
                )
                self.portfolio[row["tickersymbol"]] += required_qty

                # update target stock
                target_stocks.drop(
                    target_stocks[
                        target_stocks["tickersymbol"] == row["tickersymbol"]
                    ].index,
                    inplace=True,
                )
            else:
                target_stocks.loc[
                    target_stocks["tickersymbol"] == row["tickersymbol"], "qty"
                ] = required_qty

            stock_asset += Decimal(row["close"]) * self.portfolio[row["tickersymbol"]]
            if self.portfolio[row["tickersymbol"]] == 0:
                del self.portfolio[row["tickersymbol"]]

        target_stocks["adjusted_qty"] = float(total_cash) / (
            len(target_stocks)
            * target_stocks["prev_close"].copy()
            * (1 + float(self.buy_fee))
        )
        target_stocks["adjusted_qty"] = (
            target_stocks["adjusted_qty"].apply(round_lot).copy()
        )
        target_stocks = target_stocks[target_stocks["adjusted_qty"] > 0].copy()

        return total_cash, stock_asset, target_stocks

    def rebalancing(
        self, group: pd.DataFrame, pe: List[float], dy: List[float]
    ) -> Decimal:
        """
        Buy and return current asset: cash + stock asset

        Args:
            group (pd.DataFrame)
            pe (List(float))
            dy (List(float))

        Returns:
            Decimal
        """
        qualified_stocks = group[
            (group['pe'].between(pe[0], pe[1])) & (group['dy'].between(dy[0], dy[1]))
        ].copy()
        stock_list = [symbol for symbol in self.portfolio if symbol != "CASH"]
        current_stocks = group[group["tickersymbol"].isin(stock_list)].copy()
        total_asset = self.total_asset(current_stocks)
        qualified_stocks["qty"] = float(total_asset) / (
            len(qualified_stocks) * qualified_stocks["prev_close"].copy()
        )
        qualified_stocks["qty"] = qualified_stocks["qty"].apply(round_lot)
        total_cash, stock_asset, qualified_stocks = self.sell_stocks(
            current_stocks, qualified_stocks
        )

        new_asset = stock_asset
        allocation = {"holding_capital": new_asset}
        for _, row in qualified_stocks.iterrows():
            self.old_price[row["tickersymbol"]] = row["close"]

            # Updating cash
            total_cash -= (
                row["qty"]
                * Decimal(row["prev_close"])
                * (Decimal("1.0") + self.sell_fee)
            )

            # Updating portfolio qty
            if row["tickersymbol"] not in self.portfolio:
                self.portfolio[row["tickersymbol"]] = 0
            self.portfolio[row["tickersymbol"]] += row["qty"]

            new_asset += Decimal(row["qty"]) * Decimal(row["close"])
            allocation["holding_capital"] += Decimal(row["qty"]) * Decimal(row["close"])

        self.portfolio["CASH"] = total_cash
        new_asset += self.portfolio["CASH"]

        # Update cash allocation
        allocation["cash_remaining"] = self.portfolio["CASH"]
        allocation["date"] = group["date"].iloc[0]
        self.allocation.append(allocation)

        return new_asset

    def daily_update_asset(self, group: pd.DataFrame) -> Decimal:
        """
        Daily update asset without rebalancing
        Args:
            group (pd.DataFrame)

        Returns:
            Decimal
        """
        asset = Decimal('0.0')
        for symbol, value in self.portfolio.items():
            if symbol == "CASH":
                asset += value
            else:
                try:
                    price = group[group['tickersymbol'] == symbol]["close"].iloc[0]
                    asset += value * Decimal(price)
                    self.old_price[symbol] = price
                except Exception as _:
                    self.suspended_stock.append(
                        [group["date"].iloc[0], symbol, self.old_price[symbol]]
                    )
                    asset += value * Decimal(self.old_price[symbol])

        return asset

    def update_period_return(
        self,
        group: pd.DataFrame,
        is_rebalancing: bool,
        pe=List[float],
        dy=List[float],
    ):
        """
        Update period return

        Args:
            group (pd.DataFrame)
            is_rebalancing (bool)
            pe (List(float))
            dy (List(float))
        """
        current_asset = self.assets[-1]
        updated_asset = (
            self.rebalancing(group, pe, dy)
            if is_rebalancing
            else self.daily_update_asset(group)
        )
        self.period_returns.append(updated_asset / current_asset - 1)
        self.ac_returns.append(updated_asset / self.capital - 1)
        self.assets.append(updated_asset)

    def load_data(self):
        """
        Load data to csv file
        """
        print("Fetching data from db...")
        start, from_date, to_date, end = get_date(
            self.from_date_str, self.to_date_str, look_back=252, forward_period=40
        )
        financial_data = self.data_service.get_financial_data(
            from_date.year - 1, to_date.year - 1, self.code
        )

        print("Loading data...")
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

    def process_data(self):
        """
        Process and group data to single data frame

        Returns:
            _type_: _description_
        """
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

        self.vnindex_data = pd.read_csv(self.index_path)
        self.vnindex_data["date"] = pd.to_datetime(self.vnindex_data["date"]).dt.date
        self.vnindex_data["return"] = self.vnindex_data["return"].apply(
            lambda x: Decimal(str(x))
        )

        return backtesting_data.groupby(["date"]), first_date_of_months(
            self.from_date_str, self.to_date_str
        )

    def run(
        self,
        processed_data,
        execution_dates,
        pe=BACKTESTING_CONFIG["pe"],
        dy=BACKTESTING_CONFIG["dy"],
    ):
        """_summary_

        Args:
            processed_data (_type_): _description_
            execution_dates (_type_): _description_
            pe (_type_, optional): _description_. Defaults to backtesting_config["pe"].
            dy (_type_, optional): _description_. Defaults to backtesting_config["dy"].

        Returns:
            _type_: _description_
        """
        is_rebalancing = False
        for date, group in processed_data:
            is_rebalancing = (
                ((not is_rebalancing) and (date[0] >= execution_dates.queue[0]))
                if not execution_dates.empty()
                else False
            )
            self.update_period_return(group, is_rebalancing, pe, dy)
            if is_rebalancing:
                self.rebalancing_dates.append(date[0])
                execution_dates.get()

            self.tracking_dates.append(date[0])

        self.metric = Metric(self.period_returns, self.vnindex_data["return"].to_list())
        return self.metric.sharpe_ratio(Decimal('0.03'))

    def plot_nav(self, path="result/backtest/nav.png"):
        """
        Plot and save NAV chart to path

        Args:
            path (str, optional): _description_. Defaults to "result/backtest/nav.png".
        """
        plt.figure(figsize=(10, 6))

        plt.plot(
            self.tracking_dates,
            self.ac_returns,
            label="Portfolio",
            color='black',
        )
        plt.plot(
            self.vnindex_data["date"],
            self.vnindex_data["ac_return"],
            label="VNINDEX",
            color='red',
        )

        plt.title('Asset Value Over Time')
        plt.xlabel('Time Step')
        plt.ylabel('Asset Value')
        plt.grid(True)
        plt.legend()
        plt.savefig(path, dpi=300, bbox_inches='tight')

    def plot_drawdown(self, path="result/backtest/drawdown.png"):
        """
        Plot and save drawdown chart to path

        Args:
            path (str, optional): _description_. Defaults to "result/backtest/drawdown.png".
        """
        _, drawdowns = self.metric.maximum_drawdown()

        plt.figure(figsize=(10, 6))
        plt.plot(
            self.tracking_dates,
            drawdowns,
            label="Portfolio",
            color='black',
        )

        plt.title('Draw down Value Over Time')
        plt.xlabel('Time Step')
        plt.ylabel('Percentage')
        plt.grid(True)
        plt.savefig(path, dpi=300, bbox_inches='tight')


if __name__ == "__main__":
    smart_beta, grouped_data, rebalancing_dates = create_bt_instance(
        process_data=True, is_data=True
    )
    sr = smart_beta.run(processed_data=grouped_data, execution_dates=rebalancing_dates)

    print(f"Sharpe ratio {sr}")
    print(f"Information ratio {smart_beta.metric.information_ratio()}")
    print(f"Sortino ratio {smart_beta.metric.sortino_ratio( Decimal('0.03'))}")
    mdd, dds = smart_beta.metric.maximum_drawdown()
    print(f"MDD {mdd}")

    smart_beta.plot_nav()
    smart_beta.plot_drawdown()
