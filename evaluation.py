"""
Out-sample evaluation module
"""

import numpy as np
import pandas as pd
from decimal import Decimal
from config.config import BEST_CONFIG
from metrics.metric import get_returns
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
    print(f"Information ratio {bt.metric.information_ratio() * Decimal(np.sqrt(250))}")
    print(
        f"Sortino ratio {bt.metric.sortino_ratio( Decimal('0.00023')) * Decimal(np.sqrt(250))}"
    )
    mdd, dds = bt.metric.maximum_drawdown()
    print(f"MDD {mdd}")

    monthly_df = pd.DataFrame(bt.monthly_tracking, columns=["date", "asset"])
    monthly_df_index = bt.vnindex_data[
        bt.vnindex_data["date"].isin(monthly_df["date"])
    ].copy()
    returns = get_returns(monthly_df, monthly_df_index)

    print(f"HPR {bt.metric.hpr()}")
    print(f"Excess HPR {bt.metric.excess_hpr()} ")
    print(f"Monthly return {returns['monthly_return']}")
    print(f"Excess monthly return {returns['excess_monthly_return']}")
    print(f"Annual return {returns['annual_return']}")

    bt.plot_hpr(path="result/optimization/hpr.svg")
    bt.plot_drawdown(path="result/optimization/drawdown.svg")
