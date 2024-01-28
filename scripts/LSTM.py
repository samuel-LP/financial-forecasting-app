import pandas as pd

from LSTM_utils import prepare_data, prepare_data2

import numpy as np
from keras import Sequential
from keras.layers import Dense, LSTM
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
from sklearn.model_selection import TimeSeriesSplit


class PortfolioPredicitionsLSTM():
    def __init__(self, stock_dict, n_steps, epochs):
        self.stock_dict = stock_dict
        self.splitter = TimeSeriesSplit(n_splits=2)
        self.n_steps = n_steps
        self.epochs = epochs

    def split_data(self, stock):
        returns = stock['Close'].pct_change()[1:].values.reshape(-1, 1)
        self.train, self.test = self.splitter.split(returns)

        self.returns_train = returns[self.train[1]]
        self.returns_test = returns[self.test[1]]

    def scale_data(self):
        self.scaler = StandardScaler()
        self.returns_train_scaled = self.scaler.fit_transform(self.returns_train)
        self.returns_test_scaled = self.scaler.transform(self.returns_test)

    def reshape_data(self):
        self.x_train, self.y_train = prepare_data(self.returns_train_scaled,self.n_steps)
        self.x_test, self.y_test = prepare_data(self.returns_test_scaled, self.n_steps)

        self.x_train = np.reshape(self.x_train, (self.x_train.shape[0], self.x_train.shape[1], 1))
        self.x_test = np.reshape(self.x_test, (self.x_test.shape[0], self.x_test.shape[1], 1))

    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=50))
        model.add(Dense(units=1))

        model.compile(optimizer='adam', loss='mean_squared_error')

        return model

    def fit_model(self):
        self.model = self.create_lstm_model((self.x_train.shape[1], 1))
        self.model.fit(self.x_train, self.y_train, epochs=self.epochs, batch_size=16, verbose=0)

    def predict(self):
        self.test_predictions = self.model.predict(self.x_test, verbose=0)
        self.test_predictions = self.scaler.inverse_transform(self.test_predictions)

    def compute_portfolio_value(self, stock):
        temp = stock[["Date", "Close"]].loc[self.test[1][self.n_steps:]]

        temp["Returns"] = self.returns_test[self.n_steps:]
        temp["Prediction"] = self.test_predictions
        temp.drop(columns="Close", inplace=True)

        temp['Real_Portfolio_Value'] = 1000 * (1 + temp['Returns']).cumprod()
        temp['Predicted_Portfolio_Value'] = 1000 * (1 + temp['Prediction']).cumprod()

        return(temp)

    def run_model_stock(self, stock):
        self.split_data(stock)
        self.scale_data()
        self.reshape_data()
        self.fit_model()
        self.predict()
        stock_prediction = self.compute_portfolio_value(stock)
        return(stock_prediction)

    def predict_portfolio(self):
        self.predictions_dic = {}

        for key in tqdm(self.stock_dict) :
            self.predictions_dic[key] = self.run_model_stock(self.stock_dict[key])

    def compute_portfolio(self):
        dfs_to_concat = []

        for name, df in self.predictions_dic.items():
            df['Date'] = pd.to_datetime(df['Date'])

            dfs_to_concat.append(df[['Date', 'Prediction', 'Returns']])

        portfolio_predictions = pd.concat(dfs_to_concat)

        self.portfolio_avg_predictions = portfolio_predictions.groupby('Date').mean().reset_index()

        self.portfolio_avg_predictions['Real_Portfolio_Value'] = 1000 * (1 + self.portfolio_avg_predictions['Returns']).cumprod()
        self.portfolio_avg_predictions['Predicted_Portfolio_Value'] = 1000 * (1 + self.portfolio_avg_predictions['Prediction']).cumprod()

    def predict_avg_portfolio(self):
        self.predict_portfolio()
        self.compute_portfolio()
        return(self.predictions_dic, self.portfolio_avg_predictions)

