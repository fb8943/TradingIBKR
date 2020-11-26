from datetime import datetime,timedelta
import sys
import threading
import time
import queue
import tkinter as tk
from inspect import getframeinfo, currentframe
from tkinter import ttk
import numpy as np
import talib
from ibapi.common import BarData
import datetime as dt

from Source.OnesClasses import OnePortfolio, OneContract, OneTickWithInfo, OneStock, OnePanel
from Source.UtilitiesClasses import toMessage, disLog, convertToHigher, convertToHigherBarData
import queue
from collections import deque


#this class will manage the Watch panels
class UtilityWatch:
    def __init__(self,gui):
        self.gui=gui
        self.watchButtons()
        #self.myQueue=queue.Queue()
        #self.myQueue = deque()
        #self.th=myThread(self.myQueue)
        self.th = None
        #self.Panels=[]
        self.Panels ={} #better a dictionary will be easy to access based on tickID
        self.activeStocks = None


    def watchButtons(self):
        paneBtnContracts = tk.PanedWindow(self.gui.tab_watch, height="30", width="700")
        paneBtnContracts.place(x=10, y=10)

        self.bStartWatch = tk.Button(paneBtnContracts, text="Start", command=self.Start)
        self.bStartWatch.pack(side='left')  # place(x=10, y=10)
        self.bStopWatch = tk.Button(paneBtnContracts, text="Stop", command=self.Stop)
        self.bStopWatch.pack(side='left')  # place(x=70, y=10)
        self.bStart1min = tk.Button(paneBtnContracts, text="Start1min", command=self.Start1min)
        self.bStart1min.pack(side='left')  # place(x=70, y=10)
        self.bActivate = tk.Button(paneBtnContracts, text="Activate", command=self.Activate)
        self.bActivate.pack(side='left')  # place(x=70, y=10)
        self.bTest = tk.Button(paneBtnContracts, text="Test", command=self.Test)
        self.bTest.pack(side='left')  # place(x=70, y=10)

    def Test(self):
        st=self.gui.dbLite.getOneStockPandas(28,10)
        print(st[['Date','Open']])
        print(st.tail())

    def Activate(self):
        if self.gui.dbLite==None:
            print("load the database")
            return

        if self.activeStocks==None:
            self.activeStocks = self.gui.dbLite.getActive()

        mes = toMessage("CreatePorfolio", self.activeStocks)
        self.gui.toWat.put(mes)

        self.GridPanel = tk.PanedWindow(self.gui.tab_watch, height="500", width="700",bg='blue')
        self.GridPanel.place(x=10,y=50)
        maxrow=3
        maxcol=3
        self.activeStocks = self.gui.dbLite.getActive()
        OnePanel.master=self.GridPanel
        OnePanel.height=20
        OnePanel.width=300

        row=1
        col=1
        for item in self.activeStocks:
            pn=OnePanel(row,col,self.gui)
            row+=1
            if row> maxrow:
                col+=1
                row=1

            if row>maxrow and col>maxcol:
                print("too many items")
                break

            pn.create(item)
            self.Panels[item.contractID]=pn

            print ('symbol= ',item.contractID,item.symbol)

        for key,value in self.Panels.items():
            print(key,value.x,value.y)
    '''
        class myThread (threading.Thread):
           def __init__(self, q1):
              threading.Thread.__init__(self)
              self.q = q1
    '''
    def StopPanelEngines(self):
        for key, value in self.Panels.items():
            print(key, value.x, value.y)
            msg = toMessage('exit')
            value.panelQue.put(msg)

    def Start(self):
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               "start in watch")

        if self.activeStocks==None:
            self.activeStocks = self.gui.dbLite.getActive()
        #let's verify if the 1 min data is update in the last 60 minute otherwise don't start the watch

        mes = toMessage("CreatePorfolio", self.activeStocks)
        self.gui.toWat.put(mes)

        for item in self.activeStocks:
            dt=self.gui.dbLite.getMaxDateTime(item.contractID)

            FMT1 = '%Y%m%d  %H:%M:%S'
            s1=datetime.strftime(datetime.now(),FMT1)

            tdelta = datetime.strptime(s1, FMT1) - datetime.strptime(dt, FMT1)

            #we need to have download 1 minute less than 1 hours 3600 seconds
            #we set to 3400 because the download of 5 seconds can take some time
            if tdelta.seconds>3000:
                print("you don't have enough data on 1 minute, please download 1 minute first")
                return
            else:
                print('start sending to load 1 min',item.contractID)
                #toGui = toMessage('load1min', item.contractID)
                #self.gui.toGui.put(toGui)

                self.gui.load1min(item.contractID)
                time.sleep(1)

        time.sleep(3)
        print('I finish to upload 1 min')

