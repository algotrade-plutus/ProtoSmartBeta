"""
Out-sample evaluation module
"""

import numpy as np
from decimal import Decimal
from config.config import BEST_CONFIG
from backtesting import create_bt_instance


if __name__ == "__main__":
    bt, grouped_data, rebalancing_dates = create_bt_instance(
        process_data=True, is_data=False
    )

    sr = bt.run(
        processed_data=grouped_data,
        execution_dates=rebalancing_dates,
        pe=BEST_CONFIG["pe"],
        dy=BEST_CONFIG["dy"],
    )

    print(f"Sharpe ratio {sr}")
    print(f"Information ratio {bt.metric.information_ratio()}")
    print(
        f"Sortino ratio {bt.metric.sortino_ratio( Decimal('0.00023')) * Decimal(np.sqrt(250))}"
    )
    mdd, dds = bt.metric.maximum_drawdown()
    print(f"MDD {mdd}")

    bt.plot_nav(path="result/optimization/nav.png")
    bt.plot_drawdown(path="result/optimization/drawdown.png")