class PortfolioPredicitionsLSTM_value():
    def __init__(self, stock_dict, n_steps, epochs):
        self.stock_dict = stock_dict
        self.splitter = TimeSeriesSplit(n_splits=2)
        self.n_steps = n_steps
        self.epochs = epochs

    def split_data(self, stock):
        returns = stock['Close'].values.reshape(-1, 1)
        self.train, self.test = self.splitter.split(returns)

        self.returns_train = returns[self.train[1]]
        self.returns_test = returns[self.test[1]]

    def scale_data(self):
        self.scaler = StandardScaler()
        self.returns_train_scaled = self.scaler.fit_transform(self.returns_train)
        self.returns_test_scaled = self.scaler.transform(self.returns_test)

    def reshape_data(self):
        self.x_train, self.y_train = prepare_data(self.returns_train_scaled,self.n_steps)
        self.x_test, self.y_test = prepare_data(self.returns_test_scaled, self.n_steps)

        self.x_train = np.reshape(self.x_train, (self.x_train.shape[0], self.x_train.shape[1], 1))
        self.x_test = np.reshape(self.x_test, (self.x_test.shape[0], self.x_test.shape[1], 1))

    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=50))
        model.add(Dense(units=1))

        model.compile(optimizer='adam', loss='mean_squared_error')

        return model

    def fit_model(self):
        self.model = self.create_lstm_model((self.x_train.shape[1], 1))
        self.model.fit(self.x_train, self.y_train, epochs=self.epochs, batch_size=16, verbose=0)

    def predict(self):
        self.test_predictions = self.model.predict(self.x_test, verbose=0)
        self.test_predictions = self.scaler.inverse_transform(self.test_predictions)

    def compute_portfolio_value(self, stock):
        temp = stock[["Date", "Close"]].loc[self.test[1][self.n_steps:]]

        temp["Prediction"] = self.test_predictions

        temp['Real_Return'] = temp['Close'].pct_change()
        temp['Predicted_Return'] = temp['Prediction'].pct_change()

        temp = temp.dropna()

        return(temp)

    def run_model_stock(self, stock):
        self.split_data(stock)
        self.scale_data()
        self.reshape_data()
        self.fit_model()
        self.predict()
        stock_prediction = self.compute_portfolio_value(stock)
        return(stock_prediction)

    def predict_portfolio(self):
        self.predictions_dic = {}

        for key in tqdm(self.stock_dict) :
            self.predictions_dic[key] = self.run_model_stock(self.stock_dict[key])

    def compute_portfolio(self):
        dfs_to_concat = []

        for name, df in self.predictions_dic.items():
            df['Date'] = pd.to_datetime(df['Date'])

            dfs_to_concat.append(df[['Date', 'Real_Return', 'Predicted_Return']])

        portfolio_predictions = pd.concat(dfs_to_concat)

        self.portfolio_avg_predictions = portfolio_predictions.groupby('Date').mean().reset_index()

        self.portfolio_avg_predictions['Real_Portfolio_Value'] = 1000 * (1 + self.portfolio_avg_predictions['Real_Return']).cumprod()
        self.portfolio_avg_predictions['Predicted_Portfolio_Value'] = 1000 * (1 + self.portfolio_avg_predictions['Predicted_Return']).cumprod()

    def predict_avg_portfolio(self):
        self.predict_portfolio()
        self.compute_portfolio()
        return(self.predictions_dic, self.portfolio_avg_predictions)


class PortfolioPredicitionsLSTM_value2():
    def __init__(self, stock_dict, n_steps, epochs):
        self.stock_dict = stock_dict
        self.splitter = TimeSeriesSplit(n_splits=2)
        self.n_steps = n_steps
        self.epochs = epochs

    def split_data(self, stock):
        returns = stock['Close'].values.reshape(-1, 1)
        self.train, self.test = self.splitter.split(returns)

        self.returns_train = returns[self.train[1]]
        self.returns_test = returns[self.test[1]]

    def scale_data(self):
        self.scaler = StandardScaler()
        self.returns_train_scaled = self.scaler.fit_transform(self.returns_train)
        self.returns_test_scaled = self.scaler.transform(self.returns_test)

    def reshape_data(self):
        self.x_train, self.y_train = prepare_data2(self.returns_train_scaled,self.n_steps)
        self.x_test, self.y_test = prepare_data2(self.returns_test_scaled, self.n_steps)

        self.x_train = np.reshape(self.x_train, (self.x_train.shape[0], self.x_train.shape[1], 1))
        self.x_test = np.reshape(self.x_test, (self.x_test.shape[0], self.x_test.shape[1], 1))

    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=50))
        model.add(Dense(units=7))

        model.compile(optimizer='adam', loss='mean_squared_error')

        return model

    def fit_model(self):
        self.model = self.create_lstm_model((self.x_train.shape[1], 1))
        self.model.fit(self.x_train, self.y_train, epochs=self.epochs, batch_size=16, verbose=0)

    def predict(self):
        self.test_predictions = self.model.predict(self.x_test, verbose=0)
        self.test_predictions = np.array([x[6] for x in self.test_predictions]).reshape(-1,1)
        self.test_predictions = self.scaler.inverse_transform(self.test_predictions)

    def compute_portfolio_value(self, stock):
        temp = stock[["Date", "Close"]].loc[self.test[1][self.n_steps+6:]]

        temp["Prediction"] = self.test_predictions

        temp['Real_Return'] = temp['Close'].pct_change()
        temp['Predicted_Return'] = temp['Prediction'].pct_change()

        temp = temp.dropna()

        return(temp)

    def run_model_stock(self, stock):
        self.split_data(stock)
        self.scale_data()
        self.reshape_data()
        self.fit_model()
        self.predict()
        stock_prediction = self.compute_portfolio_value(stock)
        return(stock_prediction)

    def predict_portfolio(self):
        self.predictions_dic = {}

        for key in tqdm(self.stock_dict) :
            self.predictions_dic[key] = self.run_model_stock(self.stock_dict[key])

    def compute_portfolio(self):
        dfs_to_concat = []

        for name, df in self.predictions_dic.items():
            df['Date'] = pd.to_datetime(df['Date'])

            dfs_to_concat.append(df[['Date', 'Real_Return', 'Predicted_Return']])

        portfolio_predictions = pd.concat(dfs_to_concat)

        self.portfolio_avg_predictions = portfolio_predictions.groupby('Date').mean().reset_index()

        self.portfolio_avg_predictions['Real_Portfolio_Value'] = 1000 * (1 + self.portfolio_avg_predictions['Real_Return']).cumprod()
        self.portfolio_avg_predictions['Predicted_Portfolio_Value'] = 1000 * (1 + self.portfolio_avg_predictions['Predicted_Return']).cumprod()

    def predict_avg_portfolio(self):
        self.predict_portfolio()
        self.compute_portfolio()
        return(self.predictions_dic, self.portfolio_avg_predictions)

