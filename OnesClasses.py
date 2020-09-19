# this will have OneTick,OneStock and OneContract
from ibapi.common import BarData


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


class OneTick:
    def __init__(self, open, high, low, close, volume):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


class OneStock:
    def __init__(self, contract: OneContract = None):
        # self.ticks = []
        self.bars: BarData = []
        self.bars5min: BarData = []
        self.bars15min: BarData = []
        self.bars10min: BarData = []
        self.bars30min: BarData = []
        self.bars2h: BarData = []
        self.bars4h: BarData = []
        self.barsDay: BarData = []
        self.contract = contract

    def clear(self):
        for item in self.bars:
            self.bars

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
            self.bars.append(oneBar)


class OnePortfolio:
    def __init__(self):
        self.stocks: OneStock = []
