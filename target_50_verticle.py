import pandas as pd
from datetime import datetime
import utils


def target_50_verticle(no_dupe_trade, full_data_trade, date_list_datetime, raw_put_df):
    my_verticle = []
    for i in range(len(no_dupe_trade)):
        latest_expire = no_dupe_trade.iloc[[i]]['EXPIRE_DATE'].tolist()[0]
        latest_quote_date = no_dupe_trade.iloc[[i]]['QUOTE_DATE'].tolist()[0]
        latest_dte = no_dupe_trade.iloc[[i]]['DTE'].tolist()[0]
        f_trade_df = raw_put_df.loc[
            (raw_put_df['EXPIRE_DATE'] == latest_expire) & (raw_put_df['QUOTE_DATE'] == latest_quote_date) & (
                        raw_put_df['DTE'] <= latest_dte)]
        f_trade_df = f_trade_df.loc[f_trade_df['PROB_ITM'] <= no_dupe_trade['PROB_ITM'][i]].sort_values(by='PROB_ITM',
                                                                                                   ascending=False)
        f_trade_df = f_trade_df.reset_index(drop=True)
        my_verticle.append(f_trade_df)

    made_trade_verticle = pd.DataFrame(
        columns=['SOLD_STRIKE', 'BOUGHT_STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE',
                 'EXIT_LAST_PRICE', 'EXPIRE_DATE', 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT',
                 'PROFIT_PERCENT'])
    loss_trade_verticle = pd.DataFrame(
        columns=['SOLD_STRIKE', 'BOUGHT_STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE',
                 'EXIT_LAST_PRICE', 'EXPIRE_DATE', 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT', 'PROFIT_PERCENT'])
    optimized_spread_list = [] # this can be returned also for data study collection
    next_closest_trade = my_verticle[0]['QUOTE_DATE'][0] # for line 93, first loop should be equal and then value changes

    for trade in range(len(my_verticle)):
        spread = my_verticle[trade]
        if len(spread) == 1:
            continue
        if ((spread['STRIKE'][0]) - (spread['STRIKE'].tail(1).tolist()[0])) < 5:
            continue
        optimized_spread = pd.DataFrame(
            columns=['QUOTE_DATE', 'DTE', 'EXPIRE_DATE', 'STRIKE', 'WIDTH', 'NET_CREDIT', 'BUYING_POWER', 'POP_%',
                     'ROC', 'MARGINAL_COST'])
        # creates a dataframe that gives optimal trade width
        for i in range(1, len(spread)):
            width = spread['STRIKE'][0] - spread['STRIKE'][i]
            credit = ((spread['P_ASK'][0] + spread['P_BID'][0]) / 2).round(2)
            bought = ((spread['P_ASK'][i] + spread['P_BID'][i]) / 2).round(2)
            net_credit = credit - bought
            buying_power = (width - net_credit).round(2)
            roc = (net_credit / buying_power).round(3)
            pop = ((((net_credit / width) * 100) - 100) * -1).round(3)

            narrow_width = spread['STRIKE'][0] - spread['STRIKE'][i - 1]
            narrow_bought = ((spread['P_ASK'][i - 1] + spread['P_BID'][i - 1]) / 2).round(2)
            narrow_net_credit = credit - narrow_bought
            narrow_buying_power = (narrow_width - narrow_net_credit).round(2)
            if (narrow_buying_power != 0) & (narrow_net_credit != 0):
                narrow_roc = (narrow_net_credit / narrow_buying_power).round(3)
                marginal_cost = roc / narrow_roc
            else:
                marginal_cost = 0

            single_optimized_spread = pd.DataFrame([{'QUOTE_DATE': spread['QUOTE_DATE'][i],
                                                        'DTE': spread['DTE'][i],
                                                        'EXPIRE_DATE': spread['EXPIRE_DATE'][i],
                                                        'STRIKE': spread['STRIKE'][i],
                                                        'WIDTH': width,
                                                        'NET_CREDIT': net_credit,
                                                        'BUYING_POWER': buying_power,
                                                        'ROC': roc,
                                                        'POP_%': pop,
                                                        'MARGINAL_COST': marginal_cost}])
            optimized_spread = pd.concat([optimized_spread, single_optimized_spread])
            optimized_spread = optimized_spread.reset_index(drop = True)
        optimized_spread_list.append(optimized_spread)

        # filters the data between width 5-10 and finds the highest margin cost value
        highest_margin_cost = max(optimized_spread.loc[optimized_spread['WIDTH'].between(5, 10)]['MARGINAL_COST'])
        highest_margin_strike = optimized_spread.loc[optimized_spread['MARGINAL_COST'] == highest_margin_cost]['STRIKE'].tolist()[0]

        sold = spread.iloc[[0]]
        latest_expire_sold = sold['EXPIRE_DATE'].tolist()[0]
        latest_strike_sold = sold['STRIKE'].tolist()[0]
        latest_dte_sold = sold['DTE'].tolist()[0]
        sold_df = raw_put_df.loc[
            (raw_put_df['EXPIRE_DATE'] == latest_expire_sold) & (raw_put_df['STRIKE'] == latest_strike_sold) & (
                        raw_put_df['DTE'] <= latest_dte_sold)]
        sold_df = sold_df.reset_index(drop=True)

        bought = spread.loc[spread['STRIKE'] == highest_margin_strike]
        latest_expire_bought = bought['EXPIRE_DATE'].tolist()[0]
        latest_strike_bought = bought['STRIKE'].tolist()[0]
        latest_dte_bought = bought['DTE'].tolist()[0]
        bought_df = raw_put_df.loc[
            (raw_put_df['EXPIRE_DATE'] == latest_expire_bought) & (raw_put_df['STRIKE'] == latest_strike_bought) & (
                        raw_put_df['DTE'] <= latest_dte_bought)]
        bought_df = bought_df.reset_index(drop=True)

        if next_closest_trade == sold_df['QUOTE_DATE'][0]:
            win_percent = []
            profit_list = []
            buy_back = []
            for row in range(len(sold_df)):
                buy_ask = bought_df['P_ASK'][row]
                buy_bid = bought_df['P_BID'][row]

                sell_ask = sold_df['P_ASK'][row]
                sell_bid = sold_df['P_BID'][row]

                buy_mid = (buy_ask + buy_bid) / 2
                sell_mid = (sell_ask + sell_bid) / 2

                initial_credit = ((sold_df['P_ASK'][0] + sold_df['P_BID'][0]) / 2) - (
                            (bought_df['P_ASK'][0] + bought_df['P_BID'][0]) / 2)
                exit_buy_back = (buy_mid - sell_mid).round(2)

                profit = (initial_credit + exit_buy_back).round(2)
                profit_percentage = (profit / initial_credit) * 100

                buy_back.append(exit_buy_back)
                win_percent.append(profit_percentage)
                profit_list.append(profit)

            boolean_list = [True if x >= 50 else False for x in win_percent]
            if True in boolean_list:
                # first_true_index very important
                first_true_index = boolean_list.index(True)

                exit_date = datetime.strptime(sold_df['QUOTE_DATE'][first_true_index], '%Y-%m-%d')
                if exit_date > date_list_datetime[-1]:
                    break
                next_closest_trade = min([y for y in date_list_datetime if y >= exit_date],
                                         key=lambda j: abs(j - exit_date))
                next_closest_trade = next_closest_trade.strftime('%Y-%m-%d')

                single_made_trade_verticle = pd.DataFrame([{'SOLD_STRIKE': sold_df['STRIKE'][0],
                                                            'BOUGHT_STRIKE': bought_df['STRIKE'][0],
                                                            'TRADE_DATE': sold_df['QUOTE_DATE'][0],
                                                            'TRADE_LAST_PRICE': sold_df['LAST_PRICE'][0],
                                                            'EXIT_DATE': sold_df['QUOTE_DATE'][first_true_index],
                                                            'EXIT_LAST_PRICE': sold_df['QUOTE_DATE'][first_true_index],
                                                            'EXPIRE_DATE': sold_df['EXPIRE_DATE'][0],
                                                            'DTE': sold_df['DTE'][0],
                                                            'AMOUNT_REC': initial_credit,
                                                            'AMOUNT_BUYBACK': buy_back[first_true_index],
                                                            'PROFIT': profit_list[first_true_index],
                                                            'PROFIT_PERCENT': win_percent[first_true_index]}])
                made_trade_verticle = pd.concat([made_trade_verticle, single_made_trade_verticle])
                made_trade_verticle = made_trade_verticle.reset_index(drop=True)

            else:
                current_date = sold_df['QUOTE_DATE'][0]
                dte = sold_df['DTE'][0]
                exit_date = utils.add_days_to_date(current_date, dte)
                if exit_date > date_list_datetime[-1]:
                    break
                next_closest_trade = min([y for y in date_list_datetime if y >= exit_date],
                                         key=lambda j: abs(j - exit_date))
                next_closest_trade = next_closest_trade.strftime('%Y-%m-%d')

                single_made_trade_verticle = pd.DataFrame([{'SOLD_STRIKE': sold_df['STRIKE'][0],
                                                            'BOUGHT_STRIKE': bought_df['STRIKE'][0],
                                                            'TRADE_DATE': sold_df['QUOTE_DATE'][0],
                                                            'TRADE_LAST_PRICE': sold_df['LAST_PRICE'][0],
                                                            'EXIT_DATE': sold_df['QUOTE_DATE'].tail(1).tolist()[0],
                                                            'EXIT_LAST_PRICE': sold_df['QUOTE_DATE'].tail(1).tolist()[
                                                                0],
                                                            'EXPIRE_DATE': sold_df['EXPIRE_DATE'][0],
                                                            'DTE': sold_df['DTE'][0],
                                                            'AMOUNT_REC': initial_credit,
                                                            'AMOUNT_BUYBACK': exit_buy_back,
                                                            'PROFIT': profit,
                                                            'PROFIT_PERCENT': profit_percentage}])
                made_trade_verticle = pd.concat([made_trade_verticle, single_made_trade_verticle])
                made_trade_verticle = made_trade_verticle.reset_index(drop=True)

    for index in range(len(made_trade_verticle)):
        if made_trade_verticle['PROFIT'][index] < 0:
            single_loss_trade_verticle = made_trade_verticle.iloc[[index]]
            loss_trade_verticle = pd.concat([loss_trade_verticle, single_loss_trade_verticle])
            loss_trade_verticle = loss_trade_verticle.reset_index(drop=True)

    output = dict()
    output['made_trade_verticle'] = made_trade_verticle
    output['loss_trade_verticle'] = loss_trade_verticle
    return output

