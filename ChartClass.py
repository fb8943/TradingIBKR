import tkinter as tk
import talib
import numpy as np

#from GuiClass import Gui

'''
figure = Figure(figsize=(5, 4), dpi=100)
plot = figure.add_subplot(1, 1, 1)

plot.plot(0.5, 0.3, color="red", marker="o", linestyle="")

x = [0.1, 0.2, 0.3]
y = [-0.1, -0.2, -0.3]
plot.plot(x, y, color="blue", marker="x", linestyle="")

canvas = FigureCanvasTkAgg(figure, self.tab_chart)
canvas.get_tk_widget().grid(row=0, column=0)
'''

class UtilityChart:
    pan2Height = 0
    def __init__(self,gui):
        self.gui=gui
        self.createPanes(gui)
        self.createCanvas()

        #self.mycanvas.create_rectangle(10, 20, 50, 70, fill="white")
        #uc = self.mycanvas.create_rectangle(90, 150, 200, 300, fill="blue")

        #self.mycanvas.addtag_closest("cc", 90, 150)

        # add some widgets to the canvas
        #self.mycanvas.create_line(0, 0, 200, 100)

        #self.mycanvas.create_line(0, 100, 200, 0, fill="white", dash=(4, 4))

        # tag all of the drawn widgets
        #self.mycanvas.addtag_all("all")

    def createCanvas(self):
        self.addBtn = tk.Button(self.paneRight, text="Add", command=self.add, bg="yellow", width="5")
        self.addBtn.place(x=10, y=10)

        self.leftBtn = tk.Button(self.paneRight, text="left", command=self.moveLeft, bg="red", width="5")
        self.leftBtn.place(x=10, y=40)

        self.rightBtn = tk.Button(self.paneRight, text="right", command=self.moveRight, bg="green", width="5")
        self.rightBtn.place(x=10, y=70)

        self.emaBtn = tk.Button(self.paneRight, text="EMA", command=self.ema, bg="white", width="5")
        self.emaBtn.place(x=10, y=100)

        self.listBox = tk.Listbox(self.paneRight,width=15,height=3,selectmode='extended',bg="white")
        self.listBox.place(x=10,y=150)
        self.listBox.bind('<ButtonRelease-1>',self.listBoxClick)

        self.mycanvas = ResizingCanvas(self.paneLeft, width=850, height=400, bg="white", highlightthickness=0, name='222')
        self.mycanvas.pack(fill='both', expand=True, side='top')
        self.mycanvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.mycanvas.bind_all("<Control_L>", self.on_control)
        self.mycanvas.bind_all("<KeyRelease-Control_L>", self.on_control_release)
        self.control_press=False
        # mycanvas.grid(row=1,column=1)
        self.mycanvas2 = ResizingCanvas(self.paneLeft, width=150, height=400, bg="grey", highlightthickness=0,
                                        name='111')
        self.mycanvas2.pack(fill='both', expand=True, side='bottom')

    def on_mousewheel(self,event):
        if self.control_press== False:
            return
        if event.delta >0 :
            self.moveLeft()
        else:
            self.moveRight()

    def on_control(self,event):
        self.control_press=True

    def on_control_release(self,event):
        self.control_press = False

    def ema(self):
        self.minmax()
        return
        if self.data !=None:
            self.mainChart.items.append(self.mainChart.update_ema({'period':10,'color':'red','width':3}))
            self.mainChart.draw()

    def minmax(self):
        if self.data !=None:
            self.mainChart.items.append(self.mainChart.update_minmax({'period':10,'color':'red','radius':5}))
            self.mainChart.draw()


    def listBoxClick(self,event):
        #print(event)
        all_items = self.listBox.get(0, tk.END)
        #print(all_items)
        selection = self.listBox.curselection()
        sel_list = [all_items[item] for item in selection]
        dash=sel_list[0].find('-')
        print(sel_list[0][0:dash])
        #stock='T'+sel_list[0][0:dash]
        stock = sel_list[0][0:dash]
        self.data = self.gui.dbLite.getOneStock(stock)
        self.mainChart = Chart(self.data, self.mycanvas)
        #we have a better name than first
        self.mainChart.items.append(self.mainChart.update_candles({'name':'first'}))
        self.mainChart.draw()

    def moveLeft(self):
        #if self.mainChart.endCandle <len(self.data):
        #    self.mainChart.endCandle=self.mainChart.endCandle+1
        for item in self.mainChart.items:
            if item.get('endCandle')!=None:
                if item['endCandle']<len(self.data):
                    item['endCandle']=item['endCandle']+1

        self.mainChart.draw()

    def moveRight(self):
        #self.mainChart.endCandle = self.mainChart.endCandle - 1
        for item in self.mainChart.items:
            if item.get('endCandle')!=None:
               item['endCandle']=item['endCandle']-1
        self.mainChart.draw()

    def createPanes(self, gui):
        self.paneRight = tk.PanedWindow(gui.tab_chart, height="500", width="150", bg='green')
        self.paneRight.pack(fill='y', side='right', expand=True)
        self.paneLeft = tk.PanedWindow(gui.tab_chart, height="500", width="150", bg='Yellow')
        self.paneLeft.pack(fill='both', side='left', expand=True)

        self.paneLeft.bind("<Configure>", self.cucu)

    def cucu(self,event):
        # print(event.width,event.height)
        ResizingCanvas.pan2Height = event.height
        self.mycanvas2.update()
        self.mycanvas.update()

    def add(self):
        #res=np.array(self.gui.dbLite.getOneStock('T10'))
        rows = self.gui.dbLite.populateContract()
        for row in rows:
            self.listBox.insert(row[0],str(row[0])+'-'+row[2]+row[3])



