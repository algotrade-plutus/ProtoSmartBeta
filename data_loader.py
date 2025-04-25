import os
from decimal import Decimal

from config.config import backtesting_config
from backtesting import Backtesting, create_bt_instance


def init_folder(path: str):
    """
    Creates the folder if it does not exist.

    Args:
        path (str): Path to the folder you want to initialize.
    """
    os.makedirs(path, exist_ok=True)


if __name__ == "__main__":
    required_directories = [
        "data",
        "data/is",
        "data/os",
        "result/optimization",
        "result/backtest",
        "result/optimization",
    ]
    for dir in required_directories:
        init_folder(dir)

    # Loading insample data
    is_instance, _, _ = create_bt_instance(process_data=False, is_data=True)
    is_instance.load_data()
    is_instance.load_vnindex()

    os_instance, _, _ = create_bt_instance(process_data=False, is_data=False)
    os_instance.load_data()
    os_instance.load_vnindex()
