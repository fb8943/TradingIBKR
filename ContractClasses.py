import sys
from inspect import getframeinfo, currentframe

from ibapi.contract import Contract
from ibapi.order import Order

from Source.OnesClasses import OneContract, OneStock
import tkinter as tk
from tkinter import ttk
import datetime as dt
from Source.UtilitiesClasses import toMessage, disLog


class UtilityContract:

    def __init__(self,gui):
        self.gui=gui
        self.contractsButtons()

        currency = tk.Label(gui.tab_contracts, text="Currency:", relief="flat")
        currency.place(x=10, y=50)
        self.eCurrency = tk.Entry(gui.tab_contracts, width=10)
        self.eCurrency.insert(0, 'USD')
        self.eCurrency.place(x=100, y=50)

        symbol = tk.Label(gui.tab_contracts, text="Symbol:", relief="flat")
        symbol.place(x=10, y=80)
        self.eSymbol = tk.Entry(gui.tab_contracts, width=10)
        self.eSymbol.place(x=100, y=80)

        expire = tk.Label(gui.tab_contracts, text="Expire:", relief="flat")
        expire.place(x=10, y=110)
        self.eExpire = tk.Entry(gui.tab_contracts, width=10)
        self.eExpire.place(x=100, y=110)

        exchange = tk.Label(gui.tab_contracts, text="Exchange:", relief="flat")
        exchange.place(x=10, y=140)
        self.exchange = tk.StringVar()
        self.cbExchange = ttk.Combobox(gui.tab_contracts, width=20, textvariable=self.exchange)
        self.cbExchange['values'] = ('Smart', 'GLOBEX', 'ECBOT', ' NYBOT', 'NYMEX', 'IDEALPRO')
        self.cbExchange.place(x=100, y=140)

        secType = tk.Label(gui.tab_contracts, text="Sec Type:", relief="flat")
        secType.place(x=10, y=170)
        self.secType = tk.StringVar()
        self.cbSecType = ttk.Combobox(gui.tab_contracts, width=20, textvariable=self.secType)
        self.cbSecType['values'] = ("STK", "OPT", "FUT", "IND", "FOP", "CASH", "BAG", "NEWS")
        self.cbSecType.place(x=100, y=170)

        barSize = tk.Label(gui.tab_contracts, text="Bar Size:", relief="flat")
        barSize.place(x=10, y=200)
        self.barSize = tk.StringVar()
        self.cbBarSize = ttk.Combobox(gui.tab_contracts, width=20, textvariable=self.barSize)
        self.cbBarSize['values'] = (
        "1 secs", "5 secs", "15 secs", "30 secs", "1 min", "2 mins", "3 mins", "5 mins", "15 mins", "30 mins", "1 hour",
        "1 day")
        self.cbBarSize.place(x=100, y=200)

        whatToShow = tk.Label(gui.tab_contracts, text="WhatToShow:", relief="flat")
        whatToShow.place(x=10, y=230)
        self.whatToShow = tk.StringVar()
        self.cbWhatToShow = ttk.Combobox(gui.tab_contracts, width=20, textvariable=self.whatToShow)
        self.cbWhatToShow['values'] = ("TRADES", "MIDPOINT", "BID", "ASK", "BID_ASK", "HISTORICAL_VOLATILITY", "OPTION_IMPLIED_VOLATILITY")
        self.cbWhatToShow.place(x=100, y=230)

        active = tk.Label(gui.tab_contracts, text="Active:", relief="flat")
        active.place(x=10, y=260)
        self.active = tk.StringVar()
        self.cbActive = ttk.Combobox(gui.tab_contracts, width=20, textvariable=self.active)
        self.cbActive['values'] = ("Yes", "No")
        self.cbActive.place(x=100, y=260)


        ordersize = tk.Label(gui.tab_contracts, text="OrderSize:", relief="flat")
        ordersize.place(x=10, y=290)
        self.eOrderSize = tk.Entry(gui.tab_contracts, width=10)
        self.eOrderSize.place(x=100, y=290)

        stopsize = tk.Label(gui.tab_contracts, text="StopSize:", relief="flat")
        stopsize.place(x=10, y=320)
        self.eStopSize = tk.Entry(gui.tab_contracts, width=10)
        self.eStopSize.place(x=100, y=320)

        orderextra = tk.Label(gui.tab_contracts, text="OrderExtra:", relief="flat")
        orderextra.place(x=10, y=350)
        self.eOrderExtra = tk.Entry(gui.tab_contracts, width=10)
        self.eOrderExtra.place(x=100, y=350)






        self.create_contracts_tree()

    def contractsButtons(self):
            paneBtnContracts = tk.PanedWindow(self.gui.tab_contracts, height="30", width="700")
            paneBtnContracts.place(x=10, y=10)

            self.bAddContract = tk.Button(paneBtnContracts, text="Add", command=self.addContract)
            self.bAddContract.pack(side='left')  # place(x=10, y=10)
            self.bUpdateContract = tk.Button(paneBtnContracts, text="Update", command=self.updateContract)
            self.bUpdateContract.pack(side='left')  # place(x=70, y=10)
            self.bDeleteContract = tk.Button(paneBtnContracts, text="Delete", command=self.deleteContract)
            self.bDeleteContract.pack(side='left')  # place(x=130, y=10)
            self.bHistNew = tk.Button(paneBtnContracts, text="HistNew", command=self.histnew)
            self.bHistNew.pack(side='left')  # place(x=190, y=10)
            self.bHistOld = tk.Button(paneBtnContracts, text="HistOld", command=self.histold)
            self.bHistOld.pack(side='left')  # place(x=250, y=10)
            self.bverifyData = tk.Button(paneBtnContracts, text="VerifyData", command=self.verifyData)
            self.bverifyData.pack(side='left')  # place(x=250, y=10)
            self.bMarketData = tk.Button(paneBtnContracts, text="MarketData", command=self.marketdata)
            self.bMarketData.pack(side='left')  # place(x=250, y=10)
            self.bCancelMktDt = tk.Button(paneBtnContracts, text="CanlMktDt", command=self.cancelmarketdata)
            self.bCancelMktDt.pack(side='left')  # place(x=250, y=10)
            self.bDispTest = tk.Button(paneBtnContracts, text="Disp-Test", command=self.DispTest)
            self.bDispTest.pack(side='left')  # place(x=270, y=50)
            self.bstartWatch = tk.Button(paneBtnContracts, text="StartWatch", command=self.startWatch)
            self.bstartWatch.pack(side='left')
            self.bstopWatch = tk.Button(paneBtnContracts, text="StopWatch", command=self.stopWatch)
            self.bstopWatch.pack(side='left')

            self.bstartWatch5Sec = tk.Button(paneBtnContracts, text="StartWatch5Sec", command=self.startWatch5Sec)
            self.bstartWatch5Sec.pack(side='left')
            self.bstopWatch5Sec = tk.Button(paneBtnContracts, text="Place order", command=self.placeOrder)
            self.bstopWatch5Sec.pack(side='left')

    def cancelmarketdata(self):
        #toTWS = self.gui.toTws('cancelmarketdata')
        toTWS = toMessage('cancelmarketdata')
        self.gui.toMessage.put(toTWS)

    def verifyData(self):
        item = self.treeContracts.selection()
        if not item:
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   "nothing selected")
        else:
            conID = self.treeContracts.item(item)['values'][0]
            symbol='T'+str(conID)
            oneStock:OneStock = self.gui.dbLite.getOneStock2(symbol)
            format2 = '%Y%m%d  %H:%M:%S'
            i=0
            for item in oneStock.bars[:-1]:
                format1 = '%Y%m%d %H:%M:%S'

                d0 = dt.datetime.strptime(item.date, format2)
                d1 = dt.datetime.strptime(oneStock.bars[i+1].date, format2)
                delta = (d1 - d0).total_seconds()
                if delta>60:
                    disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                           item.date,oneStock.bars[i+1].date)
                i=i+1


    def marketdata(self):
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            id=self.treeContracts.item(item)['values'][0]
            ct = OneContract(self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                             self.cbSecType.get(), self.cbBarSize.get(),
                             self.cbWhatToShow.get(), self.cbActive.get(), id)
            #mrkdt=toTWSMarketData(ct)
            #toTWS = self.gui.toTws('marketdata',id)
            toTWS = toMessage('marketdata', id)
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)


    def histnew(self):

        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            conID = self.treeContracts.item(item)['values'][0]
            ct = OneContract(self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                             self.cbSecType.get(), self.cbBarSize.get(),self.cbWhatToShow.get(), self.cbActive.get(),
                             self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get(), conID)
            #toTWS = self.gui.toTws('histnew', ct)
            toTWS = toMessage('histnew', ct)
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)
            #self.gui.getoTws()


    def histold(self):
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            conID = self.treeContracts.item(item)['values'][0]
            ct = OneContract(self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                             self.cbSecType.get(), self.cbBarSize.get(),self.cbWhatToShow.get(), self.cbActive.get(),
                             self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get(),conID)
            #toTWS = self.gui.toTws('histold', ct)
            toTWS = toMessage('histold', ct)
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)

    def disableBtn(self):
        self.bHistNew['state']='disable'
        self.bHistOld['state']='disable'

    def enableBtn(self):
        self.bHistNew['state']='normal'
        self.bHistOld['state']='normal'

    def DispTest(self):

        # d=self.dbLite.getOneStock('T11')
        # convertToHigher(d,'5min')
        # convertToSameVolume(d[0:3],1500)
        d = self.gui.dbLite.getOneStock2('11')
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
               d.bars[1])
        pass
        # self.dbLite.getContract()

    def startWatch(self):
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            conID = self.treeContracts.item(item)['values'][0]
            ct = OneContract(self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                             self.cbSecType.get(), self.cbBarSize.get(), self.cbWhatToShow.get(), self.cbActive.get(),
                             self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get(),conID)
            #toTWS = self.gui.toTws('watchStart', ct)
            toTWS = toMessage('watchStart', ct)
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)

    def stopWatch(self):
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            conID = self.treeContracts.item(item)['values'][0]
            ct = OneContract(self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                             self.cbSecType.get(), self.cbBarSize.get(), self.cbWhatToShow.get(), self.cbActive.get(),
                             self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get(),conID)
            #toTWS = self.gui.toTws('stopStart', ct)
            toTWS = toMessage('watchStop', ct)
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)

    def startWatch5Sec(self):
        print("this is disable")
        return
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            conID = self.treeContracts.item(item)['values'][0]

            #print("here  ",self.cbWhatToShow.get())
            ct = OneContract(self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                             self.cbSecType.get(), self.cbBarSize.get(),self.cbWhatToShow.get(), self.cbActive.get(),
                             self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get(),conID)
            #toTWS = self.gui.toTws('watchStart', ct)
            toTWS = toMessage('Start5SecWatch', ct)
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)

    def placeOrder(self):
        print("this place order")
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            val = (item[0], self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                   self.cbSecType.get(), self.cbBarSize.get(), self.cbWhatToShow.get(), self.cbActive.get(),
                   self.eOrderSize.get(), self.eStopSize.get(), self.eOrderExtra.get())
            print(val)
            contract = Contract()
            contract.symbol = self.eSymbol.get()
            contract.secType = self.cbSecType.get()
            contract.currency = self.eCurrency.get()
            contract.exchange = self.cbExchange.get()
            contract.lastTradeDateOrContractMonth=self.eExpire.get()
            print(contract.symbol,contract.secType,contract.currency,contract.exchange,contract.lastTradeDateOrContractMonth)

            order = Order()
            order.action = "BUY"
            #order.orderType = "LMT"
            order.orderType = "MKT"
            order.totalQuantity = 1
            #order.lmtPrice = 100
            #order.account="U146642"

            print(int(item[0]))

            toTWS = toMessage('PlaceOrder', [int(item[0]),contract,order])
            # print(self.dbLite.getDateTimeToDownload())
            self.gui.toTws.put(toTWS)

        return



    def addContract(self):

        oc=OneContract(self.eCurrency.get(),self.eSymbol.get(),self.eExpire.get(),self.cbExchange.get(),self.cbSecType.get(),
                       self.cbBarSize.get(),self.cbWhatToShow.get(),self.active.get(),
                       self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get())
        lastrow=self.gui.dbLite.addContract(oc)
        val = (lastrow, self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(), self.cbSecType.get(),
               self.cbBarSize.get(), self.cbWhatToShow.get(), self.active.get()
               ,self.eOrderSize.get(),self.eStopSize.get(),self.eOrderExtra.get())
        self.treeContracts.insert("", "end", lastrow, text="", values=val)

    def create_contracts_tree(self):
            self.paneTreeContracts = tk.PanedWindow(self.gui.tab_contracts, height="300", width="700")
            self.paneTreeContracts.place(x=10, y=380)

            self.treeContracts = ttk.Treeview(self.paneTreeContracts, height="7")
            self.treeContracts.bind("<ButtonRelease-1>", self.treeContractsClick)
            self.treeContracts.pack(side='left')
            verscrlbar = ttk.Scrollbar(self.paneTreeContracts,
                                       orient="vertical",
                                       command=self.treeContracts.yview)
            # Calling pack method w.r.to verical
            # scrollbar
            verscrlbar.pack(side='right', fill='y')
            # Configuring treeview
            self.treeContracts.configure(xscrollcommand=verscrlbar.set)
            # Defining number of columns
            self.treeContracts["columns"] = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11")
            # Defining heading
            self.treeContracts['show'] = 'headings'
            # Assigning the width and anchor to  the
            # respective columns
            self.treeContracts.column("0", width=20, anchor='c')
            self.treeContracts.column("1", width=30, anchor='se')
            self.treeContracts.column("2", width=60, anchor='se')
            self.treeContracts.column("3", width=60, anchor='se')
            self.treeContracts.column("4", width=60, anchor='se')
            self.treeContracts.column("5", width=50, anchor='se')
            self.treeContracts.column("6", width=60, anchor='se')
            self.treeContracts.column("7", width=90, anchor='se')
            self.treeContracts.column("8", width=50, anchor='se')
            self.treeContracts.column("9", width=60, anchor='se')
            self.treeContracts.column("10", width=60, anchor='se')
            self.treeContracts.column("11", width=60, anchor='se')
            # Assigning the heading names to the
            # respective columns
            # currency, exchange, expire, primaryExch, secType, barSize, whatToShow
            self.treeContracts.heading("0", text="ID")
            self.treeContracts.heading("1", text="Currency")
            self.treeContracts.heading("2", text="Symbol")
            self.treeContracts.heading("3", text="Expire")
            self.treeContracts.heading("4", text="Exchange")
            self.treeContracts.heading("5", text="SecType")
            self.treeContracts.heading("6", text="BarSize")
            self.treeContracts.heading("7", text="WhatToShow")
            self.treeContracts.heading("8", text="Active")
            self.treeContracts.heading("9", text="OrderSize")
            self.treeContracts.heading("10", text="StopSize")
            self.treeContracts.heading("11", text="OrderExtra")

    def treeContractsClick(self, event):
            item = self.treeContracts.selection()

            val = self.treeContracts.item(item)['values']
            i = 1
            for item in (self.eCurrency, self.eSymbol, self.eExpire, self.cbExchange, self.cbSecType,
                         self.cbBarSize, self.cbWhatToShow, self.cbActive,
                         self.eOrderSize, self.eStopSize,self.eOrderExtra):
                item.delete(0, "end")
                item.insert(0, val[i])
                i = i + 1

    def deleteContract(self):
        it = self.treeContracts.selection()
        if not it:
            print("nothing selected")
        else:
            self.treeContracts.delete(it)
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   it[0])
            self.gui.dbLite.deleteContract(it[0])
            for item in (self.eCurrency, self.eSymbol, self.eExpire, self.cbExchange, self.cbSecType, self.cbBarSize,
                         self.cbWhatToShow, self.cbActive,self.eOrderSize, self.eStopSize,self.eOrderExtra):
                item.delete(0, "end")

    def updateContract(self):
        item = self.treeContracts.selection()
        if not item:
            print("nothing selected")
        else:
            val = (item[0], self.eCurrency.get(), self.eSymbol.get(), self.eExpire.get(), self.cbExchange.get(),
                   self.cbSecType.get(), self.cbBarSize.get(), self.cbWhatToShow.get(), self.cbActive.get(),
                   self.eOrderSize.get(), self.eStopSize.get(),self.eOrderExtra.get())
            self.treeContracts.item(item, values=val)
            # self.treeContracts.delete(item)
            # self.treeContracts.insert("", 0, val[0], text="", values=val)
            self.gui.dbLite.Update(val)