#        mes = toMessage("start5sec", self.activeStocks)
#        self.gui.toWat.put(mes)

        #print(len(self.activeStocks),self.activeStocks[0].symbol)

        for item in self.activeStocks:
            toTWS = toMessage('Start5SecWatch', item)
            self.gui.toTws.put(toTWS)
            #break

        time.sleep(5) #we need time to be able to have continuous series

        for item in self.activeStocks:
            toTWS = toMessage('histnew5secOneTime', item)
            self.gui.toTws.put(toTWS)
            #break

    def Stop(self):

        mes = toMessage("stop5sec", None)
        self.gui.toWat.put(mes)
        for items in self.activeStocks:
            toTWS = toMessage('Stop5SecWatch', items)
            self.gui.toTws.put(toTWS)


    def Start1min(self):
        self.activeStocks = self.gui.dbLite.getActive()
        for item in self.activeStocks:
            toTWS = toMessage('histnew', item)
            self.gui.toTws.put(toTWS)


    def run(self):
          while len(self.q)>0:
            #print("Starting " + str(self.q.qsize()))
            print("Starting " + str(len(self.q)))
            time.sleep(3)
            #print("Exiting " + str(self.q.qsize()))
            print("Exiting " + str(len(self.q)))
          print('i got of thread')




#this class will manage the watch process
class Watch:
    def __init__(self, toTws, toGui, toPre):
        self.toTws = toTws
        self.toPre = toPre
        self.toGui = toGui
        self.oneportfolio=OnePortfolio() #create the portfolion that will be watch
        self.exit = False
        self.creatPort=False

    def createPortfolio(self,contracts):
        if self.creatPort==True:
            return

        for item in contracts:
            self.oneportfolio.stocks[item.contractID]=OneStock(item,item.contractID)
            #self.oneportfolio.stocks[item.contractID].ge
            print('createPorfolio',item.contractID,self.oneportfolio.stocks[item.contractID].tickid)
        self.creatPort=True

    def run(self):
        while (self.exit == False):
            time.sleep(1)
            #print("run in predict")
            self.checkMsg()
            if self.exit == True:
                disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                       "get out from run in predict2")
                break
            # self.checkMsgFromTws()

        print("get out from run in predict")
        pass

    #check the messages that will come to watch
    def checkMsg(self):
        try:
            while not self.toPre.empty():
                msg: toMessage = self.toPre.get_nowait()
                if msg.purpose == "exit":
                    disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                           msg.purpose, "i got exit from gui in predict")
                    self.exit = True
                if msg.purpose == "CreatePorfolio":
                    self.createPortfolio(msg.obj)
                if msg.purpose == "stop5sec":

                    print("i can display the portfolio in stop5sec")

                    # tickid=msg.obj.contractID
                    #
                    # f = open(str(tickid) + "-5sec-final.txt", "a")
                    # for item in self.oneportfolio.stocks[tickid].bars5sec:
                    #     f.write(
                    #         item.date + ' ' + str(item.open) + ' ' + str(item.high) + ' ' + str(item.low) + ' ' + str(
                    #             item.close) + ' ' + str(item.volume) + '\r\n')
                    # f.close()
                    #
                    # f = open(str(tickid) + "-1min-final.txt", "a")
                    # for item in self.oneportfolio.stocks[tickid].bars1min:
                    #     f.write(
                    #         item.date + ' ' + str(item.open) + ' ' + str(item.high) + ' ' + str(item.low) + ' ' + str(
                    #             item.close) + ' ' + str(item.volume) + '\r\n')
                    # f.close()

                if msg.purpose== "5sec":
                    self.do5sec(msg.obj)
                if msg.purpose == "5secHist":
                    print("5secHist")
                    self.insert5sec(msg.obj)
                if msg.purpose=="data1min":
                    #this is data for 1 min
                    self.data1min(msg.obj)

                pass
        except queue.Empty:
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   "empty")
            pass


    def data1min(self,obj):
        #let's load the data
        tickID=obj[0]

        #print('data1min,watchclasses.py Ticker is ',tickID)
        for item in obj[1].bars1min:
            #let's add them manually instead of assign
            self.oneportfolio.stocks[tickID].bars1min.append(item)


        #let's set the panda too
        self.oneportfolio.stocks[tickID].panda1min=obj[2]

        self.oneportfolio.stocks[tickID].is1minDownloaded = True
        print('data1min -  i am good with data1min ',tickID)

        #print('data1min','data is loaded for tickid',tickID)


    def dispBar(self,bar:BarData):
        print(bar.date,bar.open, bar.open, bar.high, bar.low, bar.close, bar.volume)

    def displayPorfolio(self):
        for key,value in self.oneportfolio.stocks.items():
            print('key',key)
            for item in value.bars5sec:
                self.dispBar(item)

        pass



    #this function will insert the history just downloaded in active list
    def insert5sec(self, obj):
        tickID=obj[0]
        #print("tickid=",tickID)

        format = '%Y%m%d  %H:%M:%S'
        #from hist everything is in bars1min even the 5sec
        for item in reversed(obj[1].oneStock.bars1min):
            #print(item.date,item.open,item.high,item.low,item.close,item.volume)
            #print("item.date=",item.date,"self.oneportfolio.stocks[tickID].bars5sec[0].date=",self.oneportfolio.stocks[tickID].bars5sec[0].date)

            it = BarData()
            it.date = item.date
            it.high = item.high
            it.open = item.open
            it.low = item.low
            it.close = item.close
            it.volume = item.volume
            it.barCount = item.barCount
            it.average = item.average
           #print('insert5sec len=',len(self.oneportfolio.stocks[tickID].bars5sec))
            if len(self.oneportfolio.stocks[tickID].bars5sec)>0:
                if item.date < self.oneportfolio.stocks[tickID].bars5sec[0].date:
                     self.oneportfolio.stocks[tickID].bars5sec.insert(0,it)
            else:
                self.oneportfolio.stocks[tickID].bars5sec.insert(0, it)

        # for item in  self.oneportfolio.stocks[tickID].bars5sec:
        #     f = open(str(tickID)+"-5sec-just-after-the insertion.txt", "a")
        #     for item in self.oneportfolio.stocks[tickID].bars5sec:
        #         f.write(item.date+' '+str(item.open)+' '+str(item.high)+' '+str(item.low)+' '+str(item.close)+' '+str(item.volume)+'\r\n')
        #     f.close()

        self.oneportfolio.stocks[tickID].is5secDownloaded=True
        print('insert54sec - just finish update the 5sec series',tickID)


    def do5sec(self, obj):
        self.dispBar(obj[1])
        tickID=obj[0]
        # this list of BarData

        self.oneportfolio.stocks[obj[0]].bars5sec.append(obj[1])

        if (self.oneportfolio.stocks[tickID].is1minDownloaded == True and
            self.oneportfolio.stocks[tickID].is5secDownloaded==True) :

           self.updateOneStock(tickID, obj[1])

        print('do5sec', obj[1])
        print('do5sec is1min donwloaded,is5sec downloaded ?',self.oneportfolio.stocks[tickID].is1minDownloaded,self.oneportfolio.stocks[tickID].is5secDownloaded)

    #this will update 1 min, 5 min, 30 min etc
    def updateOneStock(self,tickID,item:BarData):
        dt=self.oneportfolio.stocks[tickID].bars1min[len(self.oneportfolio.stocks[tickID].bars1min) - 1].date
        dt_obj=datetime.strptime(dt, '%Y%m%d  %H:%M:%S')
       # print('first',dt,dt_obj)
        dt_obj+=timedelta(seconds=60)
        dt=dt_obj.strftime("%Y%m%d  %H:%M:%S")
       # print('second',dt,dt_obj)

        print('updateOneStock- is 1minUpToDate?',self.oneportfolio.stocks[tickID].is1minUpToDate)

        if(self.oneportfolio.stocks[tickID].is1minUpToDate==False):
            res=convertToHigherBarData(self.oneportfolio.stocks[tickID].bars5sec,'1min')
            #next time we don't want to repopulate everything

            self.oneportfolio.stocks[tickID].is1minUpToDate =True
            rowForPandas=[]
            for item in res:
                #item is OneTick and
                if item.date >= dt: #compare the time to see if we can add this item
                    self.oneportfolio.stocks[tickID].bars1min.append(item)
                    
                    dic = self.populate_dic(item)
                    rowForPandas.append(dic)

            if len(rowForPandas)>0:
                self.oneportfolio.stocks[tickID].panda1min=\
                    self.oneportfolio.stocks[tickID].panda1min.append(rowForPandas,ignore_index=True)

            x = np.array(self.oneportfolio.stocks[tickID].panda1min['Close'], dtype=float)
            # print(x)
            output = talib.EMA(x, timeperiod=20)
            colname = 'EMA' + str(20)
            self.oneportfolio.stocks[tickID].panda1min[colname] = output
            print(self.oneportfolio.stocks[tickID].panda1min.tail(3))

            #let's build the 5 min and 30 min

            rowForPandas = []
            res5=convertToHigherBarData(self.oneportfolio.stocks[tickID].bars1min,'5min')
            for item in res5:
                self.oneportfolio.stocks[tickID].bars5min.append(item)
                dic = self.populate_dic(item)
                rowForPandas.append(dic)


            self.oneportfolio.stocks[tickID].panda5min =\
                self.oneportfolio.stocks[tickID].panda5min.append(rowForPandas, ignore_index=True)
            #print(self.oneportfolio.stocks[tickID].panda5min.tail())

            rowForPandas = []
            res30=convertToHigherBarData(self.oneportfolio.stocks[tickID].bars1min,'30min')
            for item in res30:
                self.oneportfolio.stocks[tickID].bars30min.append(item)
                dic = self.populate_dic(item)
                rowForPandas.append(dic)

            self.oneportfolio.stocks[tickID].panda30min = \
                self.oneportfolio.stocks[tickID].panda30min.append(rowForPandas, ignore_index=True)
            #print(self.oneportfolio.stocks[tickID].panda30min.tail())


        else:
            dt=datetime.strptime(item.date, '%Y%m%d  %H:%M:%S')
            # update 1 min,5min, 30 min
            self.add_one_bar(dt, item, self.oneportfolio.stocks[tickID].bars1min,1)
            self.add_one_bar(dt, item, self.oneportfolio.stocks[tickID].bars5min, 5)
            self.add_one_bar(dt, item, self.oneportfolio.stocks[tickID].bars30min, 30)

            self.oneportfolio.stocks[tickID].panda1min=\
                self.add_one_bar_to_pandas(dt, item, self.oneportfolio.stocks[tickID].panda1min,1)
            self.oneportfolio.stocks[tickID].panda5min = \
                self.add_one_bar_to_pandas(dt, item, self.oneportfolio.stocks[tickID].panda5min, 5)
            self.oneportfolio.stocks[tickID].panda30min = \
                self.add_one_bar_to_pandas(dt, item, self.oneportfolio.stocks[tickID].panda30min, 30)

            print(self.oneportfolio.stocks[tickID].panda30min.tail(3))
            #self.add_one_bar_to_pandas(dt, item, self.oneportfolio.stocks[tickID].panda5min, 5)
            #self.add_one_bar_to_pandas(dt, item, self.oneportfolio.stocks[tickID].panda30min, 30)

               #let's update the Panels
            toGui=toMessage('UpdatePanels',[tickID,self.oneportfolio.stocks[tickID].bars30min[-1].high,
                            self.oneportfolio.stocks[tickID].bars5min[-1].high,
                            self.oneportfolio.stocks[tickID].bars1min[-1].high])
            self.toGui.put(toGui)

    def populate_dic(self, item):
        dic = {}
        dic['Date'] = item.date
        dic['Open'] = item.open
        dic['High'] = item.high
        dic['Low'] = item.low
        dic['Close'] = item.close
        dic['Volume'] = item.volume
        dic['Count'] = item.barCount
        dic['Average'] = item.average
        return dic

    def add_one_bar(self, dt, item, series,interval):
        if dt.second == 0 and dt.minute % interval==0:
            # we need a new bar
            it = BarData()
            it.date = item.date
            it.high = item.high
            it.open = item.open
            it.low = item.low
            it.close = item.close
            it.volume = item.volume
            it.barCount = item.barCount
            it.average = item.average
            series.append(it)
        else:
            # just update the last bar
            series[-1].high = max(series[-1].high,item.high)
            series[-1].low = min(series[-1].low,item.low)
            series[-1].close = item.close
            series[-1].volume += item.volume
            series[-1].barCount+=item.barCount

    def add_one_bar_to_pandas(self, dt, item, series,interval):
        if dt.second == 0 and dt.minute % interval==0:
            # we need a new bar
            dic=self.populate_dic(item)
            row=[]
            row.append(dic)
            series=series.append(row,ignore_index=True)
            print('panda length= ',len(series))
        else:
            # just update the last bar
            a=series.iloc[-1]['High']
            series.iloc[-1,series.columns.get_loc('High')] = max(a,item.high)
            a=series.iloc[-1]['Low']
            series.iloc[-1,series.columns.get_loc('Low')] = min(a, item.low)

            series.iloc[-1,series.columns.get_loc('Close')] = item.close
            #df.iloc[-1, df.columns.get_loc('c')] = 42
            #series.iloc[-1]['Volume'] += item.volume
            series.iloc[-1,series.columns.get_loc('Volume')] += item.volume
            series.iloc[-1,series.columns.get_loc('Count')] += item.barCount

        print('add_one_bar_to_pandas')
        return series


def runWat(toTws, toGui, toWat):
    wat = Watch(toTws, toGui, toWat)
    wat.run()
