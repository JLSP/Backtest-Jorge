from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import datetime
import os.path
import sys
from matplotlib.cbook import todate
import csv




class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        
        dt = dt or self.data.datetime.datetime(1)
        ft = self.data1.datetime.datetime(0)
        print('%s, %s, %s' % (str(dt),str(ft),txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data dataseries
        #self.volume = self.datas[0].volume
        self.dataclose = self.data.close
        self.volume = self.data.volume
        self.high = self.data.high
        self.low = self.data.low
        self.open = self.data.open

        self.dataclose1 = self.data1.close
        self.volume1 = self.data1.volume
        self.high1 = self.data1.high
        self.low1 = self.data1.low
        self.open1 = self.data1.open

        self.rsi10 = bt.indicators.RSI_SMA(self.data1.close,period = 10, safediv=True)
        self.rsi21 = bt.indicators.RSI_SMA(self.data1.close,period = 21, safediv=True)

        self.rsi10daily = bt.indicators.RSI_SMA(self.data.close,period = 10, safediv=True)
        self.rsi21daily = bt.indicators.RSI_SMA(self.data.close,period = 21, safediv=True)

        self.atr = bt.indicators.AverageTrueRange(self.data1,period = 14)
        self.atrdaily = bt.indicators.AverageTrueRange(self.data,period = 14)

        self.williams = bt.indicators.WilliamsR(self.data1,period = 7)
        self.williamsDaily = bt.indicators.WilliamsR(self.data,period = 7)

        self.stochastic = bt.indicators.Stochastic(self.data1)
        self.stochasticDaily = bt.indicators.Stochastic(self.data)
        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        global buyprice
        global switch
        global sellprice
        global ordertype
        global pricelimit

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed]:
            if order.isbuy():
                buyprice = order.executed.price
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
                
            elif order.issell():
                sellprice = order.executed.price
                if  ordertype == "LARGO" :
                    profit = sellprice - buyprice
                else:
                    profit = buyprice - sellprice
                self.log('SELL EXECUTED, %.2f, BENEFICIO %.2f' % (order.executed.price,profit))
                switch = True

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None
  
    def next(self):
        global i
        global lastdate
        global switch
        global maxday
        global minday
        global ordertype
        global exitfilter
        global nolose    
        global buyprice
        global sellprice
        global noloseamount
        global switchnp
        global pricelimit
        global mecha
        global fileWriter
        global id
        global venta
        global compra
        global buymessage
        global sellmessage
        sizeMechaHigh = 0
        sizeMechaLow = 0
        profit = 0
        event = ""


        if venta == 1:
            fileWriter.write(sellmessage.replace("##sellprice##",str(sellprice)))    
            venta = 0
        if compra == 1:
            fileWriter.write(buymessage.replace("##buyprice##",str(buyprice)))
            compra = 0

        if len(self.data)<self.data.buflen():
            m = 0
            if self.data.datetime.datetime(0)!= lastdate:
                i = i+1
            
            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.order:
                return
            
            # Check if we are in the market
            if switch:

                if i<3:
                    ordertype = "NOORDER"
                else:
                    if self.dataclose[1]>self.open[1]:
                        #Regla Unknown
                        #sizeMechaHigh = self.high[1]-self.open[1]
                        #Regla real
                        sizeMechaHigh = self.high[1]-self.dataclose[1]
                        sizeMechaInfHigh = self.low[1]-self.open[1]
                        sizeBodyHigh = self.dataclose[1]-self.open[1]
                    else:
                        #Regla Unknown
                        #sizeMechaHigh = self.high[1]-self.open[1]
                        #Regla real
                        sizeMechaHigh = self.high[1]-self.open[1]
                        sizeMechaInfHigh = self.low[1]-self.dataclose[1]
                        sizeBodyHigh = self.open[1]-self.dataclose[1]

                    if self.dataclose[1]>self.open[1]:
                        sizeMechaLow = self.open[1]-self.low[1]
                        sizeMechaInfLow = self.high[1]-self.dataclose[1]
                        sizeBodyLow = self.dataclose[1]-self.open[1]
                    else:
                        sizeMechaLow = self.dataclose[1]-self.low[1]
                        sizeMechaInfLow = self.high[1]-self.open[1]
                        sizeBodyLow = self.open[1]-self.dataclose[1]

                    if self.high[1]>= self.high[0] and self.high[0]>= self.high[-1] and sizeMechaHigh>=mecha \
                        and str(self.data1.datetime.datetime(0).time()) == "17:15:00":# and sizeMechaHigh>sizeMechaInfHigh
                        self.order = self.buy(data = data1)
                        compra = 1
                        ordertype = "CORTO"
                        id = len(self.data)
                        buymessage = str(id)+";"+str(self.data.datetime.datetime(1))+";"+str(self.data1.datetime.datetime(1))+";"+ordertype+";"+str(self.dataclose[1])+";"+str(self.open[1])+";"+str(self.volume[1])+";"+str(self.high[1])+";"+str(self.low[1])+";"+"##buyprice##"+";"+"0"+";"+"0"+";"+str(pricelimit)+";"+str(self.williamsDaily[1])+";"+str(self.rsi10daily[1])+";"+str(self.rsi21daily[1])+";"+str(self.atr[1])+";"+str(self.atrdaily[1])+"\n"
                        switch = False
                        #sys.stdin.read(1)
                    elif self.low[1]<= self.low[0] and self.low[0]<= self.low[-1] and sizeMechaLow>=mecha \
                        and str(self.data1.datetime.datetime(0).time()) == "17:15:00": #  and sizeMechaLow>sizeMechaInfLow
                        self.order = self.buy(data = data1)
                        compra = 1
                        ordertype = "LARGO"
                        id = len(self.data)                      
                        buymessage = str(id)+";"+str(self.data.datetime.datetime(1))+";"+str(self.data1.datetime.datetime(1))+";"+ordertype+";"+str(self.dataclose[1])+";"+str(self.open[1])+";"+str(self.volume[1])+";"+str(self.high[1])+";"+str(self.low[1])+";"+"##buyprice##"+";"+"0"+";"+"0"+";"+str(pricelimit)+";"+str(self.williamsDaily[1])+";"+str(self.rsi10daily[1])+";"+str(self.rsi21daily[1])+";"+str(self.atr[1])+";"+str(self.atrdaily[1])+"\n"
                        switch = False
                        #sys.stdin.read(1)
                    else:
                        ordertype = "NOORDER"

                    maxday = self.high[1]
                    minday = self.low[1]

                    if  ordertype == "LARGO":
                        #Basic rule
                        pricelimit = minday - exitfilter

                    else:
                        #Basic rule
                        pricelimit = maxday + exitfilter

                if str(self.data1.datetime.datetime(0).time()) == "17:15:00" or ordertype != "NOORDER":                            
                        self.log('BUY %s, C%.2f, V%.2f, H%.2f, L%.2f, STOPLOSS= %.2f' % (ordertype,self.dataclose[1],self.volume[1],self.high[1],self.low[1],pricelimit))
                   

            else:

                if  ordertype == "LARGO" :
                        profit = self.dataclose1[0] - buyprice
                        atr = int((self.dataclose1[-1]-self.dataclose1[0])/self.atr[0])
                else:
                        profit = buyprice - self.dataclose1[0]
                        atr = int((self.dataclose1[0]-self.dataclose1[-1])/self.atr[0])
                
                self.log('15minutos Close %.2f, Vol %.2f, High %.2f, Low %.2f, Beneficio %.2f, StopLoss %.2f' % (self.dataclose1[0],self.volume1[0],self.high1[0],self.low1[0],profit,pricelimit))
                
                if  self.data.datetime.datetime(1).date() > self.data1.datetime.datetime(0).date() and not switchnp:
                    if  ordertype == "LARGO" :
                        event = 'Change day, Long'
                        #Basic rule
                        pricelimit = self.low1[-10]

                    else:
                        event = 'Change day, Short'
                        #Basic Rule
                        pricelimit = self.high1[-10]    

                if switchnp:
                    if  ordertype == "LARGO" :
                        if self.dataclose1[0] - buyprice >= nolose and buyprice+noloseamount>pricelimit:
                           
                            event = 'SwitchNP, Long'
                            #Basic Rule
                            pricelimit = buyprice + noloseamount
                            switchnp = False
                        
                    else:
                        if buyprice - self.dataclose1[0] >= nolose and buyprice-noloseamount<pricelimit:
                            event = 'SwitchNP, Short'
                            #Basic Rule
                            pricelimit = buyprice - noloseamount
                            switchnp = False
                    self.log(event) 
      
                #sys.stdin.read(1)
                if  ordertype == "LARGO" :
                    if self.dataclose1[0] <= pricelimit:
                        self.order = self.sell(data = data1)
                        switchnp = True
                        sellmessage = str(id)+";"+str(self.data.datetime.datetime(1))+";"+str(self.data1.datetime.datetime(0))+";"+"VENTAL"+";"+str(self.dataclose1[0])+";"+str(self.open1[0])+";"+str(self.volume1[0])+";"+str(self.high1[0])+";"+str(self.low1[0])+";"+str(buyprice)+";"+"##sellprice##"+";"+str(profit)+";"+str(pricelimit)+";"+str(self.williams[0])+";"+str(self.rsi10[0])+";"+str(self.rsi21[0])+";"+str(self.atr[0])+";"+str(self.atrdaily[1])+"\n"
                        venta = 1
                else:
                    if self.dataclose1[0] >= pricelimit:
                        self.order = self.sell(data = data1) 
                        switchnp = True
                        sellmessage = str(id)+";"+str(self.data.datetime.datetime(1))+";"+str(self.data1.datetime.datetime(0))+";"+"VENTAC"+";"+str(self.dataclose1[0])+";"+str(self.open1[0])+";"+str(self.volume1[0])+";"+str(self.high1[0])+";"+str(self.low1[0])+";"+str(buyprice)+";"+"##sellprice##"+";"+str(profit)+";"+str(pricelimit)+";"+str(self.williams[0])+";"+str(self.rsi10[0])+";"+str(self.rsi21[0])+";"+str(self.atr[0])+";"+str(self.atrdaily[1])+"\n"
                        venta = 1
                if venta == 0:
                    fileWriter.write(str(id)+";"+str(self.data.datetime.datetime(1))+";"+str(self.data1.datetime.datetime(0))+";"+event+";"+str(self.dataclose1[0])+";"+str(self.open1[0])+";"+str(self.volume1[0])+";"+str(self.high1[0])+";"+str(self.low1[0])+";"+"0"+";"+"0"+";"+str(profit)+";"+str(pricelimit)+";"+str(self.williams[0])+";"+str(self.rsi10[0])+";"+str(self.rsi21[0])+";"+str(self.atr[0])+";"+str(self.atrdaily[1])+"\n")    
               
            lastdate = self.data.datetime.datetime(0)

def printTradeAnalysis(analyzer):
        #Get the results we are interested in
        total_open = analyzer.total.open
        total_closed = analyzer.total.closed
        total_won = analyzer.won.total
        total_lost = analyzer.lost.total
        win_streak = analyzer.streak.won.longest
        lose_streak = analyzer.streak.lost.longest
        pnl_net = round(analyzer.pnl.net.total,2)
        strike_rate = (total_won / total_closed) * 100
        #Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate','Win Streak', 'Losing Streak', 'PnL Net']
        r1 = [total_open, total_closed,total_won,total_lost]
        r2 = [strike_rate, win_streak, lose_streak, pnl_net]
        #Check which set of headers is the longest.
        if len(h1) > len(h2):
            header_length = len(h1)
        else:
            header_length = len(h2)
        #Print the rows
        print_list = [h1,r1,h2,r2]
        row_format ="{:<15}" * (header_length + 1)
        print("Trade Analysis Results:")
        for row in print_list:
            print(row_format.format('',*row))

def printSQN(analyzer):
    sqn = round(analyzer.sqn,2)
    print('SQN: {}'.format(sqn))

if __name__ == '__main__':

    i=0
    
    switch = True
    switchnp = True
    id=0
    venta = 0
    compra = 0
    buymessage = ""
    sellmessage = ""

    pricelimit = 0
    buyprice = 0
    sellprice = 0
    minday = 0
    maxday = 0
    ordertype = 'NOORDER'
    exitfilter = 10
    nolose = 85
    noloseamount = 30
    mecha = 75

    lastdate = datetime.datetime.now()
    cerebro = bt.Cerebro()

    cerebro.addstrategy(TestStrategy)

    modpath = "C:\\Azul\\Trading\\"
    fileWriter = open(modpath+'ResultsTrading.csv','w')

    fileWriter.write(str("id")+";"+str("DateDay")+";"+str("Date15min")+";"+"EventType"+";"+str("Close")+";"+str("Open")+";"+str("Volume")+";"+str("High")+";"+str("Low")+";"+str("BuyPriceOp")+";"+str("SellPriceOp")+";"+str("Profit")+";"+str("StopLimit")+";Williams;RSI10;RSI21;ATR;ATRDaily"+"\n")    

    datapath15 = os.path.join(modpath, 'Datos15MiniIbex.csv')
    datapath = os.path.join(modpath, 'DatosDailyIndiceIbex.csv')

    data1 = bt.feeds.BacktraderCSVData(dataname=datapath15,
        separator=';',
        dtformat='%Y-%m-%d',
        fromdate=datetime.datetime(2010, 1, 1),
        reverse=True,

        datetime=0,
        time=1,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6,
        openinterest=7

        
    )   

    # Add the Data Feed to Cerebro
    data = bt.feeds.BacktraderCSVData(dataname=datapath,
        separator=';',
        dtformat='%Y-%m-%d',
        fromdate=datetime.datetime(2010, 1, 1),
        reverse=True,

        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=6

        )
    
    cerebro.adddata(data)
    cerebro.adddata(data1)
    
    
    # Add analyzer
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

    # Set our desired cash start
    cerebro.broker.setcash(500000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    thestrats = cerebro.run()
    thestrat = thestrats[0]
    fileWriter.close()

    ## Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Print analyzer
    printTradeAnalysis(thestrat.analyzers.ta.get_analysis())
    printSQN(thestrat.analyzers.sqn.get_analysis())
    



