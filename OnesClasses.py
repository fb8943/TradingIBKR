# this will have OneTick,OneStock and OneContract
import copy
import queue
import threading
import time
import pandas as pd
from datetime import datetime
import tkinter as tk
from ibapi.common import BarData
import tkinter.font as font


#from Source.UtilitiesClasses import toMessage
class toMessage2:
    def __init__(self,purp,obj=None):
        self.purpose=purp
        self.obj=obj

class OneContract:
    def __init__(self, currency, symbol, expire, exchange, sectype, barsize, whattoshow, active, conID=0):
        self.currency = currency
        self.symbol = symbol
        self.expire = expire
        self.exchange = exchange
        self.sectype = sectype
        self.barsize = barsize
        self.whattoshow = whattoshow
        self.active = active
        self.contractID = conID  # this value will change once enter in DB

    def getValues(self):
        return "'" + self.currency + "','" + self.symbol + "','" + self.expire + "','" + self.exchange + "','" + self.sectype + "','" + self.barsize + "','" + self.whattoshow + "','" + self.active + "'"

#this class is equivalent of BarData class from common.py
class OneTick:
    def __init__(self, date,open_, high, low, close, volume,wap, count):
        self.date=date
        self.open_ = open_
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.wap=wap
        self.count=count

    def disp(self):
        print(datetime.fromtimestamp(self.date).strftime("%Y%m%d %H:%M:%S"),self.open_,self.high,self.low,self.close,self.volume,self.wap,self.count)

class OneTickWithInfo:
    def __init__(self,tickid,onetick:OneTick):
        self.tickid=tickid
        self.onetick=onetick

        #or
        #super().__init__(self,open_, high, low, close, volume,wap, count)

    def display(self):
        #pass
        #print(self.tickid,datetime.fromtimestamp(self.onetick.date).strftime("%Y%m%d %H:%M:%S"),self.onetick.open_, self.onetick.high, self.onetick.low, self.onetick.close, self.onetick.volume,self.onetick.wap,self.onetick.count)
        print(self.tickid, self.onetick.date, self.onetick.open_,
              self.onetick.high, self.onetick.low, self.onetick.close, self.onetick.volume, self.onetick.wap,
              self.onetick.count)

class OneStock:
    def __init__(self, contract: OneContract = None,tickid=0):
        # self.ticks = []
        #self.bars: BarData = []
        #self.bars5sec:OneTick=[]
        self.bars5sec: BarData = []
        self.bars1min=[] #this are BarData
        self.bars5min= []
        self.bars15min = []
        self.bars10min = []
        self.bars30min = []
        self.bars2h = []
        self.bars4h = []
        self.barsDay = []
        self.contract = contract
        self.tickid=tickid
        self.panda1min=None
        self.panda5min=pd.DataFrame()
        self.panda30min=pd.DataFrame()

        self.is5secDownloaded=False
        self.is1minDownloaded=False
        self.is1minUpToDate=False


       # if self.tickid==0:
       #     self.tickid=self.contract.contractID


    #  def getOneBar(bar:BarData):
    #      return "'"+bar.date+"',"+bar.open+","+bar.hign+","+bar.low+","+bar.close+","+bar.volume+","+bar.barCount+","+bar.average

    '''def addOneTick(self, oneTick):
        if isinstance(oneTick, OneTick):
            self.ticks.append(oneTick)
        else:
            print("this is not a tick")
'''

    def addOneBar(self, oneBar: BarData):
        if (isinstance(oneBar, BarData)):
            self.bars1min.append(oneBar)



class OnePortfolio:
    def __init__(self):
        #this will have the key the tickid and the
        self.stocks={}


