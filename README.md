# QMUL Final Project
This was an experiment and a research project for my Final Year at QMUL. The files included are some of those that helped me collect and analyse the data some have been also included in the supporting material, but others are only available on GitHub due to file size limits.

## Project Files
As well as in the supporting materials folder, I have pushed the files to a repo on [GitHub](https://github.com/DavidSint/Final-Project), where it can be downloaded/cloned.

## Environment
The python files were run in a conda environment, of which the environment.yml can be used to load the necessary libraries. The command for creating the conda environment using environment.yml is:
```bash
conda env create --name envname -f environment.yml
```
Activate this environment, for use with this project.

## Data
The data stored in my database is too large for me to share in the supporting material folder. The MongoDB has been dumped to a folder called `dump` in the repo and can be restored to a local MongoDB instance by using the command:
```bash
mongorestore dump
```
Sometimes MongoDB fails to restore all the collections and documents from multiple DBs. In this instance they can be restored individually with the commands:
```bash
mongorestore -d StocksDB dump/StocksDB
mongorestore -d TestStocksDB dump/TestStocksDB
mongorestore -d TweetsDB dump/TweetsDB
```

The Data/tickers.txt file is a list of the S&P 100 tickers, it has the ticker for $BIIB removed, as explained in the report. However, if you would like to add it back in for data collection purposes, it can be added with the new line, `BIIB`.

## Python Files
Python files can be found in the home directory of the repo or supporting materials folder.

* `tweetgetter.py` was used to collect tweets using the `twitterscraper` library. The `config.py` variables need to contain the gmail password for those features to work, instead - these sections have been commented out.
* `stockgetter.py` was used to collect stocks from Alpha Vantage. The `config.py` variables need to contain the gmail password and the API key for this to work. The gmail functionality has been commented out so this is not needed, but an API Key is still necessary in the config.py.
* `iexgetter.py` was used to collect stock prices from IEX Finance.
* `ml.py` was used for calculating the analysis. Its use is explained below.
* `auxillary.py` and `functions.py` are supporting files for `ml.py`.
* `config.py` should contain the gmail password and API key. These have been left out! You can get your own API key at [AlphaVantage](https://www.alphavantage.co/support/#api-key).

## ml.py
`ml.py` makes the csv files and performs the correlation and machine learning analyses.

To run `ml.py`, run the command:
```bash
python ml.py
```
You will be presented with multiple options. But, you *must* run the first three commands in order before any others.

The first commands you must run (in order) are:
1. `get`
2. `baseline`
3. `tweets`
These will generate the necessary CSV files in `Data/`. After this, you can use the other commands. 



| Command | Purpose | Arguments | Parameter details |
|:---:|---|---|---|
| `get` | Will get the data from MongoDB and store it in CSV files. This will also start the data cleaning process. After this stage, the MongoDB can be shut down. | | None |
| `baseline` | Finishes the cleaning process and makes the baseline dataset CSVs | | None |
| `tweets` | Finishes the cleaning process and makes the tweets dataset CSVs | | None |
| `pearson` | Will print the Pearson correlations and plot on a graph | ticker | Optional parameter: ticker of stock Default: AAPL |
| `coors` | Will print the Pearson correlation ordered by coefficient values | | None |
| `rf` | Will calculate the baseline and tweets MAPE as well as their difference for Random Forest | test_size, n_estimators | Optional parameters: test size and number of estimators Default: 0.1, 1000 |
| `linear` | Will calculate the baseline and tweets MAPE as well as their difference for Linear Regression | test_size | Optional parameters: test size Default: 0.1 |
| `linearSVR` | Will calculate the baseline and tweets MAPE as well as their difference for Linear SVR | test_size, tol | Optional parameters: test size and tolerance Default: 0.1, 1e-5 |
| `kNearest` | Will calculate the baseline and tweets MAPE as well as their difference for k-nearest neighbor | test_size, neigh | Optional parameters: test size and number of neighbors Default: 0.1, 3 |
| `exit` | Will quit the script | | None |

## Troubleshooting
*Problem with MongoDB when running `get` command*
If you find an issue with MongoDB, first try the mongorestore individually for each db:
```bash
mongorestore -d StocksDB dump/StocksDB
mongorestore -d TestStocksDB dump/TestStocksDB
mongorestore -d TweetsDB dump/TweetsDB
```
If this still does not fix the issue, then large `.bson` files may need to be manually copied over to the MongoDB instance. The two largest files are `dump/TweetsDB/AAPL.bson` and `dump/TweetsDB/FOX.bson`.

*Problem with libraries or Conda*
Ensure that the conda environment has been activated and the libraries from `environment.yml` are shown when you run the command `conda list`.

*Problem running the correlation or regressors*
Ensure that the get, baseline and tweets commands have been run completely without errors. API errors are expected, and not a problem.