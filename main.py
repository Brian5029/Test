import pandas as pd
from datetime import datetime

desired_width=32
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns',15)


raw_put_df = pd.read_csv('C:/Users/bkim5/Desktop/Options data/aapl_put_df_2017_2020/aapl_put_df_2017_2020.csv')

min_user_prob_itm = int(input('Desired minimum prob. ITM percentage: '))
max_user_prob_itm = int(input('Desired maximum prob. ITM percentage: '))
min_user_dte = int(input('Desired minimum DTE: '))
max_user_dte = int(input('Desired maximum DTE: '))

# The code below will find the trade that meet the users criteria and put it in a dataframe
my_trade_condition_df = pd.DataFrame()
for rows in range(len(raw_put_df)):
    if (min_user_prob_itm <= raw_put_df['PROB_ITM'][rows] <= max_user_prob_itm) and (min_user_dte <= raw_put_df['DTE'][rows] <= max_user_dte):
        trade_row = (raw_put_df.iloc[[rows]])
        my_trade_condition_df = pd.concat([my_trade_condition_df,trade_row])
my_trade_condition_df = my_trade_condition_df.reset_index(drop=True)

import utils
no_dupe_trade = utils.no_dupe_trade(my_trade_condition_df)

# creating a dataframe with first data being the value of no_dupe_trade all the way through 0 or 1 DTE
full_data_trade = []
partial_data_trade = []
for i in range(len(no_dupe_trade)):
    latest_expire = no_dupe_trade.iloc[[i]]['EXPIRE_DATE'].tolist()[0]
    latest_strike = no_dupe_trade.iloc[[i]]['STRIKE'].tolist()[0]
    latest_dte = no_dupe_trade.iloc[[i]]['DTE'].tolist()[0]
    trade_df = raw_put_df.loc[(raw_put_df['EXPIRE_DATE'] == latest_expire) & (raw_put_df['DTE'] <= latest_dte) & (raw_put_df['STRIKE'] == latest_strike)]
    trade_df = trade_df.reset_index(drop=True)
    if (trade_df['DTE'].tail(1).tolist()[0] == 0) or (trade_df['DTE'].tail(1).tolist()[0] == 1) or (trade_df['DTE'].tail(1).tolist()[0] == 2):
        full_data_trade.append(trade_df)
    else:
        partial_data_trade.append(trade_df)

for i in range(len(no_dupe_trade)):
    for rows in range(len(partial_data_trade)):
        each_df = partial_data_trade[rows]
        no_dupe_trade = no_dupe_trade.drop(no_dupe_trade.loc[no_dupe_trade['QUOTE_DATE'] == each_df['QUOTE_DATE'][0]].index)
        no_dupe_trade = no_dupe_trade.reset_index(drop = True)

no_dupe_trade['QUOTE_DATE'] = no_dupe_trade['QUOTE_DATE'].str.strip()
date_list_string = no_dupe_trade['QUOTE_DATE'].tolist()

date_list_datetime = []
for date in range(len(date_list_string)):
    dates = datetime.strptime(date_list_string[date], '%Y-%m-%d')
    date_list_datetime.append(dates)


#import till_dte_naked
#output = till_dte_naked.untill_dte_naked(full_data_trade, date_list_datetime)
#print(output['made_trade'])

#import target_50_naked
#output = target_50_naked.target_50_naked(full_data_trade, date_list_datetime)
#print(output['made_trade_naked'])

import target_50_verticle
output = target_50_verticle.target_50_verticle(no_dupe_trade, full_data_trade, date_list_datetime, raw_put_df)
print(output['made_trade_verticle'])

