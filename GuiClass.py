import tkinter as tk
from tkinter import ttk
import sys
import queue
from tkinter import filedialog as fd

from Source.ChartClass import UtilityChart
from Source.SQLiteClass import DB
from Source.UtilitiesClasses import toTws
from Source.PredictClasses import UtilityPredict
from Source.ContractClasses import UtilityContract

import matplotlib
matplotlib.use("TkAgg")


class Gui:

    def __init__(self, gui2tws, tws2gui,gui2pre,pre2gui):

        self.gui2tws = gui2tws
        self.tws2gui = tws2gui
        self.gui2pre=  gui2pre
        self.pre2gui=  pre2gui

        self.index = 0

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
        # self.root.protocol("WM_DELETE_WINDOW", self.onQuit)

        self.checkMsgFromTws()
        self.checkMsgFromPredict()

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
        self.nameDB = "gigi.db" #default name
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

    def checkMsgFromPredict(self):
        print("checkMsgFromPredict")
        try:
            while not self.tws2gui.empty():
                pass

        except queue.Empty:
            print("empty checkMsgFromPredict")
            pass

        self.root.after(1000, self.checkMsgFromPredict)

    def checkMsgFromTws(self):
        try:
            while not self.tws2gui.empty():
                print("not empty")
                msg = str(self.tws2gui.get_nowait())
                stemp = str(self.index)
                print('checkMsgFromTws msg ',msg)
                self.listbox.insert(0, stemp + "-" + str(msg))
                self.index = self.index + 1

                if msg.startswith('ERROR'):
                    print('TWS Error', msg)
                elif msg.startswith('NEWROW'):
                    print('newrow')
                elif msg.startswith('END'):
                    print('end')
                else:
                    # TODO: Error here?
                    pass
                    print(f'Unknown GUI message: {msg}')
        except queue.Empty:
            print("empty")
            pass

        self.root.after(100, self.checkMsgFromTws)

    def run(self):
        self.init_gui()
        self.root.wm_protocol("WM_DELETE_WINDOW", self.ex)
        self.root.mainloop()

    def ex(self):
        print('exit now')
        to_tws = toTws("exit",None)
        self.gui2tws.put(to_tws)
        self.gui2pre.put(to_tws)
        #time.sleep(1)
        self.root.destroy()

    def connect(self):
        to_tws=toTws("connect",None)
        self.gui2tws.put(to_tws)
        print('i disconect')

    def disconnect(self):
        to_tws = toTws("disconnect",None)
        self.gui2tws.put(to_tws)
        print('i disconect')




    def loaddb(self):
        dbname=self.eLoadDB.get()
        self.dbLite = DB(dbname)
        #self.dbLite.connect()
        rows=self.dbLite.populateContract()
        for row in rows:
           # print(row[0])
            self.contract.treeContracts.insert("", "end", row[0],text="", values=row)
        toTWS = toTws('database',dbname)
        self.gui2tws.put(toTWS)

    def choosedb(self):
        self.dbLite.dbname = fd.askopenfilename(initialdir="C:\\Users\\fb894\\PycharmProjects\\Test")
        self.eLoadDB.insert(0, self.dbLite.dbname)



def runGui(gui2tws, tws2gui,qui2pre,pre2qui):
    gui = Gui(gui2tws, tws2gui,qui2pre,pre2qui)
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
