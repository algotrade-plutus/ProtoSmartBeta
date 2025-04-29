"""
Optimization module
"""

import logging
import optuna
from optuna.samplers import TPESampler
from config.config import OPTIMIZATION_CONFIG

from backtesting import create_bt_instance


class OptunaCallBack:
    """
    Optuna call back class
    """

    def __init__(self) -> None:
        """
        Init optuna callback
        """
        logging.basicConfig(
            filename="result/optimization/optimization.log.csv",
            format="%(message)s",
            filemode="w",
        )
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        self.logger.info("number,pelb,peub,dylb,dyub")

    def __call__(self, _: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> None:
        """

        Args:
            study (optuna.study.Study): _description_
            trial (optuna.trial.FrozenTrial): _description_
        """
        pelb = trial.params["pelb"]
        peub = trial.params["peub"]
        dylb = trial.params["dylb"]
        dyub = trial.params["dyub"]
        self.logger.info(
            "%s,%s,%s,%s,%s,%s",
            trial.number,
            pelb,
            peub,
            dylb,
            dyub,
            trial.value,
        )


if __name__ == "__main__":
    smart_beta, grouped_data, rebalancing_dates = create_bt_instance()

    def objective(trial):
        """
        Sharpe ratio objective function

        Args:
            trial (_type_): _description_

        Returns:
            _type_: _description_
        """
        pelb = trial.suggest_float(
            "pelb", OPTIMIZATION_CONFIG["pe_low"][0], OPTIMIZATION_CONFIG["pe_low"][1]
        )
        peub = trial.suggest_float(
            "peub", OPTIMIZATION_CONFIG["pe_high"][0], OPTIMIZATION_CONFIG["pe_high"][1]
        )
        dylb = trial.suggest_float(
            "dylb", OPTIMIZATION_CONFIG["dy_low"][0], OPTIMIZATION_CONFIG["dy_low"][1]
        )
        dyub = trial.suggest_float(
            "dyub", OPTIMIZATION_CONFIG["dy_high"][0], OPTIMIZATION_CONFIG["dy_high"][1]
        )

        return smart_beta.run(
            grouped_data, rebalancing_dates, [pelb, peub], [dylb, dyub]
        )

    optunaCallBack = OptunaCallBack()
    # TODO: correct the seed to get input from the parameter/optimization_parameter.json
    study = optuna.create_study(sampler=TPESampler(seed=2024), direction="maximize")
    study.optimize(
        objective, n_trials=OPTIMIZATION_CONFIG["no_trials"], callbacks=[optunaCallBack]
    )
