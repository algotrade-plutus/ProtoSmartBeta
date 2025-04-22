import matplotlib.pyplot as plt
import pandas as pd
import math


def plot_portfolio_allocation(log):
    all_assets = set()
    dates = []

    # Collect all possible asset names
    for entry in log:
        all_assets.update(entry["holdings"].keys())
        dates.append(entry["date"])

    top_components_list = []
    cash_list = []

    for entry in log:
        holdings = entry["holdings"]
        cash = entry["cash_remaining"]

        # Sort holdings by value
        sorted_holdings = sorted(holdings.items(), key=lambda x: x[1], reverse=True)

        top5 = dict(sorted_holdings[:5])
        others = sum(v for _, v in sorted_holdings[5:])

        comp = {k: v for k, v in top5.items()}
        comp['Others'] = others
        top_components_list.append(comp)
        cash_list.append(cash)

    # Convert to DataFrame
    df = pd.DataFrame(top_components_list).fillna(0)
    df['Cash'] = cash_list
    df['date'] = dates
    df.set_index('date', inplace=True)

    # Plot
    df.plot(kind='bar', stacked=True, figsize=(14, 6), colormap='tab20')
    plt.ylabel("Value ($)")
    plt.title("Portfolio Composition at Rebalancing (Top 5 Holdings, Others, Cash)")
    plt.xticks(rotation=45)
    plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    plt.tight_layout()
    plt.grid(axis='y')
    plt.show()
