import pandas as pd
from datetime import datetime
import utils


def target_50_naked(full_data_trade, date_list_datetime):
    made_trade_naked = pd.DataFrame(
        columns=['STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE', 'EXIT_LAST_PRICE', 'EXPIRE_DATE',
                 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT_PERCENT', 'PROFIT'])
    loss_trade_naked = pd.DataFrame(
        columns=['STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE', 'EXIT_LAST_PRICE', 'EXPIRE_DATE',
                 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT_PERCENT', 'PROFIT'])
    next_closest_trade = full_data_trade[0]['QUOTE_DATE'][0] # for line 18
    exit_date = [] # for line 40

    for df_index in range(len(full_data_trade)):
        each_df = full_data_trade[df_index]
        # if the next closest date is equal to the first date of the df, first date of the df has to be equal to each_df
        # since that same date is contained in other df too.
        if next_closest_trade == each_df['QUOTE_DATE'][0]:
            win_percent = []
            amount_buyback_list = []
            profit_list = []
            # looping through each df in my_df and calculating values
            for rows in range(len(each_df)):
                amount_received = ((each_df['P_ASK'][0] + each_df['P_BID'][0]) / 2).round(3)
                current_p_ask = each_df['P_ASK'][rows]
                current_p_bid = each_df['P_BID'][rows]
                amount_buyback = ((current_p_ask + current_p_bid) / 2).round(3)
                profit = (amount_received - amount_buyback).round(3)
                profit_percent = (((amount_received - amount_buyback).round(3)) / amount_received) * 100

                # These are needed to find the correct index of the value that needs to be appended in the made_trade df
                amount_buyback_list.append(amount_buyback)
                win_percent.append(profit_percent)
                profit_list.append(profit)
            # This boolean list is used to find out when to exit the trade. (which FIRST index of each_df is True)
            boolean_list = [True if x >= 50 else False for x in win_percent]
            if True in boolean_list:
                # Finds the first index of where each_df is true meaning that index has all the exit values.
                first_true_index = boolean_list.index(True)
                exit_date.append(each_df['QUOTE_DATE'][first_true_index])

                next_date = datetime.strptime(each_df['QUOTE_DATE'][first_true_index], '%Y-%m-%d')
                if next_date > date_list_datetime[-1]:
                    break
                next_closest_trade = min([y for y in date_list_datetime if y >= next_date],
                                         key=lambda j: abs(j - next_date))
                next_closest_trade = next_closest_trade.strftime('%Y-%m-%d')

                single_made_trade_naked = pd.DataFrame([{'TRADE_DATE': each_df['QUOTE_DATE'][0],
                                                         'TRADE_LAST_PRICE': each_df['LAST_PRICE'][0],
                                                         'EXIT_DATE': each_df['QUOTE_DATE'][first_true_index],
                                                         'EXIT_LAST_PRICE': each_df['LAST_PRICE'][first_true_index],
                                                         'STRIKE': each_df['STRIKE'][0],
                                                         'EXPIRE_DATE': each_df['EXPIRE_DATE'][0],
                                                         'DTE': each_df['DTE'][0],
                                                         'AMOUNT_REC': amount_received, # warning can be ignored since amount_received is always going to be the first index of the df
                                                         'AMOUNT_BUYBACK': amount_buyback_list[first_true_index],
                                                         'PROFIT_PERCENT': win_percent[first_true_index],
                                                         'PROFIT': profit_list[
                                                             first_true_index]}])  # we use first_true_index of the win_percent because that index is when we exited the trade
                made_trade_naked = pd.concat([made_trade_naked, single_made_trade_naked])
                made_trade_naked = made_trade_naked.reset_index(drop=True)

            else:
                next_date = each_df['QUOTE_DATE'][0]
                dte = each_df['DTE'][0]
                date_expired = utils.add_days_to_date(next_date, dte)
                if date_expired > date_list_datetime[-1]:
                    break
                next_closest_trade = min([y for y in date_list_datetime if y >= date_expired],
                                         key=lambda j: abs(j - date_expired))
                next_closest_trade = next_closest_trade.strftime('%Y-%m-%d')

                single_made_trade_naked = pd.DataFrame([{'TRADE_DATE': each_df['QUOTE_DATE'][0],
                                                         'TRADE_LAST_PRICE': each_df['LAST_PRICE'][0],
                                                         'EXIT_DATE': each_df['QUOTE_DATE'].tail(1).tolist()[0],
                                                         'EXIT_LAST_PRICE': each_df['LAST_PRICE'].tail(1).tolist()[0],
                                                         'STRIKE': each_df['STRIKE'][0],
                                                         'EXPIRE_DATE': each_df['EXPIRE_DATE'][0],
                                                         'DTE': each_df['DTE'][0],
                                                         'AMOUNT_REC': amount_received,
                                                         'AMOUNT_BUYBACK': amount_buyback,   # warning is not valid because we need the last iterated value
                                                         'PROFIT_PERCENT': profit_percent,   # of the varible since these are lost trade meaning the the last row.
                                                         'PROFIT': profit}])                 # of the df is what we need
                made_trade_naked = pd.concat([made_trade_naked, single_made_trade_naked])
                made_trade_naked = made_trade_naked.reset_index(drop=True)

    for index in range(len(made_trade_naked)):
        if made_trade_naked['PROFIT'][index] < 0:
            single_loss_trade = made_trade_naked.iloc[[index]]
            loss_trade_naked = pd.concat([loss_trade_naked, single_loss_trade])
            loss_trade_naked = loss_trade_naked.reset_index(drop = True)

    output = dict()
    output['made_trade_naked'] = made_trade_naked
    output['loss_trade_naked'] = loss_trade_naked
    return output