class PortfolioPredicitionsLSTMVolatility():
    def __init__(self, stock_dict, n_steps, epochs):
        self.stock_dict = stock_dict
        self.splitter = TimeSeriesSplit(n_splits=2)
        self.n_steps = n_steps
        self.epochs = epochs

    def split_data(self, stock):
        stock["ret"] = stock['Close'].pct_change()
        stock.dropna(inplace = True)
        volatility = stock['ret'].rolling(window=10).std().values.reshape(-1,1)
        self.train, self.test = self.splitter.split(volatility)

        self.returns_train = volatility[self.train[1]]
        self.returns_test = volatility[self.test[1]]

    def scale_data(self):
        self.scaler = StandardScaler()
        self.returns_train_scaled = self.scaler.fit_transform(self.returns_train)
        self.returns_test_scaled = self.scaler.transform(self.returns_test)

    def reshape_data(self):
        self.x_train, self.y_train = prepare_data(self.returns_train_scaled,self.n_steps)
        self.x_test, self.y_test = prepare_data(self.returns_test_scaled, self.n_steps)

        self.x_train = np.reshape(self.x_train, (self.x_train.shape[0], self.x_train.shape[1], 1))
        self.x_test = np.reshape(self.x_test, (self.x_test.shape[0], self.x_test.shape[1], 1))

    def create_lstm_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(units=50))
        model.add(Dense(units=1))

        model.compile(optimizer='adam', loss='mean_squared_error')

        return model

    def fit_model(self):
        self.model = self.create_lstm_model((self.x_train.shape[1], 1))
        self.model.fit(self.x_train, self.y_train, epochs=self.epochs, batch_size=16, verbose=0)

    def predict(self):
        self.test_predictions = self.model.predict(self.x_test, verbose=0)
        self.test_predictions = self.scaler.inverse_transform(self.test_predictions)

    def compute_portfolio_value(self, stock):
        temp = stock[["Date", "Close"]].loc[self.test[1][self.n_steps:]]

        temp["Volatility"] = self.returns_test[self.n_steps:]
        temp["Prediction"] = self.test_predictions
        temp.drop(columns="Close", inplace=True)

        return(temp)

    def run_model_stock(self, stock):
        self.split_data(stock)
        self.scale_data()
        self.reshape_data()
        self.fit_model()
        self.predict()
        stock_prediction = self.compute_portfolio_value(stock)
        return(stock_prediction)

    def predict_portfolio(self):
        self.predictions_dic = {}

        for key in tqdm(self.stock_dict) :
            self.predictions_dic[key] = self.run_model_stock(self.stock_dict[key])

    def compute_portfolio(self):
        dfs_to_concat = []

        for name, df in self.predictions_dic.items():
            df['Date'] = pd.to_datetime(df['Date'])

            dfs_to_concat.append(df[['Date', 'Prediction', 'Volatility']])

        portfolio_predictions = pd.concat(dfs_to_concat)

        self.portfolio_avg_predictions = portfolio_predictions.groupby('Date').mean().reset_index()

    def predict_avg_portfolio(self):
        self.predict_portfolio()
        self.compute_portfolio()
        return(self.predictions_dic, self.portfolio_avg_predictions)





