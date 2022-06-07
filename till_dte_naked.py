import pandas as pd
import utils


def untill_dte_naked(full_data_trade, date_list_datetime):
    made_trade = pd.DataFrame(columns=['STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE', 'EXIT_LAST_PRICE',
                                       'EXPIRE_DATE', 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT_PERCENT', 'PROFIT'])
    loss_trade = pd.DataFrame(columns=['STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE', 'EXIT_LAST_PRICE',
                                       'EXPIRE_DATE', 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT_PERCENT', 'PROFIT'])
    next_closest_trade_string = full_data_trade[0]['QUOTE_DATE'][0]

    for i in range(len(full_data_trade)):
        each_df = full_data_trade[i]
        if next_closest_trade_string == each_df['QUOTE_DATE'][0]:
            amount_received = ((each_df['P_ASK'][0] + each_df['P_BID'][0]) / 2)
            amount_buyback = ((each_df['P_ASK'].tail(1).tolist()[0] + each_df['P_BID'].tail(1).tolist()[0]) / 2)
            profit = (amount_received - amount_buyback).round(3)
            profit_percent = (((amount_received - amount_buyback).round(3)) / amount_received) * 100

            next_date = each_df['QUOTE_DATE'][0]
            dte = each_df['DTE'][0]
            date_expired = utils.add_days_to_date(next_date, dte)
            if date_expired > date_list_datetime[-1]:
                break

            next_closest_trade_compare = min([y for y in date_list_datetime if y >= date_expired], key=lambda j: abs(j-date_expired))
            next_closest_trade_string = next_closest_trade_compare.strftime('%Y-%m-%d')

            single_made_trade = pd.DataFrame([{'TRADE_DATE': each_df['QUOTE_DATE'][0],
                                               'TRADE_LAST_PRICE': each_df['LAST_PRICE'][0],
                                               'EXIT_DATE': each_df['QUOTE_DATE'].tail(1).tolist()[0],
                                               'EXIT_LAST_PRICE': each_df['LAST_PRICE'].tail(1).tolist()[0],
                                               'STRIKE': each_df['STRIKE'][0],
                                               'EXPIRE_DATE': each_df['EXPIRE_DATE'][0],
                                               'DTE': each_df['DTE'][0],
                                               'AMOUNT_REC': amount_received,
                                               'AMOUNT_BUYBACK': amount_buyback,
                                               'PROFIT_PERCENT': profit_percent,
                                               'PROFIT': profit}])
            made_trade = pd.concat([made_trade, single_made_trade])
            made_trade = made_trade.reset_index(drop=True)

    for index in range(len(made_trade)):
        if made_trade['PROFIT'][index] < 0:
            single_loss_trade = made_trade.iloc[[index]]
            loss_trade = pd.concat([loss_trade, single_loss_trade])
            loss_trade = loss_trade.reset_index(drop=True)
    output = dict()
    output['made_trade'] = made_trade
    output['loss_trade'] = loss_trade
    return output
