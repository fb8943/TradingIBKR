#region import
import datetime
import queue
import logging
import sys
import time
from inspect import getframeinfo, currentframe

from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.wrapper import EWrapper, TickType, TickAttribLast, TickAttribBidAsk
from ibapi.contract import Contract
from ibapi.common import BarData, TickerId, TickAttrib, OrderId

#from config import config
#from logutils import init_logger
from Source.ClientClass import TestClient
#endregion import
from Source.OnesClasses import OneContract, OneTick, OneTickWithInfo
from Source.UtilitiesClasses import toMessage, downloadHist, getStepSize, DownloadLimit, disLog
from Source.SQLiteClass import DB

'''
#def makeSimpleContract(symbol, secType = "STK", currency = "USD", exchange = "SMART"):
def makeSimpleContract(symbol="ES", secType = "FUT", currency = "USD", exchange = "GLOBEX", expire="202006"):
    contract = Contract()
    contract.symbol=symbol
    contract.secType=secType
    #contract.currency=currency
    contract.exchange=exchange
    contract.lastTradeDateOrContractMonth=expire
    return contract
'''

def makeSimpleContract(ct:OneContract):
    contract = Contract()
    contract.symbol=ct.symbol
    contract.secType=ct.sectype
    contract.currency=ct.currency
    contract.exchange=ct.exchange
    contract.lastTradeDateOrContractMonth=ct.expire
    #contract.conId=ct.contractID can't to this contract ID is different
    return contract


