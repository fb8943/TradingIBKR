#region import
import datetime
import queue
import logging
import sys
import time
from inspect import getframeinfo, currentframe

from ibapi.wrapper import EWrapper, TickType, TickAttribLast, TickAttribBidAsk
from ibapi.contract import Contract
from ibapi.common import BarData, TickerId,TickAttrib

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
        self.downloadHistInfo={}

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
            elif msg.purpose=='stopStart':
                self.watchStop(msg)

            elif msg.purpose=='Start5SecWatch':
                self.watchStart5Sec(msg)
            elif msg.purpose=='Stop5SecWatch':
                self.Stop5SecWatch(msg)

            elif msg.purpose=='cancelmarketdata':
                self.cancelMktData(self.idmarketdata)

            elif msg.purpose=='connect':
                self.connect('127.0.0.1', 7496, 1)

            elif msg.purpose=='disconnect':
                self.disconnect()


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

        nextID=oneContract.contractID
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               ' here is hist new nextID ', nextID)

        if oneContract.sectype=='FUT':
            self.downloadHistInfo[nextID].newestForNewHist=downloadHist.getStartFutureDate(oneContract.symbol,oneContract.expire)

        if self.downloadHistInfo[nextID].dateToDownload=='':
            self.downloadHistInfo[nextID].dateToDownload=self.dbLite.getMinDateTime(oneContract.contractID)

        if self.downloadHistInfo[nextID].oneContract=='':
            self.downloadHistInfo[nextID].oneContract=oneContract

        if self.downloadHistInfo[nextID].count==0:
            #self.downloadHistInfo[nextID].nextID=nextID
            self.downloadHistInfo[nextID].conID=oneContract.contractID
        if oneContract.barsize=='5 secs':
            rth=1
        else:
            rth=0
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               oneContract.barsize,' rth is :',rth)

        self.reqHistoricalData(nextID, ct, self.downloadHistInfo[nextID].dateToDownload, getStepSize(oneContract.barsize),
                               oneContract.barsize, oneContract.whattoshow, rth, 1, False, [])
        '''self.reqHistoricalData(self.nextId,
                                               makeSimpleContract(),
                                               datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"),  # endDateTime,
                                               "1 M",
                                               "1 day",
                                               "TRADES",
                                               1,
                                               1,
                                               False,
                                               []
                                               )'''
        # TODO Add message processing here

    #this assume we don't have anything in the database
    def getHistNew(self, oneContract:OneContract):
        #DownloadLimit.limit() #to stop the download

        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'start new hist for:',oneContract.symbol)
        ct = makeSimpleContract(oneContract)

        #nextID=self.nextId
        nextID=oneContract.contractID
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               ' here is nextID ', nextID)

        #if we are first time take now moment
        #if (self.downloadHistInfo.dateToDownload == '') and (self.downloadHistInfo.newestForNewHist==''):
        if (self.downloadHistInfo[nextID].dateToDownload == '') and (self.downloadHistInfo[nextID].newestForNewHist == ''):
            self.downloadHistInfo[nextID].newestForNewHist=self.dbLite.getMaxDateTime(oneContract.contractID)

            if self.downloadHistInfo[nextID].newestForNewHist=='': #we should run history
                disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                       'You need to use history old')
                return
            #self.downloadHistInfo.dateToDownload=datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
            self.downloadHistInfo[nextID].dateToDownload = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")


        if self.downloadHistInfo[nextID].oneContract=='':
            self.downloadHistInfo[nextID].oneContract=oneContract
            #self.downloadHistInfo[nextID].whatToDownload = 'histnew'



        if self.downloadHistInfo[nextID].count==0:
            #self.downloadHistInfo[nextID].nextID=nextID
            self.downloadHistInfo[nextID].conID=oneContract.contractID

        if (self.downloadHistInfo[nextID].lastDateDownload==''):
            self.downloadHistInfo[nextID].lastDateDownload = self.dbLite.getMaxDateTime(oneContract.contractID)

        #print(self.downloadHistInfo.lastDateDownload)
        stepSize=getStepSize(oneContract.barsize,self.downloadHistInfo[nextID].dateToDownload,self.downloadHistInfo[nextID].lastDateDownload)
        #print(stepSize)

        if oneContract.barsize == '5 secs':
            rth = 1
        else:
            rth = 0

        #in case we 5SecOneTime we need to go outside market hour and bar size must be 5 sec
        if self.downloadHistInfo[nextID].whatToDownload=='histnew5secOneTime':
            oneContract.barsize = '5 secs'
            rth=0
            stepSize = getStepSize(oneContract.barsize, self.downloadHistInfo[nextID].dateToDownload,
                                   self.downloadHistInfo[nextID].lastDateDownload)


        self.reqHistoricalData(nextID, ct, self.downloadHistInfo[nextID].dateToDownload, stepSize,
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
            self.reqTickByTickData(msg.obj.contractID, ct, "BidAsk", 0, True)
            pass

    def watchStop(self, msg):
            ct = makeSimpleContract(msg.obj)
            # self.cancelMktData(msg.obj.contractID)
            self.cancelTickByTickData(msg.obj.contractID)

    def watchStart5Sec(self, msg):
            ct = makeSimpleContract(msg.obj)
            wtsh=msg.obj.whattoshow
            if wtsh != 'TRADES' and wtsh !="MIDPOINT":
                wtsh='MIDPOINT'
            #self.reqRealTimeBars(3001, ContractSamples.EurGbpFx(), 5, "MIDPOINT", True, [])
            #self.reqRealTimeBars(msg.obj.contractID, ct, 5, wtsh, True, [])
            #regular time hour= FALSE
            self.reqRealTimeBars(msg.obj.contractID, ct, 5, wtsh, False, [])

            #self.reqRealTimeBars(msg.obj.contractID, ct, 5, "MIDPOINT", True, [])
            #self.reqRealTimeBars(msg.obj.contractID, ct, 5, "TRADES", True, [])
            pass

    def Stop5SecWatch(self, msg):
            ct = makeSimpleContract(msg.obj)
            # self.cancelMktData(msg.obj.contractID)
            self.cancelRealTimeBars(msg.obj.contractID)
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
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tick Generic')

    def tickPrice(self, reqId:TickerId , tickType:TickType, price:float, attrib:TickAttrib):
        EWrapper.tickPrice(self,reqId,tickType, price, attrib)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tickPrice ',reqId,tickType,price,attrib)

    def tickSize(self, reqId:TickerId, tickType:TickType, size:int):
        EWrapper.tickSize(self,reqId,tickType,size)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tickSize ',reqId,tickType,size)

    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                                                     size: int, tickAtrribLast: TickAttribLast, exchange: str,
                                                     specialConditions: str):
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAtrribLast,exchange, specialConditions)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tickByTickAllLast')
        if tickType == 1:
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   "Last.", price,'--2-',size,'--3--',datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),'--4--',exchange,'--5---',tickAtrribLast,specialConditions)
        else:
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   "AllLast.", end='')
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   " ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "Price:",
                  price, "Size:", size, "Exch:", exchange, "Spec Cond:", specialConditions, "PastLimit:", tickAtrribLast.pastLimit, "Unreported:", tickAtrribLast.unreported)

    def tickByTickBidAsk(self, reqId: int, time: int, bidPrice: float, askPrice: float,
                         bidSize: int, askSize: int, tickAttribBidAsk: TickAttribBidAsk):
        #EWrapper.tickByTickBidAsk(reqId, time, bidPrice, askPrice,bidSize, askSize, tickAttribBidAsk)
        super().tickByTickBidAsk(reqId, time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               " ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "askPrice:",
                  askPrice, "askSize:", askSize, "bidPrice:", bidPrice, "bidSize:", bidSize,"tickAttribBidAsk:",tickAttribBidAsk )

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        EWrapper.tickByTickMidPoint(reqId, time, midPoint)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tickbyTickMidPoint')



    def tickReqParams(self, tickerId:int, minTick:float, bboExchange:str, snapshotPermissions:int):
        EWrapper.tickReqParams(tickerId, minTick, bboExchange, snapshotPermissions)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tickReqParams')


    def tickString(self, reqId:TickerId, tickType:TickType, value:str):
        EWrapper.tickString(self,reqId,tickType,value)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'tickString',reqId,tickType,value)

    def marketDataType(self, reqId:TickerId, marketDataType:int):
        EWrapper.marketDataType(reqId, marketDataType)

        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'market data type',marketDataType)


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
        self.downloadHistInfo[reqId].oneStock.addOneBar(bar)
        #temp=f'{bar.date},{bar.open},{bar.close},{bar.low},{bar.high},{bar.barCount},{bar.volume},{bar.average}'


    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """ Marks the ending of the historical bars reception. """
        #msg=toMessage('DownloadFinish')
        #self.toGui.put(msg)

        EWrapper.historicalDataEnd(self, reqId, start, end)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               'historicalDataEnd')
        #print('start first',start)
        #print('end ',end)

        if self.downloadHistInfo[reqId].whatToDownload=='histnew5secOneTime':
            msg = toMessage('5secHist')
            #we must send the reaId besides the list
            msg.obj =[reqId,self.downloadHistInfo[reqId]]
            self.toWat.put(msg) # we send to watch,

            print('histnew5secOneTime',reqId)
            #f = open(str(reqId) + "-5sec-what-i-download.txt", "a")

            # for item in self.downloadHistInfo[reqId].oneStock.bars1min:
            #     f.write(
            #         item.date + ' ' + str(item.open) + ' ' + str(item.high) + ' ' + str(item.low) + ' ' + str(
            #             item.close) + ' ' + str(item.volume) + '\r\n')
            # f.close()

            #must clear the downloadHistInfo
            self.downloadHistInfo.pop(reqId)
            ## maybe we should send some message to gui too to inform the user that we are ready

            cnt = len(self.downloadHistInfo)
            print("histnew5secOneTime", cnt)
            return

        ret=self.dbLite.addOneStock(self.downloadHistInfo[reqId])

        start = self.downloadHistInfo[reqId].oneStock.bars1min[0].date

        del self.downloadHistInfo[reqId].oneStock.bars1min[:]

        if ret=='stop': #we don't need to download anymore in case of a newhist

            if self.downloadHistInfo[reqId].whatToDownload=='histnewLevel1':
                msg=toMessage('histnewLevel1End')
                msg.obj=reqId
                self.toGui.put(msg) #let's anounce that we can go to level 2
                print('hist new Level1 end')
            self.downloadHistInfo.pop(reqId)  # removed from dictionary - no sens to stay there
            return

        #delete all the bars
        self.downloadHistInfo[reqId].count += 1

        if self.downloadHistInfo[reqId].count>=60 and self.downloadHistInfo[reqId].whatToDownload=='histold':
            #we already download 60 for history so do not send anymore messages


            #msg = toMessage('HistFinish')
            #msg.obj = self.downloadHistInfo[reqId]
            #self.toGui.put(msg)

            self.downloadHistInfo.pop(reqId)
            return

        self.downloadHistInfo[reqId].dateToDownload = start
        msg=toMessage('HistFinish')
        msg.obj=self.downloadHistInfo[reqId]
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
             msg.obj=[reqId,oneBar]
             self.toWat.put(msg)
################# end call back##############################





# endregion Callbacks

# region main
