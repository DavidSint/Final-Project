import numpy as np
import pandas as pd
from datetime import datetime, time
from auxillary import ticker_scroll, weekdays
from functions import get, baseline, tweets, split, mape, rf, linear, linearSVR, kNearest, regressor

holiday_list = ['2018-11-22', '2018-11-23', '2018-12-05',
                '2018-12-24', '2018-12-25', '2019-01-01', '2019-01-21', '2019-02-18']  # half days are included as a holiday too
# [thanksgiving, black friday (closes 13:00), GHWB death, Xmas eve (closes 13:00), Xmas, New years day, MLK bday, Presidents day]

tweet_bin_length = '60min'
tweet_window_length = '1440min'  # 24 hours

start_date = datetime(2018, 10, 29).date()
end_date = datetime(2019, 3, 25).date()

DATA_PATH = "Data/"


while True:
    ans = input(
        "\n\n\nOPTIONS\n-------\nData: 'get', 'baseline' & 'tweets'\n\nCorrelation:'pearson', 'coors' \n\nRegression: 'rf', 'linear', 'linearSVR' or 'kNearest'\n(optional: add the n_estimators, tolerance or n_neighbors after test_size)\n\nOther: 'exit'\n\n\nWhat would you like to do?\n")
    if ans.split(' ', 1)[0] == "get":
        ticker_scroll(get)
    elif ans.split(' ', 1)[0] == 'baseline':
        ticker_scroll(baseline)
    elif ans.split(' ', 1)[0] == 'tweets':
        ticker_scroll(tweets)
    elif ans.split(' ', 1)[0] == "rf":
        try:
            test_size = float(ans.split(' ', 1)[1])
            if test_size < 0 or test_size > 1:
                test_size = 0.1
                print("Incorrect test size detected. Default of 0.1 set")
        except:
            print("No test size detected. Default of 0.1 set.")
            test_size = 0.1
        try:
            n_estimators = int(ans.split(' ', 1)[2])
            if n_estimators < 2:
                n_estimators = 1000
                print("Weird number of estimators detected. Default of 1000 set")
        except:
            print("No number of estimators detected. Default of 1000 set.")
            n_estimators = 1000
        regressor(rf, test_size, 'MAPE', n_estimators)
    elif ans.split(' ', 1)[0] == "linear":
        try:
            test_size = float(ans.split(' ', 1)[1])
            if test_size < 0 or test_size > 1:
                test_size = 0.1
                print("Incorrect test size detected. Default of 0.1 set")
        except:
            print("No test size detected. Default of 0.1 set.")
            test_size = 0.1
        regressor(linear, test_size, 'MAPE')
    elif ans.split(' ', 1)[0] == "linearSVR":
        try:
            test_size = float(ans.split(' ', 1)[1])
            if test_size < 0 or test_size > 1:
                test_size = 0.1
                print("Incorrect test size detected. Default of 0.1 set")
        except:
            print("No test size detected. Default of 0.1 set.")
            test_size = 0.1
        try:
            tol = float(ans.split(' ', 1)[2])
            if tol < 0 or tol > 1:
                tol = 1e-5
                print("Incorrect teolerance detected. Default of 1e-5 set")
        except:
            print("No tolerance detected. Default of 1e-5 set.")
            tol = 1e-5

        regressor(linearSVR, test_size, 'MAPE', tol)
    elif ans.split(' ', 1)[0] == "kNearest":
        try:
            test_size = float(ans.split(' ', 1)[1])
            if test_size < 0 or test_size > 1:
                test_size = 0.1
                print("Incorrect test size detected. Default of 0.1 set")
        except:
            print("No test size detected. Default of 0.1 set.")
            test_size = 0.1
        try:
            neigh = int(ans.split(' ', 1)[2])
            if neigh < 2:
                neigh = 3
                print("Incorrect number of neighbors detected. Default of 3 set")
        except:
            print("No number of neighbors detected. Default of 3 set.")
            neigh = 3
        regressor(kNearest, test_size, 'MAPE', neigh)

    elif ans.split(' ', 1)[0] == "pearson":
        import matplotlib.pyplot as plt
        try:
            ticker = str(ans.split(' ', 1)[1])
        except:
            print("No ticker detected. Default of AAPL set.")
            ticker = "AAPL"
        print("Processing pearson correaltion for", ticker + "...")
        try:
            tdb = pd.read_csv(DATA_PATH + ticker + " tdb.csv", index_col=0,
                              parse_dates=['timestamp'], date_parser=pd.to_datetime, engine='python')  # engine needed to be changed, as dates were causing issues.
            sdbtargeted = pd.read_csv(DATA_PATH + ticker + " stocks ftlbl.csv", index_col=0,
                                      parse_dates=[0])
        except:
            print("You must first run the 'get' and 'baseline' commands")
            break

        countdb = tdb.drop(
            ['fullname', 'replies', 'retweets', 'text', 'user'], axis=1)
        countdb = countdb.groupby(pd.Grouper(
            key='timestamp', freq=tweet_bin_length)).count()

        df = countdb.groupby(pd.Grouper(
            freq=tweet_window_length))['likes'].agg(list)
        df = pd.DataFrame(df.tolist(), index=df.index)

        # will become df, but only for weekdays
        weekdaydf = pd.DataFrame(columns=list(df))
        for i in weekdays(start_date, end_date):
            temp = str(i.date()) + " 16:00:00"

            # if the day is not a holiday, then make a line in the weekdaydf for it
            if str(pd.to_datetime(temp, infer_datetime_format=True).date()) not in holiday_list:
                # add the df row to the new weekday
                weekdaydf.loc[i] = df.loc[i]

        mergeddf = pd.concat([weekdaydf, sdbtargeted], axis=1, sort=False)

        # if targets column is empty (i.e. the API failed for that day), then delete the day, as the data is useless.
        mergeddf = mergeddf.dropna(subset=['target'])

        df = mergeddf

        from scipy import stats as st

        rhos = dict.fromkeys(range(24))
        pvals = dict.fromkeys(range(24))
        for i in range(24):
            print(df[[i]])
            rhos[i], pvals[i] = st.pearsonr(df[[i]], df[['target']])

        print('=======\n\nPearson:\n')

        height = []
        bars = []
        intensity = []

        for key in range(24):
            print('time = {}, rho = {}, pval = {}'.format(key, rhos[key].item(0),
                                                          pvals[key].item(0)))
            height.append(rhos[key].item(0))
            bars.append(key)
            intensity.append(pvals[key].item(0))

        bars = tuple(bars)

        colours = []
        for i in intensity:
            transparency = 1 - i
            colours.append((0, 0.3399, 0.6601, transparency))

        y_pos = np.arange(len(bars))
        plt.bar(y_pos, height, color=colours)
        plt.xticks(y_pos, bars)
        plt.show()

        # print('=======\n\nSpearman:\n')

        # rhos = dict.fromkeys(range(24))
        # pvals = dict.fromkeys(range(24))
        # for i in range(24):
        #     rhos[i], pvals[i] = st.spearmanr(df[[i]], df[['target']])

        # for key in range(24):
        #     print('time = {}, rho = {}, pval = {}'.format(key, rhos[key],
        #                                                   pvals[key]))
    elif ans.split(' ', 1)[0] == "coors":
        from scipy import stats as st
        tickerlist = []
        for f in open(DATA_PATH + 'tickers.txt', 'r'):
            tickerlist.append(f.strip())
        coors = dict.fromkeys(tickerlist)

        for ticker in coors.keys():

            df = pd.read_csv(DATA_PATH + ticker +
                             " tweets ftlbl.csv", index_col=0, parse_dates=[0])

            coors[ticker] = {'pear': [0]*24, 'pval': [0]*24, 'avg_pear': None}
            for i in range(24):
                temp = st.pearsonr(df[[str(i)]], df[['target']])
                coors[ticker]['pear'][i], coors[ticker]['pval'][i] = [
                    temp[0][0], temp[1][0]]

            coors[ticker]['avg_pear'] = np.mean(coors[ticker]['pear'][i])

        print(sorted(coors, key=lambda k: abs(coors[k]['avg_pear'])))

    elif ans.split(' ', 1)[0] == "exit":
        break
