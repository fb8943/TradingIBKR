import sys
import threading
import datetime as dt
import time
from inspect import getframeinfo, currentframe

import numpy as np
from ibapi.common import BarData

from Source.OnesClasses import OneStock, OneContract
def disLog(arg1, *argv):
    return
    print (arg1+": ")
    for arg in argv:
        print(arg, end =" ")


def getStepSize(barSize,higherDate='',lowerDate=''):
    stepSize = {'1 sec': '1800 S', '5 secs': '3600 S', '10 secs': '14400 S', '30 secs': '28800 S',
                 '1 min': '2 D', '5 mins': '1 W', '30 30 mins': '1 M', '30 mins': '1 D'}
#    stepSize = {'1 sec': '1800 S', '5 secs': '60 S', '10 secs': '14400 S', '30 secs': '28800 S',
#                '1 min': '2 D', '5 mins': '1 W', '30 30 mins': '1 M', '30 mins': '1 D'}


    if higherDate=='' or lowerDate=='' or barSize != '1 min':
        return stepSize.get(barSize)
    print(higherDate,lowerDate)
    format1 = '%Y%m%d %H:%M:%S'
    format2 = '%Y%m%d  %H:%M:%S'
    d0 = dt.datetime.strptime(higherDate, format1)
    d1 = dt.datetime.strptime(lowerDate, format2)
    delta = (d0 - d1).total_seconds()
    print(delta)


    if delta<1800:
        return '1800 S'
    if delta<3600:
        return '3600 S'
    if delta<14400:
        return '14400 S'
    if delta<28800:
        return '28800 S'
    if delta<1800:
        return '28800 S'
    if delta<86400:
        return '1 D'
    return '2 D'


    return ''


#to classes that will send messages to TWS
#from classes that will receive back Message from TWS
def findMinMax(data,size):
    min1=[]
    max1=[]
    if size>=len(data):
        return  min1, max1
    i=size
    for item in data[size:-size]:
        a=data[i-size:i+size+1]
        print(a,a.index(max(a)))
        if a.index(max(a))==i:
            max1.append(a[i])
        if a.index(min(a))==i:
            min1.append(a[i])
        i=i+1
    return min1, max1


def convertToSameVolume(d,volume):
    res=[]#result
    i=0
    res.append([0,-100000,100000])#append first bar
    for item in d:
        print(item)
        if volume-res[i][0]>item[5]:
            #we can put the entire item in
            res[i][0]=res[i][0]+item[5]
            res[i][1]=max(res[i][1],item[2])
            res[i][2] = min(res[i][2], item[3])
        else:
            #we need to break the item in multiple and add extra items in res
            while True:
        #we need to adjust the 
                if item[5] > (volume - res[i][0]): #will have to add more
                    item[5] = item[5] - (volume - res[i][0])
                    res[i][0] = volume
                    res[i][1] = max(res[i][1], item[2])
                    res[i][2] = min(res[i][2], item[3])

                    print(res[i])
                    res.append([0, -100000, 100000])
                    i = i + 1

                else:
                    #we don't have to add more to res
                    res[i][0] = res[i][0]+item[5]
                    res[i][1] = max(res[i][1], item[2])
                    res[i][2] = min(res[i][2], item[3])
                    print(res[i])
                    if res[i][0]==volume:
                        #we fill up this one
                        res.append([0, -100000, 100000])
                        i = i + 1
                    break

    print('----------final-----------')
    for it in res:
        print(it)


#this function will convert 1min bars to 5min, 10 min, etc
#item in d are on the form of [date,open,high,low,close,volume,count
def convertToHigher(d,newtime='5min'):
    #we got 1min because we can convert 5 sec to 1 min
    dic = {'1min':[1,1],'2min': [2, 1],'5min': [5, 1], '15min': [15, 1], '10min': [10, 1], '30min': [30, 1],
           '1h': [60, 1],'2h': [60, 2],'4h': [60, 4]}

    if not(newtime in dic.keys()):
        print(newtime,' is not a valid transformation -converToHigher in Utilitieclasses.py')
        return None

    format = '%Y%m%d  %H:%M:%S'
    a = dic.get(newtime)[0]
    b = dic.get(newtime)[1]
    i = 0
    res = []
    for item in d:
        d1 = dt.datetime.strptime(item[0], format)
        disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),item)

        # no average
        if d1.minute % a == 0 and d1.hour % b == 0 and d1.second==0:
            if i > 0:
                disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno), 'result= ', res[i - 1])
            it = BarData()
            it.date = item.date
            it.high = item.high
            it.open = item.open
            it.low = item.low
            it.close = item.close
            it.volume = item.volume
            it.barCount = item.barCount
            it.average = item.average
            res.append(it)
            i = i + 1
        elif i > 0:  # skip the first
            res[i - 1][2] = max(res[i - 1][2], item[2])  # high
            res[i - 1][3] = min(res[i - 1][3], item[3])  # low
            res[i - 1][4] = item[4]  # close
            res[i - 1][5] = res[i - 1][5] + item[5]  # volume
            res[i - 1][6] = res[i - 1][6] + item[6]  # count

    #return res this is a list
    return np.array(res) #return as a numpy

