import datetime as dt

from Source.OnesClasses import OneStock


def getStepSize(barSize,higherDate='',lowerDate=''):
    stepSize = {'1 sec': '1800 S', '5 secs': '3600 S', '10 secs': '14400 S', '30 secs': '28800 S',
                 '1 min': '2 D', '5 mins': '1 W', '30 30 mins': '1 M', '30 mins': '1 D'}
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
def convertToHigher(d,newtime='5min'):
    dic = {'2min': [2, 1],'5min': [5, 1], '15min': [15, 1], '10min': [10, 1], '30min': [30, 1], '2h': [60, 2],'4h': [60, 4]}

    if not(newtime in dic.keys()):
        print(newtime,' is not a valid transformation')
        return None

    format = '%Y%m%d  %H:%M:%S'
    a = dic.get(newtime)[0]
    b = dic.get(newtime)[1]
    i = 0
    res = []
    for item in d:
        d1 = dt.datetime.strptime(item[0], format)
        print(item)

        # no average
        if d1.minute % a == 0 and d1.hour % b == 0:
            if i > 0:
                print('result= ', res[i - 1])
            res.append(item)
            i = i + 1
        elif i > 0:  # skip the first
            res[i - 1][2] = max(res[i - 1][2], item[2])  # maxim
            res[i - 1][3] = min(res[i - 1][3], item[3])  # minimum
            res[i - 1][4] = item[4]  # close
            res[i - 1][5] = res[i - 1][5] + item[5]  # volume
            res[i - 1][6] = res[i - 1][6] + item[6]  # count

    return res

class toTws:
    def __init__(self,purp,obj=None):
        self.purpose=purp
        self.obj=obj


class fromTws:
    #if nextID is -1 than a next id need to be generated
    def __init__(self,purp,obj=None):
        self.purpose=purp
        self.obj=obj

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

    maxDownload=60 #how many I can download
    waittime=600 #
    #def __init__(self,nextID,conID,count=0,dateToDownload=0):
    def __init__(self):
        self.nextID:int=0
        self.startTime=dt.datetime.today() #to keep track when start downloading to wait 10 min
        self.conID:int=0
        self.oneStock:OneStock=OneStock(None)
        self.oneContract=''
        self.count:int=0
        self.dateToDownload:str=''# from where to start to download
        self.whatToDownload:str=''
        self.newestForNewHist:str='' # when start a new history download this is the newest where we suppose to stop
        self.lastDateDownload:str='' #this will be use only for newHist to be able to minimize the downloading

'''
class toTws:
    def __init__(self,purp,nextID=-1,obj=None):
        self.purpose=purp
        self.obj=obj
        self.nextID = nextID

class toTWSHist:
    def __init__(self,datetime=None,ct:OneContract=None):
        self.datetime = datetime
        self.contract = ct

class fromTws:
    #if nextID is -1 than a next id need to be generated
    def __init__(self,purp,nextID=-1,obj=None):
        self.purpose=purp
        self.nextID=nextID
        self.obj=obj


class fromTwsHist:
    def __init__(self,reqID,oneStock:OneStock=None
                 ,ct:OneContract=None
                 ,startHist=None
                 ,endHist=None):
        self.reqID=reqID
        self.oneStock:OneStock=oneStock
        self.contract = ct
        self.startHist=startHist
        self.endHist = endHist

class toTWSMarketData:
    def __init__(self,ct:OneContract,genericTickList="233"):
        self.contract=ct
        self.genericTickList=genericTickList
        pass

'''