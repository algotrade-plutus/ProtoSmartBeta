import logging
import optuna
from optuna.samplers import RandomSampler

import pandas as pd
from metrics import *
from backtesting import Backtesting
from utils import get_date


class OptunaCallBack:
    def __init__(self) -> None:
        logging.basicConfig(
            filename="stat/optimization.log.csv", format="%(message)s", filemode="w"
        )
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        self.logger.info(f"number,llb,lub,value")

    def __call__(
        self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial
    ) -> None:
        llb = trial.params["llb"]
        lub = llb + trial.params["delta"]
        self.logger.info(f"{trial.number},{llb},{lub},{trial.value}")


if __name__ == "__main__":
    start_date_str = "2022-01-01"
    end_date_str = "2023-01-01"
    start, from_date, to_date, end = get_date(
        start_date_str, end_date_str, look_back=252, forward_period=40
    )

    print("Fetching Data...")
    # financial_data = data_service.get_financial_data(start.year, to_date.year, INCLUDED_CODES)
    df = pd.read_csv("temp.csv")

    def objective(trial):
        pelb = trial.suggest_float("pelb", 0.0, 5.0)
        peub = trial.suggest_float("peub", 10.0, 15.0)
        dylb = trial.suggest_float("dylb", 0.01, 0.1)

    optunaCallBack = OptunaCallBack()
    study = optuna.create_study(sampler=RandomSampler(seed=2024), direction="maximize")
    study.optimize(
        objective, n_trials=optimization_params["no_trials"], callbacks=[optunaCallBack]
    )
