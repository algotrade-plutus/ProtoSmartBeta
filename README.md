# PE and Devidend Yeild
> Select stocks based on P/E and Devidend Yeild

## Abstract
In this project, we use the P/E ratio and dividend yield to select and hold stocks in the Vietnamese stock market. The portfolio is rebalanced on the first day of each month; if that day is a holiday, rebalancing is carried out on the next trading day.

## Introduction
In value investing, one common approach to stock selection involves identifying undervalued companies with strong income potential. This strategy leverages two key financial metrics: the Price-to-Earnings (P/E) ratio and the dividend yield. The P/E ratio helps assess whether a stock is trading at a reasonable price relative to its earnings, while the dividend yield highlights its income-generating potential.

The core idea is to select stocks with a low P/E ratio and a high dividend yield, as these stocks may represent undervalued opportunities that also offer steady cash returns. This method is particularly effective in mature or stable markets, such as the Vietnamese stock market, where dividend-paying companies are often more established and financially sound.

## Hypothesis
We filter and hold a collection of stocks with a P/E ratio in the range (0, 15) and a dividend per share (DPS) greater than 0.01. Existing holdings are sold before purchasing new stocks at each rebalancing period.

## Data
- Data source: Algotrade database
- Data period: from 2022-01-01 to 2025-01-01
- Financial and closing price data are extracted and stored in a .csv file to reduce the time required for subsequent actions.
- Each sell or buy side will be charge 0.035% fee.
### Data collection
#### Daily closing price data
- The daily close price is collected from Algotrade database using SQL queries. 
- The data is collected using the script `data_loader.py` 
- The data is stored in the `/temp.csv` file. 

#### Financial data
- P/E and DPS are calculated based on:
    - Net Profit After Tax Atributed To Shareholder
    - Outstanding share
    - Dividends paid
- The data is also collected using the `data_loader.py` file.

## Implementation
### Environment Setup
1. Set up python virtual environment
```bash
python -m venv venv
source venv/bin/activate # for Linux/MacOS
.\venv\Scripts\activate.bat # for Windows command line
.\venv\Scripts\Activate.ps1 # for Windows PowerShell
```
2. Install the required packages
```bash
pip install -r requirements.txt
```
3. (OPTIONAL) Create `.env` file in the root directory of the project and fill in the required information. The `.env` file is used to store environment variables that are used in the project. The following is an example of a `.env` file:
```env
DB_NAME=<database name>
DB_USER=<database user name>
DB_PASSWORD=<database password>
DB_HOST=<host name or IP address>
DB_PORT=<database port>
```

### Data Collection
#### Option 1. Download from Google Drive
Data can be download directly from [Google Drive](https://drive.google.com/drive/folders/1kdCQ7sQJIKiBMWDF37x5PflQ2gAejmDs?usp=sharing).
- The data files are stored in the `data` folder with the following folder structure:
```
data
└── pe_dps.csv
```
- You should place this folder to the current ```PYTHONPATH``` for the following steps.
#### Option 2. Run codes to collect data
1. Collect data from database
In the root directory of the project, run the following command. The process will take about 7-10 minutes to finish.
```bash
python data_loader.py
```
The result will be stored in the `data/pe_dps.csv`
### In-sample Backtesting
- To init parameters for the first run, access `config/config.yaml` file and adjust the `default_backtest_params`.
- For this project, we use data of the period from 2023-02-01 to 2024-01-31 as the in-sample period. These can be adjusted in `config/config.yaml`.
- `--name` argument must match the configuration name in `config/config.yaml` file, where each name has `start_date` and `end_date` parameters. The default name is `in_sample`. This name will also be used to save in the result folder.
```bash
python -m src.backtest --name in_sample
```
The result will be stored in the `result/backtest/in_sample` folder.

### Optimization
Run this command to start the optimization process. You can adjust the random seed by editing `random_seed` in the `config/config.yaml` file. The default random seed is 42.
```bash
python -m src.optimize --n_trials 5000 
```
The optimization result will be stored in the `optimization` folder. And the optimized in-sample backtest result will be stored in the `backtest/optimized_in_sample` folder.
This process will take about 1-2 hours to finish on a standard laptop. You can skip this step by copying the [best_params.json](doc/report/optimization/best_params.json) file to the `optimization` folder.

After that, you can run the in-sample backtesting process again with the optimized parameters. 
```bash
python src.backtest --name optimized_in_sample
```
The result will be stored in the `result/backtest/optimized_in_sample` folder.

### Out-of-sample Backtesting
Run this command to start the out-of-sample backtesting process.
```bash
python -m src.backtest --name out_sample
```
The result will be stored in the `result/backtest/out_sample` folder.

### Configurations
## In-sample Backtesting
### Evaluation Metrics
- Backtesting results are stored in the `result/backtest/` folder. 
- Used metrics to compare with VNINDEX are: 
  - Sharpe ratio (SR)
  - Sortino ratio (SoR)
  - Information ratio (Inf)
  - Maximum drawdown (MDD)
  - Longest drawdown (LDD)
### Parameters
### In-sample Backtesting Result
## Optimization
### Optimization Result
## Out-of-sample Backtesting
### Out-of-sample Backtesting Result