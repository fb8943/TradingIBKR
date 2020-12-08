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

from ibapi.contract import Contract
from ibapi.order import Order

from Source.OnesClasses import OnePortfolio, OneContract, OneTickWithInfo, OneStock, OnePanel
from Source.UtilitiesClasses import toMessage, disLog, convertToHigher, convertToHigherBarData, \
    convertToHigherBarDataDic, calculateWT, calculateWT2
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
        self.eTimeFrame = tk.Entry(paneBtnContracts, width=50)
        self.eTimeFrame.insert(0, "1min,5min,10min,info,info2")
        self.eTimeFrame.pack(side='left')

    def Test(self):
        #st=self.gui.dbLite.getOneStockPandas(28,10)


        return
        st=self.gui.dbLite.getOneStockDic(28,3000,'NO')

        for i,j in zip(st['D1min'][-20:],st['C1min'][-20:]):
            print(i,j)
        print('\t\n')
        convertToHigherBarDataDic(st, src='1min', dest='5min')

        #for i,j in zip(st['D5min'][-10:],st['C5min'][-10:]):
        #    print(i,j)

        #print('\t\n')
        convertToHigherBarDataDic(st, src='1min', dest='30min')
        calculateWT(st, 1)
        calculateWT(st, 5)
        calculateWT(st, 30)

        calculateWT2(st, '1min')
        calculateWT2(st, '5min')
        calculateWT2(st, '30min')
        print('cros=',st['WTval1min'])
        print('cros=', st['WTval5min'])
        print('cros=', st['WTval30min'])

        print('1min',st['D1min'][-1],st['WTwt11min'][-1],st['WTwt21min'][-1])
        print('1min', st['D1min'][-2], st['WTwt11min'][-2], st['WTwt21min'][-2])
        print('1min', st['D1min'][-3], st['WTwt11min'][-3], st['WTwt21min'][-3])

        print('\r\n')
        print('5min', st['WTwt15min'][-1], st['WTwt25min'][-1])
        print('5min', st['WTwt15min'][-2], st['WTwt25min'][-2])
        print('5min', st['WTwt15min'][-3], st['WTwt25min'][-3])
        print('\r\n')
        print('30min', st['WTwt130min'][-1], st['WTwt230min'][-1])
        print('30min', st['WTwt130min'][-2], st['WTwt230min'][-2])
        print('30min', st['WTwt130min'][-3], st['WTwt230min'][-3])


        print('\r\n\r\n')
        print('cros=',st['WT2val1min'])
        print('cros=', st['WT2val5min'])
        print('cros=', st['WT2val30min'])

        print('1min', st['D1min'][-1], st['WT2wt11min'][-1], st['WT2wt21min'][-1])
        print('1min', st['D1min'][-2], st['WT2wt11min'][-2], st['WT2wt21min'][-2])
        print('1min', st['D1min'][-3], st['WT2wt11min'][-3], st['WT2wt21min'][-3])

        print('\r\n')
        print('5min', st['WT2wt15min'][-1], st['WT2wt25min'][-1])
        print('5min', st['WT2wt15min'][-2], st['WT2wt25min'][-2])
        print('5min', st['WT2wt15min'][-3], st['WT2wt25min'][-3])
        print('\r\n')
        print('30min', st['WT2wt130min'][-1], st['WT2wt230min'][-1])
        print('30min', st['WT2wt130min'][-2], st['WT2wt230min'][-2])
        print('30min', st['WT2wt130min'][-3], st['WT2wt230min'][-3])

    def Activate(self):
        self.timeframe=self.eTimeFrame.get().split(",")

        if self.gui.dbLite==None:
            print("load the database")
            return

        mes=toMessage("timeframe",self.timeframe)
        self.gui.toWat.put(mes)

        if self.activeStocks==None:
            self.activeStocks = self.gui.dbLite.getActive()

        mes = toMessage("CreatePorfolio", self.activeStocks)
        self.gui.toWat.put(mes)

        self.GridPanel = tk.PanedWindow(self.gui.tab_watch, height="500", width="700",bg='blue')
        self.GridPanel.place(x=10,y=50)
        maxrow=30
        maxcol=1
        self.activeStocks = self.gui.dbLite.getActive()
        OnePanel.master=self.GridPanel
        OnePanel.height=20
        OnePanel.width=300

        row=1
        col=1
        for item in self.activeStocks:
            pn=OnePanel(row,col,self.gui,self.timeframe)
            row+=1
            if row> maxrow:
                col+=1
                row=1

            if row>maxrow and col>maxcol:
                print("too many items")
                break

            pn.create(item)
            #print('item.contractID in activate',item.contractID)
            self.Panels[item.contractID]=pn

            #print ('symbol= ',item.contractID,item.symbol)

        #for key,value in self.Panels.items():
        #    print(key,value.x,value.y)
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
            # print('symbol',self.oneportfolio.stocks[item.contractID].contract.symbol)
            # print('ordersize', self.oneportfolio.stocks[item.contractID].contract.ordersize)

            # self.oneportfolio.stocks[item.contractID].order['OrderSize']=item.ordersize
            # self.oneportfolio.stocks[item.contractID].order['StopSize'] = item.stopsize
            # self.oneportfolio.stocks[item.contractID].order['TimeFrame'] = item.orderextra

            #self.oneportfolio.stocks[item.contractID].ge
            #print('createPorfolio',item.contractID,self.oneportfolio.stocks[item.contractID].tickid)
        self.creatPort=True

    def run(self):
        while (self.exit == False):
            time.sleep(1)
            #print("run in predict")
            self.checkMsg()
            if self.exit == True:
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
                elif msg.purpose=="tickbytick":
                    self.tickbytick(msg.obj)
                elif msg.purpose == "5secHist":
                    print("5secHist")
                    self.insert5sec(msg.obj)
                elif msg.purpose=="data1min":
                    #this is data for 1 min
                    self.data1min(msg.obj)
                elif msg.purpose=="timeframe":
                    self.timeframe=msg.obj
                else:
                    print("message unkown in checkMsg in WatchClasses")

                pass
        except queue.Empty:
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   "empty")
            pass


    def tickbytick(self,obj):
        conID=obj[0]
        if len(self.oneportfolio.stocks[conID].data['DTbT'])==0:
            #it's first bar
            self.oneportfolio.stocks[conID].data['DTbT'].append(obj[1])#date
            self.oneportfolio.stocks[conID].data['OTbT'].append(obj[2])
            self.oneportfolio.stocks[conID].data['HTbT'].append(obj[3])
            self.oneportfolio.stocks[conID].data['LTbT'].append(obj[2])
            self.oneportfolio.stocks[conID].data['CTbT'].append(obj[3])
        else:

            if item[0][12:14]==res[-1][0][12:14]:
                #we are in the same minute
                res[-1][2]=max(res[-1][2],item[2]) #high
                res[-1][3] =min(res[-1][3], item[1]) #low
                res[-1][4]=item[2] #close will be the last high
            else:
                #add for a new minute
                item[0]=item[0][:15]+"XX"
                res.append([item[0],item[1],item[2],item[1],item[2]])#date,open,high,low,close


    def data1min(self,obj):
        #let's load the data
        tickID=obj[0]

        self.oneportfolio.stocks[tickID].data.update(obj[1])
        self.oneportfolio.stocks[tickID].is1minDownloaded = True
        print('data1min -  i am good with data1min ', tickID)
        return
        #below is the old code



    def displayBar(self, bar:BarData):
        print(bar.date,bar.open, bar.open, bar.high, bar.low, bar.close, bar.volume)

    def displayPorfolio(self):
        for key,value in self.oneportfolio.stocks.items():
            print('key',key)
            for item in value.bars5sec:
                self.displayBar(item)

        pass



    #this function will insert the history just downloaded in active list
    def insert5sec(self, obj):
        tickID=obj[0]
        #print("tickid=",tickID)

        format = '%Y%m%d  %H:%M:%S'
        #from hist everything is in bars1min even the 5sec
        for item in reversed(obj[1].oneStock.bars1min):
            if len(self.oneportfolio.stocks[tickID].data['D5sec'])>0:
                if item.date < self.oneportfolio.stocks[tickID].data['D5sec'][0]:
                     self.oneportfolio.stocks[tickID].insertBarToData('5sec',item,0)
            else:
                self.oneportfolio.stocks[tickID].insertBarToData('5sec',item,0)
        self.oneportfolio.stocks[tickID].is5secDownloaded=True
        print('insert54sec - just finish update the 5sec series',tickID)
        return


        # for item in  self.oneportfolio.stocks[tickID].bars5sec:
        #     f = open(str(tickID)+"-5sec-just-after-the insertion.txt", "a")
        #     for item in self.oneportfolio.stocks[tickID].bars5sec:
        #         f.write(item.date+' '+str(item.open)+' '+str(item.high)+' '+str(item.low)+' '+str(item.close)+' '+str(item.volume)+'\r\n')
        #     f.close()




    def do5sec(self, obj):
        #self.displayBar(obj[1])
        tickID=obj[0]
        # this list of BarData

        self.oneportfolio.stocks[tickID].addBarToData('5sec',obj[1])
        #self.oneportfolio.stocks[obj[0]].bars5sec.append(obj[1])

        #print('ipdateOneStock ', self.oneportfolio.stocks[tickID].is1minDownloaded,
        #      self.oneportfolio.stocks[tickID].is5secDownloaded)

        if (self.oneportfolio.stocks[tickID].is1minDownloaded == True and
            self.oneportfolio.stocks[tickID].is5secDownloaded==True) :


                self.updateOneStock(tickID, obj[1])

        #print('do5sec', obj[1])
        #print('do5sec is1min donwloaded,is5sec downloaded ?',self.oneportfolio.stocks[tickID].is1minDownloaded,self.oneportfolio.stocks[tickID].is5secDownloaded)

    #this will update 1 min, 5 min, 30 min etc
    def updateOneStock(self,tickID,item:BarData):
        '''
        dt=self.oneportfolio.stocks[tickID].bars1min[len(self.oneportfolio.stocks[tickID].bars1min) - 1].date
        dt_obj=datetime.strptime(dt, '%Y%m%d  %H:%M:%S')
        dt_obj+=timedelta(seconds=60)
        dt=dt_obj.strftime("%Y%m%d  %H:%M:%S")
        '''

        #print('updateOneStock- is 1minUpToDate?',self.oneportfolio.stocks[tickID].is1minUpToDate)
        d = self.oneportfolio.stocks[tickID].data
        symbol=self.oneportfolio.stocks[tickID].contract.symbol
        #print('symbol=', symbol)
        if(self.oneportfolio.stocks[tickID].is1minUpToDate==False):
            #res=convertToHigherBarData(self.oneportfolio.stocks[tickID].bars5sec,'1min')
            #convert from 5sec to 1 min
            print('is1minUpToDate is false')
            convertToHigherBarDataDic(d,'5sec','1min')
            for item in self.timeframe:
                if item not in ['1min','info','info2']:
                    #print('item in update one stock',item)
                    convertToHigherBarDataDic(d, '1min', item)




            self.oneportfolio.stocks[tickID].is1minUpToDate = True

            #let's find the open on one minute
            find = False
            i=-1
            while find==False:
                if d['D1min'][i][10:]=='06:30:00': # we can find the end of previous day but ZS is not ending at 13:00
                    #print('find open ',d['D1min'][i][10:],d['O1min'][i])
                    d['Open']=float(d['C1min'][i])
                    find=True
                i-=1

            #lets do WT
            start=time.time()
            end=time.time()


            #next time we don't want to repopulate everything

        else:
            #print('do 5 sec',item)
            self.add_one_bar_to_dict(item, d, "1min")
            calculateWT2(self.oneportfolio.stocks[tickID].data, "1min")
            for key in self.timeframe:
                if key not in ['1min', 'info','info2']:
                    #print('i add one item to dictionary', key)
                    self.add_one_bar_to_dict(item, d, key)
                    calculateWT2(d, key)
            '''
            self.add_one_bar_to_dict(item,d,1)
            self.add_one_bar_to_dict(item, d, 5)
            self.add_one_bar_to_dict(item, d, 30)
            calculateWT2(self.oneportfolio.stocks[tickID].data, "1min")
            calculateWT2(self.oneportfolio.stocks[tickID].data, "5min")
            calculateWT2(self.oneportfolio.stocks[tickID].data, "30min")
            '''

            today_change=float(item.close)-d['Open']
            diclabel={}
            #print('position ',self.oneportfolio.stocks[tickID].order['Position'])
            for key in self.timeframe:
                if key=='info':
                    diclabel[key] =[str(item.close)+" "+item.date[15:],'white']
                elif key=='info2':
                    diclabel[key] =["{:+.2f}".format(today_change),"green" if today_change>0  else "red"]
                else:
                    str2=str(d['WT2val'+key][0])+" "+"{:.2f}".format(abs(d['WT2val'+key][1]-d['WT2val'+key][2]))

                    if key==self.oneportfolio.stocks[tickID].contract.orderextra:
                        #print("key ",key)
                        if d['WT2val' + key][0] == 1 and d['WT2col' + key] == 'lime':
                            self.doOrder("BUY",self.oneportfolio.stocks[tickID])
                            print('buy')

                        elif d['WT2val' + key][0] == 1 and d['WT2col' + key] == 'pink':
                            print('sell')
                            self.doOrder("SELL", self.oneportfolio.stocks[tickID])

                    '''
                    if key in ["1min","5min","10min"]:
                         if d['WT2val' + key][0]==1 and d['WT2col'+key]=='lime':
                            if d['position'+key]==-100:
                                str1='buy at '+key+' tickID=' + str(tickID)+' price= '+str(item.close)+' datetime= '+item.date+' position=0'
                                print(str1)
                                self.writetofile(symbol+key,str1)
                                d['position'+key] = 0
                            if d['position'+key]==0:
                                str1='buy at ' + key + ' tickID='+ str(tickID)+ ' price= '+ str(item.close)+ ' datetime= '+ item.date+ ' position=100'
                                print(str1)
                                self.writetofile(symbol+key, str1)
                            d['position'+key] = 100

                        elif  d['WT2val' + key][0] == 1 and d['WT2col' + key] == 'pink':
                            if d['position'+key]==100:
                                str1='sell at '+key+' tickID='+str(tickID)+' price= '+str(item.close)+' datetime= '+item.date+' position=0'
                                print(str1)
                                self.writetofile(symbol+key, str1)
                                d['position'+key] = 0
                            if d['position'+key]==0:
                                str1='sell at ' + key + ' tickID='+ str(tickID)+ ' price= '+ str(item.close)+ ' datetime= '+ item.date+ ' position=-100'
                                print(str1)
                                self.writetofile(symbol+key, str1)
                            d['position'+key] = -100
                    '''


                    diclabel[key]=[str2,d['WT2col'+key]]

            toGui=toMessage('UpdatePanels', [tickID,diclabel])
            '''        
            toGui = toMessage('UpdatePanels', [tickID,\
                    [d['WT2val30min'],d['WT2col30min']],
                    [d['WT2val5min'],d['WT2col5min']],
                    [d['WT2val1min'],d['WT2col1min']],[str(item.close)+" "+item.date[15:],'white'],
                                               ["{:+.2f}".format(today_change),"green" if today_change>0  else "red"]])
            '''
            #20201201 07:24:12
            self.toGui.put(toGui)
            #print("HLC--",d['D1min'][-1],d['H1min'][-1],d['L1min'][-1],d['C1min'][-1])

    def writetofile(self,filename,str1):
             fn=filename+"-tran.txt"
             print(fn)
             f = open(fn, "a")
             f.write(str1+'\r\n')
             f.close()

    def doOrder(self,action,instrument:OneStock):
        contract = Contract()
        contract.symbol = instrument.contract.symbol
        contract.secType = instrument.contract.sectype
        contract.currency = instrument.contract.currency
        contract.exchange = instrument.contract.exchange
        contract.lastTradeDateOrContractMonth = instrument.contract.expire

        #print(contract.symbol, contract.secType, contract.currency, contract.exchange,
        #      contract.lastTradeDateOrContractMonth)

        order = Order()
        #order.action = "BUY"
        order.action = action
        # order.orderType = "LMT"
        order.orderType = "MKT"
        #order.totalQuantity = 1
        ordersize=int(instrument.contract.ordersize)

        if instrument.order['Position']==0:
            order.totalQuantity = ordersize
            if action=='BUY':
                instrument.order['Position'] = ordersize
            else:
                instrument.order['Position'] = -ordersize
        elif instrument.order['Position']==ordersize and action=='SELL':
            order.totalQuantity = ordersize*2
            instrument.order['Position'] = -ordersize
        elif instrument.order['Position']==-ordersize and action=='BUY':
            order.totalQuantity = ordersize * 2
            instrument.order['Position'] = ordersize
        else:
            return #nothing to do
        # order.lmtPrice = 100
        # order.account="U146642"


        print("action=",action,"size=",order.totalQuantity,ordersize,
              "symbol=",contract.symbol,'Position=',instrument.order['Position'])
        toTWS = toMessage('PlaceOrder', ['Nothing', contract, order])
        # print(self.dbLite.getDateTimeToDownload())
        self.toTws.put(toTWS)

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

    def add_one_bar_to_dict(self,item,d,inter):
        dest=inter
        #print("inter= ",inter)
        str1=inter[:-3]
        #print("str1= ",str1)
        interval=int(str1)
        #print('interval is',interval)

        dt = datetime.strptime(item.date, '%Y%m%d  %H:%M:%S')
        if dt.second == 0 and dt.minute % interval == 0:
            d['D' + dest].append(item.date)
            d['O' + dest].append(item.open)
            d['H' + dest].append(item.high)
            d['L' + dest].append(item.low)
            d['C' + dest].append(item.close)
            d['V' + dest].append(item.volume)
            d['N' + dest].append(item.barCount)
            d['A' + dest].append(item.average)
        else:
            d['H' + dest][-1] = max(d['H' + dest][- 1], item.high)
            d['L' + dest][- 1] = min(d['L' + dest][- 1], item.low)
            d['C' + dest][- 1] = item.close
            d['V' + dest][- 1] += item.volume
            d['N' + dest][- 1] += item.average

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