class ResizingCanvas(tk.Canvas):
    pan2Height = 0

    def __init__(self, parent, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        # self.bind("<Key>",self.on_enter,"+")
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
        self.name = kwargs['name']
        print('name is ', self.name)

    def on_enter(self, event):
        print(event.char)

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width) / self.width
        hscale = float(event.height) / self.height
        self.width = event.width
        self.height = event.height
        # print(self.width,self.height)
        # resize the canvas

        if (self.name == '222'):
           # print('name 222 ',ResizingCanvas.pan2Height)
            self.height = int(ResizingCanvas.pan2Height * 0.8)
        else:
            self.height = int(ResizingCanvas.pan2Height * 0.2)
           # print('name 111 ', ResizingCanvas.pan2Height)

        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        #self.scale("cc", 0, 0, wscale, hscale)


class Chart:
    upcolor='green'
    downcolor='red'
    margin=20
    widthcandle=5
    spacecandle=3

    def draw_ema(self,ema):
        candle=self.get_candle('first')
        data=ema['data'][candle['beginCandle']:candle['endCandle']]
        #print(candle['beginCandle'],'---',candle['endCandle'],'here in draw data ',data)
        i=0
        for item in data[0:-1]:
            x1 = candle['margin'] + i * (candle['widthcandle'] + candle['spacecandle'])+candle['widthcandle'] / 2
            x2 = x1 + candle['widthcandle'] + candle['spacecandle']
            y1 = candle['scale'] * (candle['max'] - item) + candle['margin']
            y2 = candle['scale'] * (candle['max'] - data[i+1]) + candle['margin']
            self.canvas.create_line(x1, y1, x2, y2, fill=ema['color'],width=ema['width'])
            i=i+1

    def draw_minmax(self,minmax):
        candle=self.get_candle('first')
        print(candle['beginCandle'],'---',candle['endCandle'])
        i=0
        for x in range(candle['beginCandle'],candle['endCandle']):

            if(minmax['mindata'].get(x)!= None):
                x1 = candle['margin'] + i * (candle['widthcandle'] + candle['spacecandle']) + candle['widthcandle'] / 2
                y1 = candle['scale'] * (candle['max'] - minmax['mindata'].get(x)) + candle['margin']
                self.canvas.create_oval(x1-minmax['radius'], y1-minmax['radius'], x1+minmax['radius'],y1+minmax['radius'], fill=minmax['color'])

            if(minmax['maxdata'].get(x)!= None):
                x1 = candle['margin'] + i * (candle['widthcandle'] + candle['spacecandle']) + candle['widthcandle'] / 2
                y1 = candle['scale'] * (candle['max'] - minmax['maxdata'].get(x)) + candle['margin']
                self.canvas.create_oval(x1-minmax['radius'], y1-minmax['radius'], x1+minmax['radius'],y1+minmax['radius'], fill=minmax['color'])

            i=i+1

    def draw_grid(self,args):
        pass
    def draw_volume(self,args):
        pass
    def draw_line(self,args):
        pass




    def __init__(self,data,canvas:ResizingCanvas):
        self.data=data
        self.canvas=canvas
        #self.endCandle=len(data)#last candle
        #self.doMath()
        #self.items=[{'type':'candles','name':'firstcandle','data':'','upcolor':'blue'}]
        self.items=[]
        self.draw_jobs = {
            'candles': self.draw_candles,
            'ema'   : self.draw_ema,
            'grid'  : self.draw_grid,
            'volume': self.draw_volume,
            'lines'  : self.draw_line,
            'texts'  :self.draw_texts,
            'circles':self.draw_circles,
            'minmax':self.draw_minmax
        }

    def get_candle(self,name):
        for item in self.items:
            if (item.get('name')==name):
                return item
        return None

    def update_ema(self,ema):
        ema['type']='ema'
        x=np.array(self.data)
        #print(x[:,4])
        #return
        ema['data'] = talib.EMA(x[:,4].astype('float64'), timeperiod=ema['period'])
        return ema

    def update_minmax(self,minmax):
        minmax['type']='minmax'
        x = np.array(self.data)
        high = x[:,2]
        low = x[:,3]
        # print(high)
        period=minmax['period']

        count = len(x)
        min1 = {}
        max1 = {}
        if len(x) > period:
            i = period
            for item in high[period:-period]:
                a = high[i - period:i + period + 1]
                # print(a[period],max(a))
                if a[period] == max(a):
                    #max1.append([a[period], i])  # will append the value and the position
                    #better to use a dictionary
                    max1[i]=a[period].astype('float64')
                    #print(max1[i],i)
                i = i + 1
           # print('max----------------------------')
            i = period
            for item in low[period:-period]:
                a = low[i - period:i + period + 1]
                # print(a,a.index(max(a)))
                if a[period] == min(a):
                    #min1.append([a[period], i])  # will append the value and the position
                    #better to use a dictionary
                    min1[i]=a[period].astype('float64')
                  #  print(min1[i], i)
                i = i + 1

        #print(min1)
        #print(max1)
        minmax['mindata']=min1
        minmax['maxdata']=max1
        return minmax


    def update_candles(self, candle):
        candle['type']='candles'
        candle['upcolor']=Chart.upcolor if candle.get('upcolor') == None else candle.get('upcolor')
        candle['downcolor'] = Chart.downcolor if candle.get('downcolor') == None else candle.get('downcolor')
        candle['widthcandle'] = Chart.widthcandle if candle.get('widthcandle') == None else candle.get('widthcandle')
        candle['spacecandle'] = Chart.spacecandle if candle.get('spacecandle') == None else candle.get('spacecandle')
        candle['margin'] = Chart.margin if candle.get('margin') == None else candle.get('margin')
        candle['width'] = self.canvas.winfo_reqwidth() - (2 * candle['margin'])
        candle['height'] = self.canvas.winfo_reqheight() - (2 * candle['margin'])

        candle['countCandle'] = int(candle['width'] / (candle['widthcandle'] + candle['spacecandle']))
        candle['endCandle']=len(self.data) if candle.get('data') ==None else candle.get('endCandle')
        candle['beginCandle'] = candle['endCandle'] - candle['countCandle']

        candle['data']=self.data[candle['beginCandle']:candle['endCandle']]

        candle['max'] = max([row[2] for row in candle['data']])
        candle['min'] = min([row[3] for row in candle['data']])

        lowhigh = candle['max'] - candle['min']
        candle['scale'] = candle['height'] / lowhigh

        return candle


    def draw_texts(self,args):
        pass

    def draw_circles(self,args):
        pass

    def draw(self):
        self.canvas.delete("all")
        for item in self.items:
            self.draw_jobs[item['type']](item)

    def draw_candles(self,candle):
        #print(candle.get('endCandle'),candle.get('upcolor'),candle.get('upcolor'))
        self.update_candles(candle)

        #self.doMath()
        i=0
        for item in candle['data']:
            x1=candle['margin']+i*(candle['widthcandle']+candle['spacecandle'])
            x2=x1+candle['widthcandle']
            x3=x1+candle['widthcandle']/2
            if item[1]<item[4]:
                color = candle['upcolor'] if candle.get('upcolor')== None else candle.get('upcolor')
                y1=candle['scale']*(candle['max']-item[4])+candle['margin']
                y2 = candle['scale'] * (candle['max'] - item[1])+candle['margin']
            else:
                color = candle['downcolor']
                y1=candle['scale']*(candle['max']-item[1])+candle['margin']
                y2 = candle['scale'] * (candle['max'] - item[4])+candle['margin']

            y3 = candle['scale'] * (candle['max'] - item[2]) + candle['margin']
            y4 = candle['scale'] * (candle['max'] - item[3]) + candle['margin']

            self.canvas.create_rectangle(x1,y1,x2,y2,fill=color,width=0)
            self.canvas.create_line(x3,y3,x3,y4,fill=color)
            #self.canvas.create_line(x1+Chart.widthcandle/2,)

            if i%10==0:
                self.canvas.create_text(x1, candle['height']+candle['margin'], fill="darkblue", font="Times 10",
                                    text=item[0][10:])
                #print(item[0])
                self.canvas.create_line(x1,0,x1,candle['height'],fill="gray", dash=(4,10))
            i=i+1

        #display on Y (vertical)
        #getcontext().prec = 3
        step=(candle['max']-candle['min'])/10
        for i in range(10):
            self.canvas.create_text(20, (i* step)*candle['scale'] + candle['margin'], fill="darkblue", font="Times 10",
                                   # text=str(self.max-i*step))
                                    text="{:10.2f}".format(candle['max']-i*step))
            self.canvas.create_line(30, (i* step)*candle['scale'], candle['width'], (i* step)*candle['scale'], fill="gray", dash=(4, 10))


    '''
        def draw_candles(self,candle):
        print(candle['name'],candle['upcolor'],candle.get('upcolor2'))
        self.canvas.delete("all")
        #self.doMath()
        i=0
        for item in self.data[self.beginCandle:self.endCandle]:
            x1=Chart.margin+i*(Chart.widthcandle+Chart.spacecandle)
            x2=x1+Chart.widthcandle
            x3=x1+Chart.widthcandle/2
            if item[1]<item[4]:
                color = Chart.upcolor if args.get('upcolor')== None else args.get('upcolor')
                y1=self.scale*(self.max-item[4])+Chart.margin
                y2 = self.scale * (self.max - item[1])+Chart.margin
            else:
                color = Chart.downcolor
                y1=self.scale*(self.max-item[1])+Chart.margin
                y2 = self.scale * (self.max - item[4])+Chart.margin

            y3 = self.scale * (self.max - item[2]) + Chart.margin
            y4 = self.scale * (self.max - item[3]) + Chart.margin

            self.canvas.create_rectangle(x1,y1,x2,y2,fill=color,width=0)
            self.canvas.create_line(x3,y3,x3,y4,fill=color)
            #self.canvas.create_line(x1+Chart.widthcandle/2,)

            if i%10==0:
                self.canvas.create_text(x1, self.height+Chart.margin, fill="darkblue", font="Times 10",
                                    text=item[0][10:])
                #print(item[0])
                self.canvas.create_line(x1,0,x1,self.height,fill="gray", dash=(4,10))
            i=i+1

        #display on Y (vertical)
        getcontext().prec = 3
        step=(self.max-self.min)/10
        for i in range(10):
            self.canvas.create_text(20, (i* step)*self.scale + Chart.margin, fill="darkblue", font="Times 10",
                                   # text=str(self.max-i*step))
                                    text="{:10.2f}".format(self.max-i*step))
            self.canvas.create_line(30, (i* step)*self.scale, self.width, (i* step)*self.scale, fill="gray", dash=(4, 10))
            '''

    def doMath(self):
        self.width=self.canvas.winfo_reqwidth()-(2*Chart.margin)
        self.height=self.canvas.winfo_reqheight()-(2*Chart.margin)
        self.countCandle=int(self.width/(Chart.widthcandle+Chart.spacecandle))
        self.beginCandle = self.endCandle - self.countCandle
        #print(self.data[self.beginCandle:self.endCandle])
        #print(self.data[self.endCandle-5:])
        print(self.beginCandle,self.endCandle)

        self.max=max([row[2] for row in self.data[self.beginCandle:self.endCandle]])
        self.min=min([row[3] for row in self.data[self.beginCandle:self.endCandle]])

        self.lowhigh=self.max-self.min
        self.scale=self.height/self.lowhigh


