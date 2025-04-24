import logging
from decimal import Decimal
import optuna
from optuna.samplers import TPESampler
from config.config import backtesting_config, optimization_config

import pandas as pd
from metrics import *
from backtesting import Backtesting
from utils import get_date


class OptunaCallBack:
    def __init__(self) -> None:
        logging.basicConfig(
            filename="result/optimization/optimization.log",
            format="%(message)s",
            filemode="w",
        )
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        self.logger.info(f"number,pelb,peub,dylb,dyub")

    def __call__(
        self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial
    ) -> None:
        pelb = trial.params["pelb"]
        peub = trial.params["peub"]
        dylb = trial.params["dylb"]
        dyub = trial.params["dyub"]
        self.logger.info(f"{trial.number},{pelb},{peub},{dylb},{dyub},{trial.value}")


if __name__ == "__main__":
    start_date_str = backtesting_config["is_from_date_str"]
    end_date_str = backtesting_config["is_end_date_str"]

    smart_beta = Backtesting(
        buy_fee=Decimal(backtesting_config["buy_fee"]),
        sell_fee=Decimal(backtesting_config["sell_fee"]),
        from_date_str=start_date_str,
        to_date_str=end_date_str,
        capital=Decimal(backtesting_config["capital"]),
    )
    grouped_data, rebalancing_dates = smart_beta.process_data()

    def objective(trial):
        pelb = trial.suggest_float(
            "pelb", optimization_config["pe_low"][0], optimization_config["pe_low"][1]
        )
        peub = trial.suggest_float(
            "peub", optimization_config["pe_high"][0], optimization_config["pe_high"][1]
        )
        dylb = trial.suggest_float(
            "dylb", optimization_config["dy_low"][0], optimization_config["dy_low"][1]
        )
        dyub = trial.suggest_float(
            "dyub", optimization_config["dy_high"][0], optimization_config["dy_high"][1]
        )

        return smart_beta.run(
            grouped_data, rebalancing_dates, [pelb, peub], [dylb, dyub]
        )

    optunaCallBack = OptunaCallBack()
    study = optuna.create_study(sampler=TPESampler(seed=2024), direction="maximize")
    study.optimize(
        objective, n_trials=optimization_config["no_trials"], callbacks=[optunaCallBack]
    )
