"""
Out-sample evaluation module
"""

from decimal import Decimal
from backtesting import create_bt_instance


if __name__ == "__main__":
    bt, grouped_data, rebalancing_dates = create_bt_instance(
        process_data=True, is_data=False
    )

    sr = bt.run(
        processed_data=grouped_data,
        execution_dates=rebalancing_dates,
        pe=[0.2164884729382647, 17.174669892864713],
        dy=[0.034556913031198136, 0.0876931181106818],
    )

    print(f"Sharpe ratio {sr}")
    print(f"Information ratio {bt.metric.information_ratio()}")
    print(f"Sortino ratio {bt.metric.sortino_ratio( Decimal('0.03'))}")
    mdd, dds = bt.metric.maximum_drawdown()
    print(f"MDD {mdd}")

    bt.plot_nav(path="result/optimization/nav.png")
    bt.plot_drawdown(path="result/optimization/drawdown.png")