#this function will convert 1min bars to 5min, 10 min, etc
#item in d are of BarData
def convertToHigherBarData(d,newtime='5min'):
    #we got 1min because we can convert 5 sec to 1 min
    dic = {'1min':[1,1],'2min': [2, 1],'5min': [5, 1], '15min': [15, 1], '10min': [10, 1], '30min': [30, 1],
           '1h': [60, 1],'2h': [60, 2],'4h': [60, 4]}

    if not(newtime in dic.keys()):
        print(newtime,' is not a valid transformation -converToHigher in Utilitieclasses.py')
        return None

    format = '%Y%m%d  %H:%M:%S'
    a = dic.get(newtime)[0]
    b = dic.get(newtime)[1]
    i = 0
    res = []
    for item in d:
        #item:BarData=ite
        d1 = dt.datetime.strptime(item.date, format)

        # no average
        if d1.minute % a == 0 and d1.hour % b == 0 and d1.second==0:
            it = BarData()
            it.date = item.date
            it.high = item.high
            it.open = item.open
            it.low = item.low
            it.close = item.close
            it.volume = item.volume
            it.barCount = item.barCount
            it.average = item.average
            res.append(it)
            i = i + 1
        elif i > 0:  # skip the first
            res[i - 1].high = max(res[i - 1].high, item.high)  # high
            res[i - 1].low= min(res[i - 1].low, item.low)  # low
            res[i - 1].close = item.close # close
            res[i - 1].volume = res[i - 1].volume + item.volume  # volume
            res[i - 1].count = res[i - 1].barCount + item.barCount  # count

    #return res this is a list
    return res #return as a list of BarData

class toMessage:
    def __init__(self,purp,obj=None):
        self.purpose=purp
        self.obj=obj


class fromTws:
    #if nextID is -1 than a next id need to be generated
    def __init__(self,purp,obj=None):
        self.purpose=purp
        self.obj=obj

        #this class will manage the start of the stocks



class DownloadLimit(threading.Thread):
    maxDownload = 60  # 60 how many I can download
    waittime = 600  # 600
    counter = 0
    start_time=0

    #def __init__(self,qIn,qOut,toTWS,toGui):
    def __init__(self, qIn, toTWS, toGui):
        threading.Thread.__init__(self)

        self.qIn=qIn
        #self.qOut=qOut
        #so we can send messages to TWS
        self.toTWS=toTWS
        self.toGui=toGui

        pass
    ''' as a static
    @staticmethod
    def limit():
        DownloadLimit.counter+=1
    '''

    def run(self):
        stop=False
        while stop is False:
            if self.qIn.qsize()==0:
                #nothing in queue
                time.sleep(1)
                #print('sleep 2 second in DownloadLimit')
                continue

            msg:toMessage=self.qIn.get_nowait()
            if msg.purpose=='exit':
                stop=True
                continue

            if msg.purpose=='HistFinish':
                dlHistInfo:downloadHist=msg.obj

                DownloadLimit.counter+=1 #this will be already 61
                print('DownloadLimit.counter is ',DownloadLimit.counter)
                if DownloadLimit.counter>DownloadLimit.maxDownload+1:

                    msg2: toMessage = toMessage('Buttons', 'Disable')
                    self.toGui.put(msg2)

                    time.sleep(DownloadLimit.waittime)
                    #reset the counter
                    DownloadLimit.counter=0
                    msg4: toMessage = toMessage('Buttons', 'Enable')
                    self.toGui.put(msg4)

                if dlHistInfo.whatToDownload=='histold':

                    msg3:toMessage=toMessage('histold')
                    msg3.obj=dlHistInfo.oneContract
                    self.toTWS.put(msg3)

                if dlHistInfo.whatToDownload=='histnew':
                    msg3:toMessage = toMessage('histnew')
                    msg3.obj = dlHistInfo.oneContract
                    self.toTWS.put(msg3)


    @classmethod
    def limit(cls):
        cls.counter+=1
        if cls.counter>cls.maxDownload:
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   'already download: ',cls.maxDownload,' need to wait now')
            time.sleep(cls.waittime)
            disLog(getframeinfo(currentframe()).filename+":"+sys._getframe().f_code.co_name+":"+str(getframeinfo(currentframe()).lineno),
                   'you waited:',cls.waittime)
            counter=1





class downloadHist:
    #we don't want to go to further in the past for contracts 3 month for ES
    #1 month for CL,NG,RG

    def getStartFutureDate(symb,dt):
        year =int(dt[:4])
        month=int(dt[4:])
        print(year,month)
        if symb in ('ES','NQ','YM','RTY','ZS','ZW','ZC'):
            month=month-3
            if month <= 0 :
                year=year-1
                month=month+12
            print(year,month)
            month=str(month).zfill(2)
            rtn=str(year)+month+'01  10:00:00'
            print(rtn)
            return rtn
        if symb in ('CL','NG','RB'):
            month=month-2
            if month <= 0 :
                year=year-1
                month=month+12
            print(year,month)
            month=str(month).zfill(2)
            rtn=str(year)+month+'01  10:00:00'
            print(rtn)
            return rtn

        return ''


    #def __init__(self,nextID,conID,count=0,dateToDownload=0):
    def __init__(self):
        #self.nextID:int=0
        self.startTime=dt.datetime.today() #to keep track when start downloading to wait 10 min
        self.conID:int=0
        self.oneStock:OneStock=OneStock(None)
        self.oneContract:OneContract=''
        self.count:int=0 #this count is use on total history to download and will not allow more than 60
        self.dateToDownload:str=''# from where to start to download
        self.whatToDownload:str=''
        self.newestForNewHist:str='' # when start a new history download this is the newest where we suppose to stop
        self.lastDateDownload:str='' #this will be use only for newHist to be able to minimize the downloading

