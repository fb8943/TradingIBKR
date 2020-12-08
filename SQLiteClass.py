import sqlite3 as sq
import datetime
import pandas as pd
import numpy as np
from ibapi.common import BarData

from Source.OnesClasses import OneStock, OneContract
from Source.UtilitiesClasses import downloadHist


class DB:
    def __init__(self, dbname):
        self.dbname = dbname
        self.conn = ''
        if self.dbname != '':
            self.conn = sq.connect(self.dbname, timeout=10)
            self.createTableContract()
        self.contracts=[]


#    def connect(self):
#        if self.dbname != '':
#            self.conn = sq.connect(self.dbname, timeout=10)
#            self.createTableContract()
#        else:
#            print("no database name")


    def __del__(self):
     if self.conn != '':
        self.conn.close()

    def createTableContract(self):
        sql = """CREATE TABLE if not exists Contract (
                    conID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                    currency       TEXT,
                    exchange       TEXT,
                    expire			TEXT,
                    includeExpired BOOLEAN DEFAULT ( 0 ),
                    localSymbol    TEXT,
                    multiplier     TEXT,
                    primaryExch    TEXT,
                    putcall        TEXT,
                    secId          TEXT,
                    secIdType      TEXT,
                    secType        TEXT NOT NULL,
                    strike         REAL,
                    symbol         TEXT,
                    tradingClass   TEXT,
                    barSize        TEXT,
                    whatToShow   TEXT,
                    active       TEXT,
                    ordersize TEXT,
                    stopsize TEXT,
                    orderextra TEXT);"""
        self.conn.execute(sql)

    def createTableStock(self,conId):
        #wap - The bar's Weighted Average Price
        sql = """CREATE TABLE if not exists T{0}
         (Date DATETIME UNIQUE,
        Open   REAL,
        High   REAL,
        Low    REAL,
        Close  REAL,
        Volume  INTEGER,
        Count INTEGER,
        Average INTEGER)""".format(conId);
        print(sql)
        self.conn.execute(sql)

    def addContract(self,oneContract):
         #sql = "INSERT INTO Contract (currency, exchange, expiry,includeExpired,localSymbol,multiplier,primaryExch,putcall,secId,secIdType,secType,strike,symbol,tradingClass,barSize,whatToShow) Values (" +oneContract.getValues()+");";
         sql = "INSERT INTO Contract (currency, localSymbol, expire,primaryExch,secType,barSize,whatToShow,active,ordersize,stopsize,orderextra) Values (" + oneContract.getValues() + ");";
         cur = self.conn.cursor()
         cur.execute(sql)
         self.conn.commit()
         self.createTableStock(cur.lastrowid)
         #self.conn.execute(sql)
         #print(sql)
         #print(cur.lastrowid)
         return cur.lastrowid

    def addOneStock(self,dwHist:downloadHist):
        rtn = ''
        try:
            cur = self.conn.cursor()

            print('first bar ',dwHist.oneStock.bars1min[0])
            print('last bar ', dwHist.oneStock.bars1min[-1])

            for item in dwHist.oneStock.bars1min:

                it:BarData=item
                if dwHist.newestForNewHist >= it.date:
                    #print(' i got to stop in SQLLiteClass')
                    #print(dwHist.newestForNewHist,' -- ',it.date)
                    rtn='stop'
                    #return 'stop' totaly wrong to do it here
                else:
                    sql="INSERT INTO T{0} VALUES('{1}',{2},{3},{4},{5},{6},{7},{8})".format(dwHist.conID, it.date,it.open,it.high,it.low,it.close,it.volume,it.barCount,it.average)
                    # print(sql)
                    cur.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(e)

        return rtn

    #this will return a dictionary Open1min,Date1min,etc
    def getOneStockDic(self,symbol,limit='ALL',rth='NO'):
        cur = self.conn.cursor()
        if limit=='ALL':
            if rth=='NO':
                sql="SELECT * FROM {0} order by date".format('T'+str(symbol))
            else:
                sql = "SELECT * FROM {0} where substr(Date,11,8)>='06:30:00' " \
                      " and substr(Date,11,8)< '13:00:00' order by date".format('T' + str(symbol))
        else:
            if rth=='NO':
                strSQL="SELECT count(*) FROM {0}".format('T'+str(symbol))
            else:
                strSQL = "SELECT count(*) FROM {0} where substr(Date,11,8)>='06:30:00'" \
                      " and substr(Date,11,8)< '13:00:00'".format('T' + str(symbol))
            cur.execute(strSQL)
            result = cur.fetchone()
            start = result[0] - limit
            if rth=='NO':
                sql = "SELECT * FROM {0} order by date limit {1},{2}".format('T' + str(symbol), start, limit)
            else:
                sql = "SELECT * FROM {0} where substr(Date,11,8)>='06:30:00'" \
                      " and substr(Date,11,8)< '13:00:00' order by date limit " \
                      "{1},{2}".format('T' + str(symbol), start, limit)

        cur.execute(sql)
        rows=cur.fetchall()

        Date1min=[]
        Open1min=[]
        High1min=[]
        Low1min=[]
        Close1min=[]
        Volume1min=[]
        Count1min=[]
        Average1min=[]

        x={'D1min':Date1min,'O1min':Open1min,'H1min':High1min,'L1min':Low1min,
           'C1min':Close1min,'V1min':Volume1min,'N1min':Count1min,'A1min':Average1min}
        #oneStock=OneStock() suppose to return oneStock not a list
        for row in rows:
            x['D1min'].append(row[0]) #Date
            x['O1min'].append(row[1]) #Open
            x['H1min'].append(row[2]) #High
            x['L1min'].append(row[3]) #low
            x['C1min'].append(row[4]) #close
            x['V1min'].append(row[5]) #Volume
            x['N1min'].append(row[6]) #count
            x['A1min'].append(row[7]) #average
        return x

        # this will return a multidimensional array
    def getOneStock(self, symbol):
            cur = self.conn.cursor()
            sql = "SELECT * FROM {0} order by date".format('T' + str(symbol))
            cur.execute(sql)
            rows = cur.fetchall()
            x = []
            # oneStock=OneStock() suppose to return oneStock not a list
            for row in rows:
                x.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]])
            return x

    #this will return an Array of OneStock
    def getOneStock2(self,symbol,limit='ALL'):
        cur = self.conn.cursor()
        if limit=='ALL':
            sql="SELECT * FROM {0} order by date".format('T'+str(symbol))
        else:
            strSQL="SELECT count(*) FROM {0}".format('T'+str(symbol))
            cur.execute(strSQL)
            result=cur.fetchone()
            start=result[0]-limit
            sql = "SELECT * FROM {0} order by date limit {1},{2}".format('T' + str(symbol),start,limit)
        cur.execute(sql)
        rows=cur.fetchall()

        oneStock=OneStock() #suppose to return oneStock not a list
        oneStock.tickid=symbol
        for row in rows:
            oneBar=BarData()
            oneBar.date=row[0]
            oneBar.open=row[1]
            oneBar.high=row[2]
            oneBar.low=row[3]
            oneBar.close=row[4]
            oneBar.volume=row[5]
            oneBar.barCount=row[6]
            oneBar.average=row[7]

            oneStock.bars1min.append(oneBar)
        return oneStock

    #this will return a pandas structure
    def getOneStockPandas(self,symbol,limit='ALL'):
        cur = self.conn.cursor()
        if limit == 'ALL':
            sql = "SELECT * FROM {0} order by date".format('T' + str(symbol))
        else:
            strSQL = "SELECT count(*) FROM {0}".format('T' + str(symbol))
            cur.execute(strSQL)
            result = cur.fetchone()
            start = result[0] - limit
            sql = "SELECT * FROM {0} order by date limit {1},{2}".format('T' + str(symbol), start, limit)

        return pd.read_sql_query(sql, self.conn)

    #this will return a numpy structure
    def getOneStockNumpy(self,symbol,limit='ALL'):
        cur = self.conn.cursor()
        if limit == 'ALL':
            sql = "SELECT * FROM {0} order by date".format('T' + str(symbol))
        else:
            strSQL = "SELECT count(*) FROM {0}".format('T' + str(symbol))
            cur.execute(strSQL)
            result = cur.fetchone()
            start = result[0] - limit
            sql = "SELECT * FROM {0} order by date limit {1},{2}".format('T' + str(symbol), start, limit)
            cur.execute(strSQL)
            alist = cur.fetchall()
            return np.array(alist)

        return pd.read_sql_query(sql, self.conn)

    #ordersize,stopsize,orderextra

    def populateContract(self):
        cur = self.conn.cursor()
        cur.execute("SELECT conID,currency, localSymbol, expire,primaryExch,secType,barSize,whatToShow,active,ordersize,stopsize,orderextra FROM Contract order by localSymbol asc")

        rows = cur.fetchall()
        return rows

    def getActive(self):
        cur = self.conn.cursor()
        sql = "SELECT currency, localSymbol, expire,primaryExch,secType,barSize,whatToShow,active,\
        ordersize,stopsize,orderextra,conID FROM Contract where active='Yes' order by localSymbol"
        cur.execute(sql)
        rows = cur.fetchall()
        x = []
        # oneStock=OneStock() suppose to return oneStock not a list
        for row in rows:
            x.append(OneContract(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],row[8], row[9], row[10],row[11]))
        return x

    def getItem(self,conID):
        cur = self.conn.cursor()
        sql = "SELECT currency, localSymbol, expire,primaryExch,secType,barSize,whatToShow,active,\
        ordersize,stopsize,orderextra,conID FROM Contract where conID="+str(conID)
        cur.execute(sql)
        rows = cur.fetchall()
        x = []
        # oneStock=OneStock() suppose to return oneStock not a list
        for row in rows:
            return OneContract(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10],row[11])


    def deleteContract(self,conID):
        sql="Delete from Contract where conID = "+conID
        self.conn.execute(sql)
        self.conn.commit()
        self.deleteTableStock(conID)

    def deleteTableStock(self, conId):
        sql = "drop table T" + conId
        self.conn.execute(sql)
        self.conn.commit()

    def Update(self, val):
        sql = "update Contract set currency='{1}', localSymbol='{2}', expire='{3}',primaryExch='{4}',\
        secType='{5}',barSize='{6}',whatToShow='{7}',active='{8}',ordersize='{9}',stopsize='{10}',orderextra='{11}'\
         where conId={0};".format(*val)
        print(sql)
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

    def getMinDateTime(self, conID):
        cur = self.conn.cursor()
        sql = "SELECT min(date)  FROM T{0};".format(conID)
        cur.execute(sql)
        rows = cur.fetchall()
        dt = rows[0][0]
        if dt==None:
            dt = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
        return dt

    def getMaxDateTime(self, conID):
        cur = self.conn.cursor()
        sql = "SELECT max(date)  FROM T{0};".format(conID)
        cur.execute(sql)
        rows = cur.fetchall()
        dt = rows[0][0]
        return dt


    def getNumberOfBars(self,conID):
        cur = self.conn.cursor()
        sql = "SELECT count()  FROM T{0};".format(conID)
        cur.execute(sql)
        rows = cur.fetchall()
        cnt = rows[0][0]
        return cnt

    def isTableValid(self,id):
        cur = self.conn.cursor()
        sql="SELECT name  FROM sqlite_master WHERE type='table' AND name='T{0}';".format(id)
        print(sql)

        cur.execute(sql)

        rows = cur.fetchall()
        print(len(rows))


        for row in rows:
            print(row[0])

        return len(rows)

