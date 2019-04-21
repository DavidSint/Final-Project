from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.svm import LinearSVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn import model_selection
from auxillary import weekdays
from datetime import datetime, timedelta, time
import pandas as pd
import numpy as np
from pymongo import MongoClient

holiday_list = ['2018-11-22', '2018-11-23', '2018-12-05',
                '2018-12-24', '2018-12-25', '2019-01-01', '2019-01-21', '2019-02-18']  # half days are included as a holiday too
# [thanksgiving, black friday (closes 13:00), GHWB death, Xmas eve (closes 13:00), Xmas, New years day, MLK bday, Presidents day]

stock_bin_length = 65
stock_window_length = 390  # trading day

tweet_bin_length = '60min'
tweet_window_length = '1440min'  # 24 hours

start_date = datetime(2018, 10, 29).date()
end_date = datetime(2019, 3, 25).date()

DATA_PATH = "Data/"

if (stock_window_length/stock_bin_length).is_integer() == False:
    raise Exception('stock window length mod stock bin length should be 0. it was: {}'.format(
        str(stock_window_length/stock_bin_length)))

    # function to read from a db into a pandas df
    # https://stackoverflow.com/questions/16249736/how-to-import-data-from-mongodb-to-pandas
def read_from_db(db, ticker, query={}, no_id=True):
    cursor = db[ticker].find(query)
    df = pd.DataFrame(list(cursor))
    try:
        if no_id:
            del df['_id']
    except KeyError as e:
        print("There is a problem with the MongoDB instance:", ticker,"from", str(db), "has caused an error. Are you sure it has been restored properly?")
        exit()

    df['timestamp'] = pd.to_datetime(
        df['timestamp'],  infer_datetime_format=True)
    df = df.sort_values(by='timestamp')
    return df


def get(ticker):
    '''
    Creates a Stocks CSV file and a Tweets CSV files for the ticker.
    sdb is for the stock values and tdb is for the tweets.
    '''
    start_date = datetime(2018, 10, 29).date()
    end_date = datetime(2019, 3, 25).date()


    client = MongoClient('localhost', 27017)
    StocksDB = client.StocksDB
    newStocksDB = client.TestStocksDB
    TweetsDB = client.TweetsDB

    print("Getting and starting cleaning",
          ticker, "stock prices from MongoDB...")
    sdb = read_from_db(StocksDB, ticker).set_index(
        'timestamp')  # stocks database 2018
    nsdb = read_from_db(newStocksDB, ticker).set_index(
        'timestamp')  # stocks database 2019
    sdb = nsdb.drop_duplicates().combine_first(sdb)  # merge 2018 with 2019

    sdb['date'] = sdb.index
    sdb = sdb[~sdb['date'].dt.strftime('%Y-%m-%d').isin(holiday_list)]
    sdb.drop('date', axis=1, inplace=True)

    # if a close is missing, remove the entry as it is useless.
    sdb = sdb.dropna(subset=['close'])

    sdb.to_csv(DATA_PATH + ticker + " sdb.csv")

    print("Getting and starting cleaning", ticker, "tweets from MongoDB...")
    tdb = read_from_db(TweetsDB, ticker)  # tweets database
    tdb = tdb.reset_index(drop=True)
    # convert tweets to the Eastern Timezone to match the S&P100 timezone
    tdb['timestamp'] = tdb['timestamp'].dt.tz_localize(
        'Europe/London').dt.tz_convert('US/Eastern').dt.tz_localize(None)

    # for the grouping to work, the tweets should be grouped 00:00-23:59. If people only start tweeting later on the 29th, grouping will start late. To ensure grouping is done properly, a fake tweet is added to the 28th which will be grouped (perhaps with errors) and then dropped.
    tdb.loc[-1] = ['Starting', 0, 0, 0, 'Starting',
                   '2018-10-28 00:00:00', 'Starting']
    tdb.index = tdb.index + 1
    tdb = tdb.sort_index()

    tdb.to_csv(DATA_PATH + ticker + " tdb.csv")


def baseline(ticker):
    '''
    Creates the baseline dataset
    '''
    try:
        sdb = pd.read_csv(DATA_PATH + ticker + " sdb.csv", index_col=0,
                          parse_dates=['timestamp'])
    except:
        print("You must first run the 'get' command!")
        return

    print("Processing baseline for", ticker + "...")
    avgdb = sdb.drop(['volume'], axis=1)

    per_day_stock = {}

    for dt, values in avgdb.iterrows():
        day_date = str(dt.date())
        if day_date not in per_day_stock:  # if the day has not been put in then, set the current bin to the date
            current_bin = datetime.combine(dt.date(), time(9, 31, 0))
            per_day_stock[day_date] = [[values['close']]]
        else:
            # if the distance of the dt from current_bin is less than bin_width, then append this entry to the current bin
            # o.w., update the current_bin, create a new list with this new entry.
            if (dt - current_bin) < timedelta(minutes=stock_bin_length):
                per_day_stock[day_date][-1].append(values['close'])
            else:
                current_bin = current_bin + timedelta(minutes=stock_bin_length)
                per_day_stock[day_date].append([values['close']])

    # for each bin calculate variance and mean
    meanstd = {}
    for key, value in per_day_stock.items():
        x = []
        for i in range(0, int(stock_window_length/stock_bin_length)):
            std = np.std(value[i])
            mean = np.mean(value[i])

            x.append(std)
            x.append(mean)

        meanstd[key] = x

    sdf = pd.DataFrame.from_dict(meanstd, orient='index')

    # add on targets
    roller = sdb.rolling(390)
    volList = roller.std(ddof=0)
    volList = volList.drop(['volume'], axis=1)

    targets = []  # Will become the targets column
    sdbtargeted = pd.DataFrame(columns=list(sdf))
    for i in weekdays(start_date, end_date):
        temp = str(i.date()) + " 16:00:00"

        if str(pd.to_datetime(temp, infer_datetime_format=True).date()) not in holiday_list:
            try:
                target_date = volList.loc[temp, 'close']
                targets.append(target_date)
                sdbtargeted.loc[i] = sdf.loc[str(i.date())]
            except KeyError as e:
                print('API issue. Skipping day as no CoB stock prices were found at', e)
                pass

    sdbtargeted['target'] = targets

    # shift target one to account for next day
    sdbtargeted['target'] = sdbtargeted['target'].shift(-1)
    sdbtargeted = sdbtargeted[: -1]
    sdbtargeted.to_csv(DATA_PATH + ticker + " stocks ftlbl.csv")
    print(ticker + " stocks ftlbl.csv created.")