class TestApp(TestClient, EWrapper):
    """
    Mixin of Client (message sender and message loop holder)
    and Wrapper (set of callbacks)
    """


    def __init__(self, toTws, toGui,toWat):
        EWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.idmarketdata=0#temporary

        self.toTws = toTws
        self.toGui = toGui
        self.toWat = toWat


        self.nKeybInt = 0
        self.started = False
        #self._lastId = None
        self._lastId = 0
        self._file = None
        #self.stepSize={'1 sec':'1800 S','5 sec':'3600 S','10 secs':'14400 S','30 secs':'28800 S','1 min':'2 D','30 mins':'1 M','1 day':'1 Y'}

        #self.oneStock=OneStock(None)
        self.downloadHistInfo={} #will keep the donwload info
        self.nextIDconID={}#to be able to translate nextID to conID
        #self.stop5secnextID={}#will keep the nextID to be able to stop 5 sec
        self.stop_reqTickByTickData={}#will keep the nextID to be able to stop the MarketData
        self.stop_reqRealTimeBars={} #stop 5 sec bars

        self.realTickData={} #will keep the data

    @property
    def nextId(self):
        #self.tws2gui.put(self._lastId)
        self._lastId += 1
        return self._lastId

    def keyboardInterrupt(self):
        """Callback - User pressed Ctrl-C"""
        self.nKeybInt += 1
        if self.nKeybInt == 1:
            msg = "Manual interruption!"
            logging.warn(msg)
            print(msg)
            self._onStop()
        else:
            msg = "Forced Manual interruption!"
            logging.error(msg)
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   msg)
            self.done = True

    def _onStart(self):
        if self.started: return
        self.started = True
        self.onStart()

    def _onStop(self):
        if not self.started: return
        self.onStop()
        self.started = False

    # region GuiMsgProcessors
    # ----------------------------------------------------------------------------

    def exit(self):
        msg=toMessage('exit')
        self.toGui.put(msg)
        """
        Exit from the application
        """
        self.done = True
        self._onStop()

    # endregion GuiMsgProcessors

    # region Callbacks
    # ----------------------------------------------------------------------------

    def onStart(self):
        #logging.info('Main logic started')
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'Main logic started')

    def onStop(self):
        if self._file: self._file.close()
        #logging.info('Main logic stopped')
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'Main logic stopped')

    #this will take the messages from gui
    def onLoopIteration(self): # this is called from ClientClass
        try:
            msg:toMessage = self.toTws.get_nowait()
            #logging.info(f'GUI MESSAGE: {msg}')


            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   'msg.purpose on appclass ',msg.purpose)
            if msg.purpose=='histold':
                if(self.downloadHistInfo.get(msg.obj.contractID)==None):
                    self.downloadHistInfo[msg.obj.contractID]=downloadHist()# need to be outside because we don't want to call many times
                    self.downloadHistInfo[msg.obj.contractID].whatToDownload = 'histold'
                self.getHistOld(msg.obj)
            elif msg.purpose in ['histnew','histnewLevel1']:
                if (self.downloadHistInfo.get(msg.obj.contractID) == None):
                    self.downloadHistInfo[msg.obj.contractID]=downloadHist()
                    self.downloadHistInfo[msg.obj.contractID].whatToDownload=msg.purpose
                self.getHistNew(msg.obj)
            elif msg.purpose=='histnew5secOneTime':
                if (self.downloadHistInfo.get(msg.obj.contractID) == None):
                    self.downloadHistInfo[msg.obj.contractID]=downloadHist()
                    self.downloadHistInfo[msg.obj.contractID].whatToDownload='histnew5secOneTime'
                else:
                    print('i got this contract id',msg.obj.contractID)
                self.getHistNew(msg.obj)
            elif msg.purpose == 'histstop':
                self.downloadHistInfo.pop(msg.obj.contractID)
            elif msg.purpose == 'histgap':
                #not implemented yet it may happen if a stock was download for a long period of time.
                pass
            elif msg.purpose=='marketdata':
                self.getMarketData(msg)
                
            elif msg.purpose=='watchStart':
                self.watchStart(msg)
            elif msg.purpose=='watchStop':
                self.watchStop(msg)

            elif msg.purpose=='Start5SecWatch':
                self.watchStart5Sec(msg)
            elif msg.purpose=='Stop5SecWatch':
                self.Stop5SecWatch(msg)

            elif msg.purpose=='cancelmarketdata':
                self.cancelMktData(self.idmarketdata)

            elif msg.purpose=='connect':
                #self.connect('127.0.0.1', 7496, 1) #live
                self.connect('127.0.0.1', 7497, 1) #paper

            elif msg.purpose=='disconnect':
                self.disconnect()
            elif msg.purpose=='PlaceOrder':
                #self.cancelOrder(msg.obj[0])
                x=self.nextId
                print('order id=',x)
                self.placeOrder(x,msg.obj[1],msg.obj[2])
                #self.cancelOrder(58)
            elif msg.purpose == 'exit':
                self.exit()
            elif msg.purpose == 'database':
                disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                       msg.obj)
                self.dbLite=DB(msg.obj)
                if self.dbLite.conn != '':
                    disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                           'i am connected to database')

            elif msg.purpose == 'bubu':
                disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                       'i am bubu from appclass')
            else:
                #logging.error(f'Unknown GUI message: {msg}')
                disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                       "Unknown GUI messageXXXX")
        except queue.Empty:
            pass

        self.count = 0

    def getMarketData(self, msg):
        toMarket = msg.obj
        ct = makeSimpleContract(toMarket.contract)
        self.idmarketdata = self.nextId
        self.reqMktData(self.idmarketdata, ct, toMarket.genericTickList, False, False, None)

    def getHistOld(self, oneContract:OneContract):
        #DownloadLimit.limit()
        #downloadHist.getStartFutureDate(oneContract.symbol,oneContract.expire)
        #return

        ct = makeSimpleContract(oneContract)

        nextID=self.nextId
        #nextID=oneContract.contractID
        self.nextIDconID[nextID]=oneContract.contractID
        conID=oneContract.contractID
        #print("nextID,contractid",nextID,oneContract.contractID)

        if oneContract.sectype=='FUT':
            self.downloadHistInfo[conID].newestForNewHist=downloadHist.getStartFutureDate(oneContract.symbol,oneContract.expire)

        if self.downloadHistInfo[conID].dateToDownload=='':
            self.downloadHistInfo[conID].dateToDownload=self.dbLite.getMinDateTime(oneContract.contractID)

        if self.downloadHistInfo[conID].oneContract=='':
            self.downloadHistInfo[conID].oneContract=oneContract

        if self.downloadHistInfo[conID].count==0:
            #self.downloadHistInfo[nextID].nextID=nextID
            self.downloadHistInfo[conID].conID=oneContract.contractID
        if oneContract.barsize=='5 secs':
            rth=1
        else:
            rth=0

        self.reqHistoricalData(nextID, ct, self.downloadHistInfo[conID].dateToDownload, getStepSize(oneContract.barsize),
                               oneContract.barsize, oneContract.whattoshow, rth, 1, False, [])

    #this assume we don't have anything in the database
    def getHistNew(self, oneContract:OneContract):
        #DownloadLimit.limit() #to stop the download


        ct = makeSimpleContract(oneContract)

        nextID=self.nextId
        #nextID=oneContract.contractID
        self.nextIDconID[nextID]=oneContract.contractID
        conID=oneContract.contractID
        #print("nextID,contractid",nextID,oneContract.contractID)


        #if we are first time take now moment
        #if (self.downloadHistInfo.dateToDownload == '') and (self.downloadHistInfo.newestForNewHist==''):
        if (self.downloadHistInfo[conID].dateToDownload == '') and (self.downloadHistInfo[conID].newestForNewHist == ''):
            self.downloadHistInfo[conID].newestForNewHist=self.dbLite.getMaxDateTime(conID)

            if self.downloadHistInfo[conID].newestForNewHist=='' or self.downloadHistInfo[conID].newestForNewHist==None: #we should run history
                print("use historyold")
                return
            #self.downloadHistInfo.dateToDownload=datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
            self.downloadHistInfo[conID].dateToDownload = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")


        if self.downloadHistInfo[conID].oneContract=='':
            self.downloadHistInfo[conID].oneContract=oneContract
            #self.downloadHistInfo[nextID].whatToDownload = 'histnew'



        if self.downloadHistInfo[conID].count==0:
            #self.downloadHistInfo[nextID].nextID=nextID
            self.downloadHistInfo[conID].conID=oneContract.contractID

        if (self.downloadHistInfo[conID].lastDateDownload==''):
            self.downloadHistInfo[conID].lastDateDownload = self.dbLite.getMaxDateTime(conID)

        #print(self.downloadHistInfo.lastDateDownload)
        stepSize=getStepSize(oneContract.barsize,self.downloadHistInfo[conID].dateToDownload,self.downloadHistInfo[conID].lastDateDownload)
        #print(stepSize)

        if oneContract.barsize == '5 secs':
            rth = 1
        else:
            rth = 0

        #in case we 5SecOneTime we need to go outside market hour and bar size must be 5 sec
        if self.downloadHistInfo[conID].whatToDownload=='histnew5secOneTime':
            oneContract.barsize = '5 secs'
            rth=0
            stepSize = getStepSize(oneContract.barsize, self.downloadHistInfo[conID].dateToDownload,
                                   self.downloadHistInfo[conID].lastDateDownload)


        self.reqHistoricalData(nextID, ct, self.downloadHistInfo[conID].dateToDownload, stepSize,
                               oneContract.barsize, oneContract.whattoshow, rth, 1, False, [])

    def _write(self, msg):
        if self._file:
            self._file.write(msg)
            self._file.write('\n')
        else:
            print(msg)

    def watchStart(self, msg):
            ct = makeSimpleContract(msg.obj)
            print(msg.obj.contractID, '----', ct)
            # self.reqMktData(msg.obj.contractID, ct, "233", False, False, [])
            # self.reqTickByTickData(msg.obj.contractID, ct, "Last", 0, True)

            nextID = self.nextId
            # nextID=oneContract.contractID
            self.nextIDconID[nextID] = msg.obj.contractID


            if msg.obj.contractID in self.stop_reqTickByTickData:
                print(' Error watchStart - we are already subscribed to ',msg.obj.contractID)
                return
            else:
                self.realTickData[msg.obj.contractID]=[]
                self.stop_reqTickByTickData[msg.obj.contractID] = nextID
                self.reqTickByTickData(nextID, ct, "BidAsk", 0, True)
                #self.reqTickByTickData(nextID, ct, "Last", 0, True)


    def watchStop(self, msg):
            #ct = makeSimpleContract(msg.obj)
            # self.cancelMktData(msg.obj.contractID)

            self.cancelTickByTickData(self.stop_reqTickByTickData[msg.obj.contractID])
            self.stop_reqTickByTickData.pop(msg.obj.contractID)#we need to remove it
            #let's print before
            self.realTickData_writeToAFile(msg.obj.contractID,1)
            self.realTickData.pop(msg.obj.contractID)

    def realTickData_writeToAFile(self,conID,interval=1):
        #interval are in minute
        #for item in self.realTickData[conID]:
        #    print(item)
        #return

        res=[]
        res.append([self.realTickData[conID][0][0],self.realTickData[conID][0][1],self.realTickData[conID][0][2],
        self.realTickData[conID][0][1],self.realTickData[conID][0][2]])
        #date,open,high,low,close - close will be the last high low=open and close=high
        #i=0
        for item in self.realTickData[conID]:
            #print(item[0][12:14],res[-1][0][12:14])
            if item[0][12:14]==res[-1][0][12:14]:
                #we are in the same minute
                res[-1][2] = max(res[-1][2],item[2]) #high
                res[-1][3] = min(res[-1][3], item[1]) #low
                res[-1][4] = item[2] #close will be the last high
            else:
                print('close at',res[-1][0],' is ',res[-1][4])
                #add for a new minute
                item[0]=item[0][:15]+"XX"
                res.append([item[0],item[1],item[2],item[1],item[2]])#date,open,high,low,close


        file1 = open("tick"+str(conID)+".txt", "a")  # append mode
        for item in res:
            file1.write(item[0]+","+str(item[1])+","+str(item[2])+","+str(item[3])+","+str(item[3])+"\n")
        file1.write("\n")

        for item in self.realTickData[conID]:
            file1.write(item[0]+","+str(item[1])+","+str(item[2])+"\n")
        file1.close()

        #write to a file

    def watchStart5Sec(self, msg):
            ct = makeSimpleContract(msg.obj)
            wtsh=msg.obj.whattoshow
            if wtsh != 'TRADES' and wtsh !="MIDPOINT":
                wtsh='MIDPOINT'
            #regular time hour= FALSE

            nextID = self.nextId
            # nextID=oneContract.contractID
            self.nextIDconID[nextID] = msg.obj.contractID

            if msg.obj.contractID in self.stop_reqRealTimeBars:
                print('Error watchStart5Sec - we are already subscribed to ', msg.obj.contractID)
                return
            else:
                self.stop_reqRealTimeBars[msg.obj.contractID] = nextID
                self.reqRealTimeBars(nextID, ct, 5, wtsh, False, [])





    def Stop5SecWatch(self, msg):
            ct = makeSimpleContract(msg.obj)
            # self.cancelMktData(msg.obj.contractID)
            self.cancelRealTimeBars(self.stop_reqRealTimeBars[msg.obj.contractID])
            self.stop_reqRealTimeBars.pop(msg.obj.contractID)

    ##################end the caller################################







