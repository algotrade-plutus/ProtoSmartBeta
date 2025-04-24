import os
from decimal import Decimal

from config.config import backtesting_config
from backtesting import Backtesting


def init_folder(path: str):
    """
    Creates the folder if it does not exist.

    Args:
        path (str): Path to the folder you want to initialize.
    """
    os.makedirs(path, exist_ok=True)


if __name__ == "__main__":
    required_directories = ["data", "result/optimization", "result/backtest"]
    for dir in required_directories:
        init_folder(dir)

    start_date_str = backtesting_config["is_from_date_str"]
    end_date_str = backtesting_config["is_end_date_str"]

    backtesting = Backtesting(
        buy_fee=Decimal(backtesting_config["buy_fee"]),
        sell_fee=Decimal(backtesting_config["sell_fee"]),
        from_date_str=start_date_str,
        to_date_str=end_date_str,
        capital=Decimal(backtesting_config["capital"]),
    )
    backtesting.load_data()
    backtesting.load_vnindex()
