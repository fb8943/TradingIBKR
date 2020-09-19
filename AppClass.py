#region import
import datetime
import queue
import logging

from ibapi.wrapper import EWrapper, TickType, TickAttribLast, TickAttribBidAsk
from ibapi.contract import Contract
from ibapi.common import BarData, TickerId,TickAttrib

#from config import config
#from logutils import init_logger
from Source.ClientClass import TestClient
#endregion import
from Source.OnesClasses import OneContract
from Source.UtilitiesClasses import toTws, downloadHist,getStepSize
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


    def __init__(self, gui2tws, tws2gui,tws2pre,pre2tws):
        EWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.idmarketdata=0#temporary

        self.gui2tws = gui2tws
        self.tws2gui = tws2gui
        self.tws2pre = tws2pre
        self.pre2tws = pre2tws

        self.nKeybInt = 0
        self.started = False
        self._lastId = None
        self._file = None
        #self.stepSize={'1 sec':'1800 S','5 sec':'3600 S','10 secs':'14400 S','30 secs':'28800 S','1 min':'2 D','30 mins':'1 M','1 day':'1 Y'}

        #self.oneStock=OneStock(None)

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
            print(msg)
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
        self.tws2gui.put("exit")
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
        print('Main logic started')

    def onStop(self):
        if self._file: self._file.close()
        #logging.info('Main logic stopped')
        print('Main logic stopped')

    # this will take the messages from pre
    def onLoopIteration2(self):
        try:
            msg:toTws = self.pre2tws.get_nowait()
        except queue.Empty:
            #print('onLoopIteration2 - pre2tws is empty')
            pass

    #this will take the messages from gui
    def onLoopIteration(self): # this is called from ClientClass
        #logging.debug('onLoopIteration()')
        #print('onLoopIteration()1111')
        try:
            msg:toTws = self.gui2tws.get_nowait()
            #logging.info(f'GUI MESSAGE: {msg}')


            print('msg.purpose ',msg.purpose)
            if msg.purpose=='histold':
                print('i am inside ')
                self.downloadHistInfo=downloadHist()# need to be outside because we don't want to call many times
                self.downloadHistInfo.whatToDownload = 'histold'
                self.getHistOld(msg.obj)
            elif msg.purpose=='histnew':
                self.downloadHistInfo = downloadHist()
                self.downloadHistInfo.whatToDownload = 'histnew'
                self.getHistNew(msg.obj)
            elif msg.purpose == 'histgap':
                #not implemented yet it may happen if a stock was download for a long period of time.
                pass
            elif msg.purpose=='marketdata':
                self.getMarketData(msg)
                
            elif msg.purpose=='watchStart':
                self.watchStart(msg)
            elif msg.purpose=='stopStart':
                self.watchStop(msg)

            elif msg.purpose=='watchStart5Sec':
                self.watchStart5Sec(msg)
            elif msg.purpose=='stopStart5Sec':
                self.watchStop5Sec(msg)

            elif msg.purpose=='cancelmarketdata':
                self.cancelMktData(self.idmarketdata)

            elif msg.purpose=='connect':
                self.connect('127.0.0.1', 7496, 1)
                self.tws2gui.put('i am connect now')
            elif msg.purpose=='disconnect':
                self.disconnect()
                self.tws2gui.put('i am disconet now')

            elif msg.purpose == 'exit':
                self.exit()
            elif msg.purpose == 'database':
                print(msg.obj)
                self.dbLite=DB(msg.obj)
                if self.dbLite.conn != '':
                    print('i am connected to database')
            else:
                #logging.error(f'Unknown GUI message: {msg}')
                print("Unknown GUI messageXXXX")
        except queue.Empty:
            pass

        self.count = 0

    def getMarketData(self, msg):
        toMarket = msg.obj
        ct = makeSimpleContract(toMarket.contract)
        self.idmarketdata = self.nextId
        self.reqMktData(self.idmarketdata, ct, toMarket.genericTickList, False, False, None)

    def getHistOld(self, oneContract:OneContract):

        #downloadHist.getStartFutureDate(oneContract.symbol,oneContract.expire)
        #return

        ct = makeSimpleContract(oneContract)

        if oneContract.sectype=='FUT':
            self.downloadHistInfo.newestForNewHist=downloadHist.getStartFutureDate(oneContract.symbol,oneContract.expire)

        if self.downloadHistInfo.dateToDownload=='':
            self.downloadHistInfo.dateToDownload=self.dbLite.getMinDateTime(oneContract.contractID)

        if self.downloadHistInfo.oneContract=='':
            self.downloadHistInfo.oneContract=oneContract


        nextID=self.nextId
        print('nextID ',nextID)

        if self.downloadHistInfo.count==0:
            self.downloadHistInfo.nextID=nextID
            self.downloadHistInfo.conID=oneContract.contractID
        if oneContract.barsize=='5 secs':
            rth=1
        else:
            rth=0
        print(oneContract.barsize,' rth is :',rth)

        self.reqHistoricalData(nextID, ct, self.downloadHistInfo.dateToDownload, getStepSize(oneContract.barsize),
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
        ct = makeSimpleContract(oneContract)

        #if we are first time take now moment
        if (self.downloadHistInfo.dateToDownload == '') and (self.downloadHistInfo.newestForNewHist==''):
            self.downloadHistInfo.newestForNewHist=self.dbLite.getMaxDateTime(oneContract.contractID)

            if self.downloadHistInfo.newestForNewHist=='': #we should run history
                print('You need to use history old')
                return
            #self.downloadHistInfo.dateToDownload=datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
            self.downloadHistInfo.dateToDownload = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")


        if self.downloadHistInfo.oneContract=='':
            self.downloadHistInfo.oneContract=oneContract
            self.downloadHistInfo.whatToDownload = 'histnew'

        nextID=self.nextId

        if self.downloadHistInfo.count==0:
            self.downloadHistInfo.nextID=nextID
            self.downloadHistInfo.conID=oneContract.contractID

        if (self.downloadHistInfo.lastDateDownload==''):
            self.downloadHistInfo.lastDateDownload = self.dbLite.getMaxDateTime(oneContract.contractID)

        #print(self.downloadHistInfo.lastDateDownload)
        stepSize=getStepSize(oneContract.barsize,self.downloadHistInfo.dateToDownload,self.downloadHistInfo.lastDateDownload)
        #print(stepSize)

        if oneContract.barsize == '5 secs':
            rth = 1
        else:
            rth = 0
        print(oneContract.barsize,' -rth is :', rth)

        print('dateToDownload ',self.downloadHistInfo.dateToDownload,' count= ',self.downloadHistInfo.count)
        self.reqHistoricalData(nextID, ct, self.downloadHistInfo.dateToDownload, stepSize,
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
            print(ct)
            # self.cancelMktData(msg.obj.contractID)
            self.cancelTickByTickData(msg.obj.contractID)

    def watchStart5Sec(self, msg):
            ct = makeSimpleContract(msg.obj)
            print(msg.obj.contractID, '----', ct)
            print(msg.obj.whattoshow, 'whattoshow')
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

    def watchStop5Sec(self, msg):
            ct = makeSimpleContract(msg.obj)
            print(ct)
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
        print('tick Generic')

    def tickPrice(self, reqId:TickerId , tickType:TickType, price:float, attrib:TickAttrib):
        EWrapper.tickPrice(self,reqId,tickType, price, attrib)
        print('tickPrice ',reqId,tickType,price,attrib)

    def tickSize(self, reqId:TickerId, tickType:TickType, size:int):
        EWrapper.tickSize(self,reqId,tickType,size)
        print('tickSize ',reqId,tickType,size)

    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                                                     size: int, tickAtrribLast: TickAttribLast, exchange: str,
                                                     specialConditions: str):
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAtrribLast,exchange, specialConditions)
        print('tickByTickAllLast')
        if tickType == 1:
            print("Last.", price,'--2-',size,'--3--',datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),'--4--',exchange,'--5---',tickAtrribLast,specialConditions)
        else:
            print("AllLast.", end='')
            print(" ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "Price:",
                  price, "Size:", size, "Exch:", exchange, "Spec Cond:", specialConditions, "PastLimit:", tickAtrribLast.pastLimit, "Unreported:", tickAtrribLast.unreported)

    def tickByTickBidAsk(self, reqId: int, time: int, bidPrice: float, askPrice: float,
                         bidSize: int, askSize: int, tickAttribBidAsk: TickAttribBidAsk):
        #EWrapper.tickByTickBidAsk(reqId, time, bidPrice, askPrice,bidSize, askSize, tickAttribBidAsk)
        super().tickByTickBidAsk(reqId, time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk)
        print(" ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "askPrice:",
                  askPrice, "askSize:", askSize, "bidPrice:", bidPrice, "bidSize:", bidSize,"tickAttribBidAsk:",tickAttribBidAsk )

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        EWrapper.tickByTickMidPoint(reqId, time, midPoint)
        print('tickbyTickMidPoint')



    def tickReqParams(self, tickerId:int, minTick:float, bboExchange:str, snapshotPermissions:int):
        EWrapper.tickReqParams(tickerId, minTick, bboExchange, snapshotPermissions)
        print('tickReqParams')


    def tickString(self, reqId:TickerId, tickType:TickType, value:str):
        EWrapper.tickString(self,reqId,tickType,value)
        print('tickString',reqId,tickType,value)

    def marketDataType(self, reqId:TickerId, marketDataType:int):
        EWrapper.marketDataType(reqId, marketDataType)

        print('market data type')


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

        #date, time = bar.date.split()
        self.downloadHistInfo.oneStock.addOneBar(bar)
        #temp=f'{bar.date},{bar.open},{bar.close},{bar.low},{bar.high},{bar.barCount},{bar.volume},{bar.average}'


    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """ Marks the ending of the historical bars reception. """
        EWrapper.historicalDataEnd(self, reqId, start, end)
        print ('historicalDataEnd')
        print('start first',start)
        print('end ',end)

        ret=self.dbLite.addOneStock(self.downloadHistInfo)
        if ret=='stop': #we don't need to download anymore in case of a newhist
            print(' i stop downloading becouse of downloadHistInfor')
            return

        #delete all the bars

        start=self.downloadHistInfo.oneStock.bars[0].date
        print('start = ',start)
        del self.downloadHistInfo.oneStock.bars[:]

        print('count is=',self.downloadHistInfo.count,' ',self.downloadHistInfo.whatToDownload)

        if self.downloadHistInfo.count<60:#downloadHist.maxDownload:
             self.downloadHistInfo.count+=1
             self.downloadHistInfo.dateToDownload=start #- after hour is bogus
             if self.downloadHistInfo.whatToDownload=='histold':
                self.getHistOld(self.downloadHistInfo.oneContract)
             elif self.downloadHistInfo.whatToDownload=='histnew':
                 self.getHistNew(self.downloadHistInfo.oneContract)
        else:
            print(' i finish downloading the 30/60 ')
        #self.tws2gui.put('END')


    def winError(self, text:str, lastError:int):
        EWrapper.winError(text, lastError)
        print('win error')



    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        """This event is called when there is an error with the
        communication or when TWS wants to send a message to the client."""
        EWrapper.error(self, reqId, errorCode, errorString)

        #self.tws2gui.put(f'ERROR {errorCode}: {errorString}')
        # Error messages with codes (2104, 2106, 2107, 2108) are not real errors but information messages
        if errorCode not in (2104, 2106, 2107, 2108,2158):
            self.tws2gui.put(f'ERROR {errorCode}: {errorString}')


    def realtimeBar(self, reqId: TickerId, time:int, open_: float, high: float, low: float, close: float,
                             volume: int, wap: float, count: int):
             super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
             print("TickerId:", reqId, "time:",datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"), "Open: ", open_, "Jigh: ",high,
                   "Low: ", low, "Close: ", close, "volume: ",volume, "Wap:", wap,"Count: ", count)
################# end call back##############################





# endregion Callbacks

# region main
