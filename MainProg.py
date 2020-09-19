# from tkinter import *
import multiprocessing as mp
import sys

from Source.GuiClass import runGui
from Source.AppClass import TestApp
from Source.PredictClasses import runPre


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
    print("cucu")
    gui2tws = mp.Queue()
    tws2gui = mp.Queue()

    gui2pre = mp.Queue()
    pre2gui = mp.Queue()

    tws2pre=mp.Queue()
    pre2tws=mp.Queue()

    gui = mp.Process(target=runGui, args=(gui2tws, tws2gui,gui2pre,pre2gui))
    gui.start()

    pre = mp.Process(target=runPre,args=(gui2tws, tws2gui,gui2pre,pre2gui))
    pre.start()

    app = TestApp(gui2tws, tws2gui,tws2pre,pre2tws)
    #tws2gui.put("ma conectez")
    #app.connect('127.0.0.1', 7496, 1)
    app.run()

    gui.join()
    pre.join()


    print('The History Downloader stopped')
    return 0


if __name__ == "__main__":
    sys.exit(main())

