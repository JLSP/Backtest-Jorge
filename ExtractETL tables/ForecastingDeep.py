import numpy as np
import sys

from sklearn import preprocessing

from sklearn.metrics import mean_squared_error, classification_report

import matplotlib.pylab as plt

import datetime as dt

import time

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.recurrent import LSTM, GRU
from keras.layers import Convolution1D, MaxPooling1D




def load_snp_returns():

    f = open('Datos15MiniIbex.csv', 'rb').readlines()[1:]

    raw_data = []

    raw_dates = []

    for line in f:

        try:

            open_price = float(line.split(',')[1])

            close_price = float(line.split(',')[4])

            raw_data.append(close_price - open_price)

            raw_dates.append(line.split(',')[0])

        except:

            continue



    return raw_data[::-1], raw_dates[::-1]





def load_snp_close():

    f = open('C:\\Azul\\Trading\\Datos15MiniIbex.csv', 'r').readlines()[2:]

    raw_data = []

    raw_dates = []

    for line in f:

        #try:
            
            close_price = float(line.split(';')[5])
            raw_data.append(close_price)

            raw_dates.append(line.split(';')[0]+' '+line.split(';')[1])

        #except:

            #continue



    return raw_data, raw_dates





def split_into_chunks(data, train, predict, step, binary=False, scale=True):

    X, Y = [], []

    for i in range(0, len(data), step):

        try:

            x_i = data[i:i+train]

            y_i = data[i+train+predict]

            

            # Use it only for daily return time series

            if binary:

                if y_i > 0.:

                    y_i = [1., 0.]

                else:

                    y_i = [0., 1.]



                if scale: x_i = preprocessing.scale(x_i)

                

            else:

                timeseries = np.array(data[i:i+train+predict])

                if scale: timeseries = preprocessing.scale(timeseries)

                x_i = timeseries[:-1]

                y_i = timeseries[-1]

            

        except:

            break



        X.append(x_i)

        Y.append(y_i)



    return X, Y





def shuffle_in_unison(a, b):

    # courtsey http://stackoverflow.com/users/190280/josh-bleecher-snyder

    assert len(a) == len(b)

    shuffled_a = np.empty(a.shape, dtype=a.dtype)

    shuffled_b = np.empty(b.shape, dtype=b.dtype)

    permutation = np.random.permutation(len(a))

    for old_index, new_index in enumerate(permutation):

        shuffled_a[new_index] = a[old_index]

        shuffled_b[new_index] = b[old_index]

    return shuffled_a, shuffled_b





def create_Xt_Yt(X, y, percentage=0.8):

    X_train = X[0:len(X) * percentage]

    Y_train = y[0:len(y) * percentage]

    

    X_train, Y_train = shuffle_in_unison(X_train, Y_train)



    X_test = X[len(X) * percentage:]

    Y_test = y[len(X) * percentage:]



    return X_train, X_test, Y_train, Y_test

timeseries, dates = load_snp_close()
dates = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in dates]
#plt.plot(dates, timeseries)

TRAIN_SIZE = 20
TARGET_TIME = 1
LAG_SIZE = 1
EMB_SIZE = 1
HIDDEN_RNN = 3

X, Y = split_into_chunks(timeseries, TRAIN_SIZE, TARGET_TIME, LAG_SIZE, binary=False, scale=False)
X, Y = np.array(X), np.array(Y)
X_train, X_test, Y_train, Y_test = create_Xt_Yt(X, Y, percentage=0.9)

Xp, Yp = split_into_chunks(timeseries, TRAIN_SIZE, TARGET_TIME, LAG_SIZE, binary=False, scale=False)
Xp, Yp = np.array(Xp), np.array(Yp)
X_trainp, X_testp, Y_trainp, Y_testp = create_Xt_Yt(Xp, Yp, percentage=0.9)

X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], EMB_SIZE))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], EMB_SIZE))

model = Sequential()

model.add(LSTM(64, input_dim=64, input_length=10, return_sequences=True))
model.add(LSTM(32, return_sequences=False))

model.add(Dense(2))
model.add(Activation('softmax'))
model.compile(optimizer='adam', 
              loss='mse',
              metrics=['accuracy'])

model.fit(X_train, 
    Y_train, 
    nb_epoch=5, 
    batch_size = 128, 
    verbose=1, 
    validation_split=0.1)
score = model.evaluate(X_test, Y_test, batch_size=128)
print (score)