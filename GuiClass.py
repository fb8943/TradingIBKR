import datetime
import tkinter as tk
from tkinter import ttk
import sys
import queue
from tkinter import filedialog as fd

from Source.ChartClass import UtilityChart
from Source.OnesClasses import OneStock
from Source.SQLiteClass import DB
from Source.UtilitiesClasses import toMessage,DownloadLimit
from Source.PredictClasses import UtilityPredict
from Source.ContractClasses import UtilityContract
from Source.WatchClasses import UtilityWatch

import matplotlib
import time
matplotlib.use("TkAgg")
import queue

class Gui:

    def __init__(self, toTws, toGui,toWat):

        self.toTws = toTws
        self.toGui = toGui
        self.toWat=  toWat

        self.exit=False
        self.index = 0
        self.dlQueToLimit=queue.Queue()
        #self.dlQueFromLimit = queue.Queue()
        #self.downloadLimit=DownloadLimit(self.dlQueToLimit,self.dlQueFromLimit,self.toTws, self.toGui)
        self.downloadLimit = DownloadLimit(self.dlQueToLimit, self.toTws, self.toGui)
        self.downloadLimit.start()
        self.dbLite=DB("")

    def geGui2tws(self):
        print('here')

    def init_gui(self):
        # root = self.root = tk.Tk()
        self.root = tk.Tk()
        self.root.geometry("1600x600")
        self.root.title("welcome")

        self.create_tabs()

        self.create_tab_connect()
        self.create_tab_contracts()
        self.create_tab_predict()
        self.create_tab_chart()
        self.create_tab_watch()
        # self.root.protocol("WM_DELETE_WINDOW", self.onQuit)

        self.checkMsg()
        #self.checkMsgFromPredict()

    def create_tabs(self):
        tabControl = ttk.Notebook(self.root)

        self.tab_connect = ttk.Frame(tabControl)
        tabControl.add(self.tab_connect, text="Connect")

        self.tab_contracts = ttk.Frame(tabControl)
        tabControl.add(self.tab_contracts, text="Contracts")

        self.tab_predict = ttk.Frame(tabControl)
        tabControl.add(self.tab_predict, text="Predict")

        self.tab_chart = ttk.Frame(tabControl)
        tabControl.add(self.tab_chart, text="Chart")

        self.tab_watch = ttk.Frame(tabControl)
        tabControl.add(self.tab_watch, text="Watch")

        tabControl.pack(expand=True, fill="both")

    def create_tab_connect(self):
        # self.bConnect = tk.Button(self.root, text="Connect", command=self.connect)
        self.bConnect = tk.Button(self.tab_connect, text="Connect", command=self.connect, background='green',
                                  foreground='white')
        self.bConnect.place(x=10, y=10)

        self.bDisconnect = tk.Button(self.tab_connect, text="Disconnect", command=self.disconnect)
        self.bDisconnect.place(x=10, y=50)

        self.bLoadDB = tk.Button(self.tab_connect, text="Load DB", command=self.loaddb)
        self.bLoadDB.place(x=10, y=90)

        self.eLoadDB = tk.Entry(self.tab_connect, width=30)
        self.eLoadDB.place(x=70, y=90)
        self.nameDB = "C:\\Users\\fb894\\PycharmProjects\\Test\\gigi.db" #default name
        self.eLoadDB.insert(0, self.nameDB)

        self.bchooseDB = tk.Button(self.tab_connect, text="Choose DB", command=self.choosedb)
        self.bchooseDB.place(x=270, y=90)

        self.scrollbar = tk.Scrollbar(self.tab_connect)
        self.scrollbar.place(x=80, y=200, height=160, width=20)
        # self.scrollbar.pack()
        self.listbox = tk.Listbox(self.tab_connect, height=10, width=60)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.place(x=100, y=200)

    def create_tab_contracts(self):
        self.contract = UtilityContract(self)
        pass

    def create_tab_predict(self):
        # self.bConnect = tk.Button(self.root, text="Connect", command=self.connect)
        self.predict=UtilityPredict(self)

    def create_tab_chart(self):
        self.chart=UtilityChart(self)

    def create_tab_watch(self):
        self.watch=UtilityWatch(self)

    def buttons(self,action):
        if(action=='Enable'):
            self.contract.enableBtn()
        elif(action=='Disable'):
            self.contract.disableBtn()
        else:
            print("unknows actions in buttons function in GuiClass.py")

    def checkMsg(self):

        try:
            while not self.toGui.empty():
                #print("not empty")
                msg:toMessage = self.toGui.get_nowait()
                #stemp = str(self.index)
                #print('checkMsgFromTws msg ',msg.purpose)
                #self.listbox.insert(0, stemp + "-" + msg.purpose)
                #self.index = self.index + 1

                if msg.purpose=='ERROR':
                    print('TWS Error', str(msg.obj))
                elif msg.purpose=='NEWROW':
                    print('newrow')
                elif msg.purpose=='END':
                    print('end')
                elif msg.purpose=='HistFinish':
                    print('HistFinish')
                    #send message to DownloadLimit class in UtilitiesClasses.py
                    self.dlQueToLimit.put(msg)# put the message in the thread queue
                elif msg.purpose=='Buttons':
                    self.buttons(msg.obj)
                elif msg.purpose=='load1min':
                    self.load1min(msg.obj)
                elif msg.purpose=='histnewLevel1End':
                    self.load1min(msg.obj)  # let's load the 1 min and send to the watch
                elif msg.purpose=='UpdatePanels':
                    self.updatePanels(msg.obj)
                else:
                    # TODO: Error here?
                    pass
                    print(f'Unknown GUI message: {msg}')
        except queue.Empty:
            print("check Msg is empty in gui")
            pass
        #stop the loop

        if self.exit==False:
            self.root.after(100, self.checkMsg)

    def updatePanels(self,item):
        #print('updatePanel ',item[0],item[1],item[2],item[3])
        self.watch.Panels[item[0]].updatePanel(item[1])

    def load1min(self,item):
        if self.dbLite==None:
            print('Database is not loaded - load1min')
            return

        if isinstance(item, int)==True:
            item=self.dbLite.getItem(item)
            print('item is integer',item)
        else:
            print('item is item')

        #let's verify if we really need data
        dt = self.dbLite.getMaxDateTime(item.contractID)
        print('load1min in gui',dt)
        FMT1 = '%Y%m%d  %H:%M:%S'
        s1 = datetime.datetime.strftime(datetime.datetime.now(), FMT1)

        tdelta = datetime.datetime.strptime(s1, FMT1) - datetime.datetime.strptime(dt, FMT1)
        if tdelta.seconds > 3000:
            print('load1min','we need to take the 1 minute data in level1')
            toTWS = toMessage('histnewLevel1', item)
            self.toTws.put(toTWS)
        else:
            print('load1min', 'we have the data load and go level2')
            #let's download only 3000 bars

            #oneMin:OneStock=self.dbLite.getOneStock2(item.contractID,3000)
            #panda1min=self.dbLite.getOneStockPandas(item.contractID,3000)
            if item.sectype=='FUT':
                RTH='NO'
            else:
                RTH='YES'
            print('security type',item.sectype)
            dic1min=self.dbLite.getOneStockDic(item.contractID,3000,RTH)

            #mes=toMessage('data1min',[item.contractID,oneMin,panda1min])
            mes = toMessage('data1min', [item.contractID, dic1min])
            self.toWat.put(mes)

            time.sleep(1)  # not sure if necessary
            self.watch.Panels[item.contractID].panelQue.put(toMessage('level2'))

    def run(self):
        print("init_gui")
        self.init_gui()
        print("init_gui2")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.ex)
        print("init_gui3")
        self.root.mainloop()

    def ex(self):
        print('exit now')
        self.watch.StopPanelEngines()
        mes = toMessage("exit", None)
        #self.watch.myQueue.queue.clear()
        #self.watch.myQueue.clear()
        self.dlQueToLimit.put(mes)
        time.sleep(1)

        self.toTws.put(mes)
        self.toWat.put(mes)
        self.exit=True
        #time.sleep(1)
        self.root.destroy()

    def connect(self):
        to_tws=toMessage("connect", None)
        self.toTws.put(to_tws)
        print('i connect')

    def disconnect(self):
        to_tws = toMessage("disconnect", None)
        self.toTws.put(to_tws)
        print('i disconect')


    def loaddb(self):
        dbname=self.eLoadDB.get()
        self.dbLite = DB(dbname)
        #self.dbLite.connect()
        rows=self.dbLite.populateContract()
        for row in rows:
           # print(row[0])
            self.contract.treeContracts.insert("", "end", row[0],text="", values=row)
        toTWS = toMessage('database', dbname)
        self.toTws.put(toTWS)

    def choosedb(self):
        self.dbLite.dbname = fd.askopenfilename(initialdir="C:\\Users\\fb894\\PycharmProjects\\Test")
        self.eLoadDB.insert(0, self.dbLite.dbname)



def runGui(toTws, toGui,toPre):
    gui = Gui(toTws, toGui,toPre)
    gui.run()


# region main
# -------------------------------------------------------------------------------
if __name__ == '__main__':
    print(__doc__)
    print('This is a python library - not standalone application')

    #    runGui(gui2tws.Queue())
    #sys.quit(-1)
    sys.exit(-1)
# endregion main