#####################this are the call back that is comming back from TWS########################################
    ####### should replace EWrapper with super()
    def nextValidId(self, orderId: int):
        """
        Callback
        orderId -- First unused order id provided by TWS
        Use reqIds() to request this info
        """
        EWrapper.nextValidId(self, orderId)
        #logging.debug(f'Setting next order Id: {orderId}')
        #self.tws2gui.put(f'Setting next order Id: {orderId}')

        self._lastId = orderId - 1
        self._onStart()

    def tickEFP(self, reqId:TickerId, tickType:TickType, basisPoints:float,
                formattedBasisPoints:str, totalDividends:float,
                holdDays:int, futureLastTradeDate:str, dividendImpact:float,
                dividendsToLastTradeDate:float):
        EWrapper.tickEFP(reqId, tickType,basisPoints,
                formattedBasisPoints, totalDividends,
                holdDays, futureLastTradeDate, dividendImpact,
                dividendsToLastTradeDate)
        print('tickEFP')


    def tickGeneric(self, reqId:TickerId, tickType:TickType, value:float):
        EWrapper.tickGeneric(reqId, tickType, value)
        print("tickGeneric",reqId,tickType,value)

    def tickPrice(self, reqId:TickerId , tickType:TickType, price:float, attrib:TickAttrib):
        EWrapper.tickPrice(self,reqId,tickType, price, attrib)
        print("tickGeneric", reqId, tickType, price,attrib)

    def tickSize(self, reqId:TickerId, tickType:TickType, size:int):
        EWrapper.tickSize(self,reqId,tickType,size)
        print("ticksize",reqId,tickType,size)

    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                                                     size: int, tickAtrribLast: TickAttribLast, exchange: str,
                                                     specialConditions: str):
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAtrribLast,exchange, specialConditions)
        print('tickByTickAllLast')
        if tickType == 1:
            print("tickByTickAllLast type =1.",reqId, price,'--2-',size,'--3--',datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),'--4--',exchange,'--5---',tickAtrribLast,specialConditions)
        else:
            print("tickByTickAllLast type NOT 1. ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "Price:",
                  price, "Size:", size, "Exch:", exchange, "Spec Cond:", specialConditions, "PastLimit:", tickAtrribLast.pastLimit, "Unreported:", tickAtrribLast.unreported)

    def tickByTickBidAsk(self, reqId: int, time: int, bidPrice: float, askPrice: float,
                         bidSize: int, askSize: int, tickAttribBidAsk: TickAttribBidAsk):
        #EWrapper.tickByTickBidAsk(reqId, time, bidPrice, askPrice,bidSize, askSize, tickAttribBidAsk)
        super().tickByTickBidAsk(reqId, time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk)
        #print("tickByTickBidAsk ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "askPrice:",
        #          askPrice, "askSize:", askSize, "bidPrice:", bidPrice, "bidSize:", bidSize,"tickAttribBidAsk:",tickAttribBidAsk )
        self.realTickData[self.nextIDconID[reqId]].append([datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),bidPrice,askPrice])

        return
        msg = toMessage('tickbytick')
        # msg.obj=onetick
        msg.obj = [self.nextIDconID[reqId],datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),askPrice,bidPrice ]
        self.toWat.put(msg)


    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        EWrapper.tickByTickMidPoint(reqId, time, midPoint)
        print('tickByTickMidPoint')



    def tickReqParams(self, tickerId:int, minTick:float, bboExchange:str, snapshotPermissions:int):
        EWrapper.tickReqParams(tickerId, minTick, bboExchange, snapshotPermissions)
        print("tickReqParams")


    def tickString(self, reqId:TickerId, tickType:TickType, value:str):
        EWrapper.tickString(self,reqId,tickType,value)
        print('tickString',reqId,tickType,value)

    def marketDataType(self, reqId:TickerId, marketDataType:int):
        EWrapper.marketDataType(reqId, marketDataType)

        print('market data type',marketDataType)


    def historicalData(self, reqId: int, bar: BarData):
        """ returns the requested historical data bars

        reqId    - the request's identifier
        date     - the bar's date and time (either as a yyyymmss hh:mm:ss
                   formatted string or as system time according to the request)
        open     - the bar's open point
        high     - the bar's high point
        low      - the bar's low point
        close    - the bar's closing point
        volume   - the bar's traded volume if available
        barCount - the number of trades during the bar's timespan (only available for TRADES).
        average  - the bar's Weighted Average Price
        hasGaps  - indicates if the data has gaps or not. """

        EWrapper.historicalData(self, reqId, bar)
        #print("historical data id ",reqId)
        #date, time = bar.date.split()
        self.downloadHistInfo[self.nextIDconID[reqId]].oneStock.addOneBar(bar)
        #temp=f'{bar.date},{bar.open},{bar.close},{bar.low},{bar.high},{bar.barCount},{bar.volume},{bar.average}'


    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """ Marks the ending of the historical bars reception. """
        #msg=toMessage('DownloadFinish')
        #self.toGui.put(msg)

        EWrapper.historicalDataEnd(self, reqId, start, end)

        #translate back
        #print("translate back",reqId,self.nextIDconID[reqId])
        conID=self.nextIDconID[reqId]
        #print('reqId after transalation ',conID)

        if self.downloadHistInfo[conID].whatToDownload=='histnew5secOneTime':
            msg = toMessage('5secHist')
            #we must send the reaId besides the list
            msg.obj =[conID,self.downloadHistInfo[conID]]
            self.toWat.put(msg) # we send to watch,

            print('histnew5secOneTime - finished',conID)

            #must clear the downloadHistInfo
            self.downloadHistInfo.pop(conID)
            ## maybe we should send some message to gui too to inform the user that we are ready

            return

        ret=self.dbLite.addOneStock(self.downloadHistInfo[conID])

        start = self.downloadHistInfo[conID].oneStock.bars1min[0].date

        del self.downloadHistInfo[conID].oneStock.bars1min[:]

        if ret=='stop': #we don't need to download anymore in case of a newhist

            if self.downloadHistInfo[conID].whatToDownload=='histnewLevel1':
                msg=toMessage('histnewLevel1End')
                msg.obj=conID
                self.toGui.put(msg) #let's anounce that we can go to level 2
                #print('hist new Level1 end')
            self.downloadHistInfo.pop(conID)  # removed from dictionary - no sens to stay there
            print('finish new download')
            return

        #delete all the bars
        self.downloadHistInfo[conID].count += 1

        if self.downloadHistInfo[conID].count>=10 and self.downloadHistInfo[conID].whatToDownload=='histold':
            #we already download 60 for history so do not send anymore messages

            self.downloadHistInfo.pop(conID)
            return

        self.downloadHistInfo[conID].dateToDownload = start
        msg=toMessage('HistFinish')
        msg.obj=self.downloadHistInfo[conID]
        self.toGui.put(msg)
        return


    def winError(self, text:str, lastError:int):
        EWrapper.winError(text, lastError)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'win error')



    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        """This event is called when there is an error with the
        communication or when TWS wants to send a message to the client."""
        EWrapper.error(self, reqId, errorCode, errorString)

        #self.tws2gui.put(f'ERROR {errorCode}: {errorString}')
        # Error messages with codes (2104, 2106, 2107, 2108) are not real errors but information messages
        if errorCode not in (2104, 2106, 2107, 2108,2158):
            msg=toMessage('ERROR')
            msg.obj=str(errorCode)+':'+str(errorString)
            #self.toGui.put(f'ERROR {errorCode}: {errorString}')
            self.toGui.put(msg)

    #5sec receiver
    def realtimeBar(self, reqId: TickerId, time:int, open_: float, high: float, low: float, close: float,
                             volume: int, wap: float, count: int):
             super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
             #print("TickerId:", reqId, "time:",datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "Open: ", open_, "Jigh: ",high,
             #      "Low: ", low, "Close: ", close, "volume: ",volume, "Wap:", wap,"Count: ", count)
             #onetick=OneTickWithInfo(reqId,OneTick(time, open_, high, low, close, volume, wap,count))

             #we need to put two spaces between date and time to be consistent with historical data format
             #onetick = OneTickWithInfo(reqId, OneTick(datetime.datetime.fromtimestamp(time).strftime("%Y%m%d  %H:%M:%S"), open_, high, low, close, volume, wap, count))

             # translate back
             #print("translate back", reqId, self.nextIDconID[reqId])
             conID = self.nextIDconID[reqId]
             #print('reqId after transalation ', conID)

             oneBar=BarData()
             oneBar.date=datetime.datetime.fromtimestamp(time).strftime("%Y%m%d  %H:%M:%S")
             oneBar.open=open_
             oneBar.high=high
             oneBar.low=low
             oneBar.close=close
             oneBar.volume=volume
             oneBar.average=wap
             oneBar.barCount=count
             msg=toMessage('5sec')
             #msg.obj=onetick
             msg.obj=[conID,oneBar]
             self.toWat.put(msg)
             #print('realtimeBar ',oneBar.close)

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        super().openOrder(orderId, contract, order, orderState)

        print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId, " OrderId:", orderId,
                "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
                "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
                "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
                "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status)
        print("permID:",order.permId)
        order.contract = contract
        #self.permId2ord[order.permId] = order

    def orderStatus(self, orderId: OrderId, status: str, filled: float,remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining,
        avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)


        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
                "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
                "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
                lastFillPrice, "ClientId:", clientId, "WhyHeld:",
                whyHeld, "MktCapPrice:", mktCapPrice)
################# end call back##############################





# endregion Callbacks

# region main