# mycanvas2.grid(row=2, column=1)


# mycanvas.place(x=10, y=10)

# add some widgets to the canvas
# mycanvas.create_line(0, 0, 200, 100)
# mycanvas.create_line(0, 100, 200, 0, fill="white", dash=(4, 4))



# tag all of the drawn widgets
# mycanvas.addtag_all("all")

#return
'''
paneChart1 = tk.PanedWindow(self.tab_chart, height="500", width="500", bg='red')
# paneChart1 = tk.PanedWindow(self.tab_chart, height="500", bg='red')
# paneChart1.place(x=10, y=10)
paneChart1.pack(side='left', expand=True)

paneChart2 = tk.PanedWindow(self.tab_chart, height="500", width="70", bg='blue')
# paneChart2.place(x=530, y=10)
paneChart2.pack(side='right', expand=True)

# frame1=tk.Frame(self.tab_chart,bg='black',height="500", width="70")
# frame1.place(x=530, y=10)
# self.qqq = tk.Button(paneChart2, text="HistOld", command=self.histold)
# self.qqq.pack(side='left')

# c=tk.Canvas(paneChart1, height="300",width="300",bg="yellow")
c = tk.Canvas(paneChart1, height="100", width="600", bg="yellow")
c2 = tk.Canvas(paneChart2, height="400", width="600", bg="red")
# c.pack(side="top", expand=False, fill='both')
# c2.pack(side="bottom", expand=True, fill='both')

# c.place(x=10,y=10)

# line=c.create_line(5,5,400,100,width=10)
'''