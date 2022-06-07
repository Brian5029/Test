import pandas as pd
from datetime import datetime
from datetime import timedelta


def no_dupe_trade(dataframe):
    seen_dates={}
    new_trade = pd.DataFrame(columns = ['QUOTE_DATE','EXPIRE_DATE','LAST_PRICE','DTE','STRIKE','P_ASK','P_BID',
                                        'P_DELTA','P_GAMMA','P_VEGA','P_THETA','P_VOLUME','P_IV'])
    for i in range(len(dataframe)):
        expire_date = dataframe['EXPIRE_DATE'][i]
        strike_value = dataframe['STRIKE'][i]
        if expire_date not in seen_dates.keys():
            seen_dates[expire_date] = [strike_value, ]
            trade_row = dataframe.iloc[[i]]
            new_trade = pd.concat([new_trade, trade_row])
        else:
            if strike_value not in seen_dates[expire_date]:
                seen_dates[expire_date].append(strike_value)
                trade_row = dataframe.iloc[[i]]
                new_trade = pd.concat([new_trade, trade_row])
    new_trade = new_trade.reset_index(drop=True)
    return new_trade


def add_days_to_date(original_date, days_added):
    output = datetime.strptime(original_date, '%Y-%m-%d')
    output = output + timedelta(days = days_added)
    # date_string = datetime.strftime(output, '%Y-%m-%d') return date_string for string
    return output