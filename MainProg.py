# from tkinter import *
import multiprocessing as mp
import sys

from Source.GuiClass import runGui
from Source.AppClass import TestApp
from Source.UtilitiesClasses import disLog
from Source.WatchClasses import runWat

from inspect import currentframe, getframeinfo
'''
def old():
    window = Tk()

    window.geometry("300x300")
    window.title("welcome")
    lab = Label(window, text="some", fg='blue')
    lab2 = Label(window, text="other", fg='red')
    lab.grid(row=1, column=1)
    # lab2.grid(row=3,column=5)

    # lab.pack()
    # lab2.pack()

    # lab.place(x=20,y=40)
    lab2.place(x=20, y=80)

    b1 = Button(window, text="Press", command=action)
    b1.place(x=100, y=100)

    window.mainloop()


def action():
    lab['text'] = "bubu"
    lab.place(x=200, y=200)
'''



def main():

    toTws = mp.Queue()
    toGui = mp.Queue()
    toWat = mp.Queue()

    gui = mp.Process(target=runGui, args=(toTws, toGui,toWat))
    gui.start()

    pre = mp.Process(target=runWat,args=(toTws, toGui,toWat))
    pre.start()

    app = TestApp(toTws, toGui,toWat)
    #toGui.put("ma conectez")
    #app.connect('127.0.0.1', 7496, 1)
    app.run()

    gui.join()
    pre.join()


    print('The History Downloader stopped')
    return 0


if __name__ == "__main__":
    sys.exit(main())

