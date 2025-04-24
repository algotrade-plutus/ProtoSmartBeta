from typing import List
import numpy as np


class Metric:
    def __init__(self, period_returns: List[float], benchmark_returns: List[float]):
        self.period_returns = period_returns
        self.benchmark_returns = benchmark_returns

    def sharpe_ratio(self, risk_free_return):
        if not self.period_returns:
            raise ValueError('Annual returns should not be None or empty')

        # Calculate excess returns
        excess_returns = [
            period_return - risk_free_return for period_return in self.period_returns
        ]

        return np.mean(excess_returns) / np.std(self.period_returns, ddof=1)

    def sortino_ratio(self, risk_free_return: float) -> float:
        if not self.period_returns:
            raise ValueError('Annual returns should not be None or empty')

        downside_returns = [
            min(0, period_return - risk_free_return)
            for period_return in self.period_returns
        ]
        downside_risk = np.sqrt(np.mean([d_r**2 for d_r in downside_returns]))

        return (np.mean(self.period_returns) - risk_free_return) / downside_risk

    def maximum_drawdown(self):
        dds = []
        if not self.period_returns:
            raise ValueError('Invalid Input')

        if any(period_return <= -1 for period_return in self.period_returns):
            raise ValueError('Invalid Input')

        peak = 1
        cur_perf = 1
        mdd = 0
        for period_return in self.period_returns:
            cur_perf *= 1 + period_return
            if cur_perf > peak:
                peak = cur_perf

            dd = cur_perf / peak - 1
            dds.append(dd)
            if dd < mdd:
                mdd = dd

        return mdd, dds

    def longest_drawdown(self):
        if not self.period_returns:
            raise ValueError('Invalid Input')

        if any(period_return <= -1 for period_return in self.period_returns):
            raise ValueError('Invalid Input')

        cur_period = 0
        max_period = 0
        peak = 1
        cur_perf = 1
        for period_return in self.period_returns:
            cur_perf *= 1 + period_return

            if cur_perf > peak:
                cur_period = 0
                peak = cur_perf
                continue

            cur_period += 1
            if cur_period > max_period:
                max_period = cur_period

        return max_period

    def information_ratio(self):
        if not self.period_returns or not self.benchmark_returns:
            raise ValueError("Invalid Input")

        if len(self.period_returns) != len(self.benchmark_returns):
            raise ValueError(
                f"Not equal length {len(self.period_returns)} - {len(self.benchmark_returns)}"
            )

        if any(period_return <= -1 for period_return in self.period_returns) or any(
            benchmark_return <= -1 for benchmark_return in self.benchmark_returns
        ):
            raise ValueError("Invalid Input")

        if len(self.period_returns) == 1 or len(self.benchmark_returns) == 1:
            raise ValueError("Invalid length")

        mean_period_returns = np.array(self.period_returns).mean()
        mean_benchmark_returns = np.array(self.benchmark_returns).mean()

        if mean_period_returns == mean_benchmark_returns:
            return 0

        excess_returns = np.array(self.period_returns) - np.array(
            self.benchmark_returns
        )

        return (mean_period_returns - mean_benchmark_returns) / excess_returns.std()