class PanelEngine(threading.Thread):

    def __init__(self, qIn, gui,item):
        threading.Thread.__init__(self)
        self.qIn = qIn
        self.gui=gui
        self.level=0
        self.item=item

    def run(self):
        stop = False
        while stop is False:
            if self.qIn.qsize() == 0:
                # nothing in queue
                time.sleep(1)
                continue

            msg: toMessage2 = self.qIn.get_nowait()
            if msg.purpose == 'exit':
                print('i stop panel engine',self.item.contractID)
                stop = True
                continue

            if msg.purpose == 'level1':
                self.level1()
                continue

            if msg.purpose == 'level2':
                self.level2()
                continue

            print('mesaj unindentify ',msg.purpose)

        print('i just got out from panel engine thread')

    def level1(self):

        print('level1 - start 5sec')
        toTWS = toMessage2('Start5SecWatch', self.item)
        self.gui.toTws.put(toTWS)
        print('level1',self.item.contractID)
        self.gui.toGui.put(toMessage2('histnewLevel1End',self.item))

    def level2(self):
        print('level2','take history on 5 sec')
        toTWS = toMessage2('histnew5secOneTime', self.item)
        self.gui.toTws.put(toTWS)

#keep the button and indicators for one stock
class OnePanel:
    master=None
    height=None
    width=None
    myFont = None

    def __init__(self,x,y,gui):
        self.x=x
        self.y=y
        #self.panel=None #this will hold the panel
        #self.tickID=None
        OnePanel.myFont=font.Font(family='Courier', size=9)
        self.item=None
        self.panelQue = queue.Queue()

        self.gui=gui

    def create(self,item:OneContract):
        self.panel=tk.PanedWindow(OnePanel.master,height=OnePanel.height,width=OnePanel.width)
        #self.panel.place(x=self.x, y=self.y)
        self.panel.grid(row=self.x, column=self.y)
        self.item=copy.deepcopy(item)

        print('create in panel',item.contractID)
        self.panelEngine = PanelEngine(self.panelQue, self.gui,self.item)

        self.bStartWatch = tk.Button(self.panel, text='Start', command=lambda: self.Start(self.item.symbol,self.item.contractID))
        self.bStartWatch['font']=self.myFont
        self.bStartWatch.pack(side='left', padx=2)

        self.idLabel=tk.Label(self.panel,text=self.item.symbol, bg='yellow',width = 8)
        self.idLabel['font'] = OnePanel.myFont
        self.idLabel.pack(side='left', padx=2)

        self.lb30min = tk.Label(self.panel, text='30min', bg='red', width=8)
        self.lb30min['font'] = OnePanel.myFont
        self.lb30min.pack(side='left', padx=2)

        self.lb5min = tk.Label(self.panel, text='5min', bg='red', width=8)
        self.lb5min['font'] = OnePanel.myFont
        self.lb5min.pack(side='left', padx=2)

        self.lb1min = tk.Label(self.panel, text='1min', bg='red', width=8)
        self.lb1min['font'] = OnePanel.myFont
        self.lb1min.pack(side='left', padx=2)

    def updatePanel(self,text30min, text5min,text1min):
        self.lb1min['text']=text1min
        self.lb5min['text'] = text5min
        self.lb30min['text'] = text30min


    def Start(self,symbol,tickID):
        print(symbol,tickID)
        if self.bStartWatch['text']=='Start':
            self.bStartWatch['text']='Stop'
            self.idLabel['bg']='green'
            if self.panelEngine.is_alive():
                print("i am alive not need to start")
                msg = toMessage2('level1')
                self.panelQue.put(msg)
            else:
                print("i will start the thread")
                self.panelEngine.start()
                msg = toMessage2('level1')
                self.panelQue.put(msg)

        elif self.bStartWatch['text']=='Stop':
            self.bStartWatch['text']='Start'
            self.idLabel['bg']='red'
            if self.panelEngine.is_alive():
                print("i am alive I will stop")
                toTWS = toMessage2('Stop5SecWatch', self.item)
                self.gui.toTws.put(toTWS)
                if isinstance(self.item,int):
                    print('self.item is integer')
                if isinstance(self.item,OneContract):
                    print('self.item is Onecontract')

                toWat = toMessage2('stop5sec', self.item)
                self.gui.toWat.put(toWat)