def tweets(ticker):
    '''
    Creats the tweets dataset
    '''
    print("Processing tweet+stocks features & labels for", ticker + "...")
    try:
        tdb = pd.read_csv(DATA_PATH + ticker + " tdb.csv", index_col=0,
                          parse_dates=['timestamp'], date_parser=pd.to_datetime, engine='python')  # engine needed to be changed, as dates were causing issues.
        sdbtargeted = pd.read_csv(DATA_PATH + ticker + " stocks ftlbl.csv", index_col=0,
                                  parse_dates=[0])
    except:
        print("You must first run the 'get' and 'baseline' commands")
        return

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

    mergeddf.to_csv(DATA_PATH + ticker + " tweets ftlbl.csv")
    print(ticker + " tweets ftlbl.csv created.")


def split(df, test_size):
    '''
    Splits a dataset into training and testing features and targets.
    '''
    targets = df['target']
    features = df.drop('target', axis=1)

    return train_test_split(features, targets, test_size=test_size, random_state=4242)


def mape(prediction, test):
    '''
    Returns the Mean Average Percentage Error
    '''
    test, prediction = np.array(test), np.array(prediction)
    return np.mean(np.abs((test - prediction) / test)) * 100


def rf(df, test_size, n_estimators):
    '''
    Returns the random forest predictions and testing value when given a dataset 
    '''
    X_train, X_test, y_train, y_test = split(df, test_size=test_size)

    # Random Forrest
    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=42)
    rf.fit(X_train, y_train)

    predictions = rf.predict(X_test)

    # mae = round(np.mean(abs(predictions - y_test)), 2)
    # return mae

    return (predictions, y_test)


def linear(df, test_size):
    '''
    Returns the linear regression predictions and testing value when given a dataset 
    '''

    X_train, X_test, y_train, y_test = split(df, test_size=test_size)

    reg = LinearRegression().fit(X_train, y_train)

    # return reg.score(X_test, y_test)

    predictions = reg.predict(X_test)
    return (predictions, y_test)


def linearSVR(df, test_size, tol):
    '''
    Returns the linear SVR predictions and testing value when given a dataset 
    '''
    import warnings
    warnings.filterwarnings('ignore')

    X_train, X_test, y_train, y_test = split(df, test_size=test_size)

    reg = LinearSVR(random_state=0, tol=tol).fit(X_train, y_train)

    # return reg.score(X_test, y_test)

    predictions = reg.predict(X_test)
    return (predictions, y_test)


def kNearest(df, test_size, n_neighbors):
    '''
    Returns the k-nearest neighbor predictions and testing value when given a dataset 
    '''

    X_train, X_test, y_train, y_test = split(df, test_size=test_size)

    reg = KNeighborsRegressor(n_neighbors=n_neighbors).fit(X_train, y_train)

    # return reg.score(X_test, y_test)

    predictions = reg.predict(X_test)
    return (predictions, y_test)


def regressor(action, test_size, value, variable=None):
    '''
    Runs the regression and prints the results
    '''
    baseline_regs = {}
    tweets_regs = {}

    print("\n")
    for f in open(DATA_PATH + 'tickers.txt', 'r'):
        ticker = f.strip()
        try:
            tweetsftlbl = pd.read_csv(
                DATA_PATH + ticker + " tweets ftlbl.csv", index_col=0, parse_dates=[0])
            stocksftlbl = pd.read_csv(
                DATA_PATH + ticker + " stocks ftlbl.csv", index_col=0, parse_dates=[0])
            if variable:
                prediction, test = action(stocksftlbl, test_size, variable)
                baseline_regs[ticker] = mape(prediction, test)
                print(ticker, 'Baseline', value+':', baseline_regs[ticker])

                prediction, test = action(tweetsftlbl, test_size, variable)
                tweets_regs[ticker] = mape(prediction, test)
                print(ticker, 'Tweets', value+':', tweets_regs[ticker])
            else:
                prediction, test = action(stocksftlbl, test_size)
                baseline_regs[ticker] = mape(prediction, test)
                print(ticker, 'Baseline', value+':', baseline_regs[ticker])

                prediction, test = action(tweetsftlbl, test_size)
                tweets_regs[ticker] = mape(prediction, test)
                print(ticker, 'Tweets', value+':', tweets_regs[ticker])

        except:
            print("You must first run the 'get' and 'baseline' commands!")
            return

    diffs = []
    for key, value in baseline_regs.items():
        diff = tweets_regs[key] - baseline_regs[key]
        diffs.append(diff)
        print(key, "improvement is:", round(diff, 2))
    print("Average improvement:", round(np.mean(diffs), 2), "\n\n")
