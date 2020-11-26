import tkinter as tk


class UtilityPredict:

    def __init__(self, gui):
        self.gui = gui
        self.predictButtons()

    def predictButtons(self):
        paneBtnPredict = tk.PanedWindow(self.gui.tab_predict, height="30", width="700")
        paneBtnPredict.place(x=10, y=10)

        self.bAddContract = tk.Button(paneBtnPredict, text="LoadModel", command=self.LoadModel)
        self.bAddContract.pack(side='left')  # place(x=10, y=10)
        self.bUpdateContract = tk.Button(paneBtnPredict, text="LoadWeights", command=self.LoadWeights)
        self.bUpdateContract.pack(side='left')  # place(x=70, y=10)
        '''  
            self.bDeleteContract = tk.Button(paneBtnPredict, text="Delete", command=self.deleteContract)
            self.bDeleteContract.pack(side='left')  # place(x=130, y=10)
            self.bHistNew = tk.Button(paneBtnPredict, text="HistNew", command=self.histnew)
            self.bHistNew.pack(side='left')  # place(x=190, y=10)
            self.bHistOld = tk.Button(paneBtnPredict, text="HistOld", command=self.histold)
            self.bHistOld.pack(side='left')  # place(x=250, y=10)
            self.bverifyData = tk.Button(paneBtnPredict, text="VerifyData", command=self.verifyData)
            self.bverifyData.pack(side='left')  # place(x=250, y=10)
            self.bMarketData = tk.Button(paneBtnPredict, text="MarketData", command=self.marketdata)
            self.bMarketData.pack(side='left')  # place(x=250, y=10)
            self.bCancelMktDt = tk.Button(paneBtnPredict, text="CanlMktDt", command=self.cancelmarketdata)
            self.bCancelMktDt.pack(side='left')  # place(x=250, y=10)
            self.bDispTest = tk.Button(paneBtnPredict, text="Disp-Test", command=self.DispTest)
            self.bDispTest.pack(side='left')  # place(x=270, y=50)
            self.bstartWatch = tk.Button(paneBtnPredict, text="StartWatch", command=self.startWatch)
            self.bstartWatch.pack(side='left')
            self.bstopWatch = tk.Button(paneBtnPredict, text="StopWatch", command=self.stopWatch)
            self.bstopWatch.pack(side='left')
            '''

    def LoadModel(self):
        print("loadModel")

    def LoadWeights(self):
        print("loadweights")


