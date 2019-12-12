import wx
from PIL import Image
from queue import Queue

# Basic settings
ZERO, ONE, UNKNOWN, ERROR = (0, 1, 2, 3)
INPUT, OUTPUT, ANDGATE, NOTGATE = (0, 1, 2, 3)
NONE, MOVEPIC, DRAWING = (0, 1, 2) # none, moving pic, drawing
inputsNum = [0, 1, 2, 1]
offset = 36
# Move from toolbar
gateSelected = [False for i in range(0, 4)] # 本图标是否在被（从工具栏）移动
gateNum = [0 for i in range(0, 4)]
gates = [[(-1, 0, (-1, -1)) for i in range(0, 1000)] for j in range(0, 4)] # (ID, state (pos.x, pos.y)) state: layed 1, else 0
gateRectangle = [(-1, -1, -1, -1) for i in range(0, 1000)]
# Grid
gridGap = 14
gridWid, gridHeight, gridWGap, gridHGap = (50, 50, gridGap - 1, gridGap)
pointState = [[0 for i in range(0,gridWid)] for j in range(0, gridHeight)]
# States
gateInputs = [[(-1, (-1, -1))for i in range(0, 32)]for j in range(0, 1000)] # ID对应各个input值及其网格坐标 (inputValue, (x, y))
gateOutput = [(2, (-1, -1)) for i in range(0, 1000)]
# Colors
ZEROCOL, ONECOL, UNKNOWNCOL, ERRORCOL =  ("rgb(0,100,0)", "rgb(0,210,0)", "rgb(40,40,255)", "rgb(192,0,0)")

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(None, -1, title='Logisimal', size=(gridGap * gridWid, gridGap * gridHeight), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
        self.SetBackgroundColour("white");self.pen = wx.Pen("black", 6, wx.SOLID);self.brush = wx.Brush('', wx.TRANSPARENT)  #透明填充
        self.InitBuffer()
        self.initGrid();self.createStatusBar();self.createMenuBar();self.createToolBar()
        self.totID = 30 # ID from 30 (gates[i][j])
        self.state = NONE
        self.lines = []
        self.p1 = self.p2 = (-1, -1); self.direction = 0 # p1,p2,画线弯折方向
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.OnMove)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Show(True)
        self.movingIndex = (-1, -1) # i, j

    #initialize window

    def InitBuffer(self):
        size = self.GetClientSize()
        self.buffer = wx.Bitmap(size.width, size.height)
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.reInitBuffer = False
    
    def initGrid(self):
        grid_sizer = wx.GridSizer(gridHeight, gridWid, gridHGap, gridWGap)
        for i in range(gridHeight * gridWid): 
            panel = wx.Panel(self)
            panel.SetMinSize((1,1))
            panel.SetBackgroundColour("gray")
            grid_sizer.Add(panel)
        self.SetSizer(grid_sizer)
        self.Fit()

    def createStatusBar(self):self.CreateStatusBar()

    def createMenuBar(self):
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)
        filemenu = wx.Menu()
        menuAbout = filemenu.Append(wx.ID_ABOUT, 'About', 'About Logisim')
        menuExit = filemenu.Append(wx.ID_EXIT, 'Exit', 'Exit the program')
        filemenu.AppendSeparator()
        menuBar.Append(filemenu, 'File')
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
    
    def createToolBar(self):
        tb = wx.ToolBar(self, wx.ID_ANY)  # 创建工具栏对象
        self.ToolBar = tb  # 将此工具栏对象放入当前窗口
        tsize = (30, 30)
        inputtool = tb.AddTool(24, 'input', wx.Bitmap('images\\input.bmp'), 'input button'); self.Bind(wx.EVT_TOOL, self.inputOnClick, inputtool)
        outputtool = tb.AddTool(25, "output", wx.Bitmap("images\\output.bmp"), "output button"); self.Bind(wx.EVT_TOOL, self.outputOnClick, outputtool)
        andgate = tb.AddTool(26, "AND", wx.Bitmap("images\\ANDgate.bmp"), "AND gate"); self.Bind(wx.EVT_TOOL, self.andOnClick, andgate)
        notgate = tb.AddTool(27, "NOT", wx.Bitmap("images\\NOTgate.bmp"), "NOT gate"); self.Bind(wx.EVT_TOOL, self.notOnClick, notgate)
        tb.Realize()

    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "Logisim is good", "About Logisim")
        dlg.ShowModal(); dlg.Destroy()

    def OnExit(self, event): self.Close(True)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)
    
    def getColor(self, state):
        if state == ZERO: return ZEROCOL
        elif state == ONE: return ONECOL
        elif state == UNKNOWN: return UNKNOWNCOL
        else: return ERRORCOL 

    # drawing
    def drawInOutGate(self, dc, pos, state, outputState, isInput):
        (x, y) = pos
        brush = wx.Brush('', wx.TRANSPARENT) 
        if state == 0: 
            pen = wx.Pen("GREY", 4, wx.SOLID)
            dc.SetPen(pen)
            dc.SetBrush(brush)
            if isInput: dc.DrawRectangle(x, y, 2 * gridGap, 2 * gridGap)
            else: dc.DrawCircle(x + gridGap, y + gridGap, gridGap)
        else: 
            pen = wx.Pen("BLACK", 4, wx.SOLID)
            dc.SetPen(pen)
            dc.SetBrush(brush)
            if isInput: dc.DrawRectangle(x, y, 2 * gridGap, 2 * gridGap)
            else: dc.DrawCircle(x + gridGap, y + gridGap, gridGap)
            color = self.getColor(outputState)
            dc.SetPen(wx.Pen(color, 1, wx.SOLID))
            dc.SetBrush(wx.Brush(color, wx.BRUSHSTYLE_SOLID))
            if isInput: dc.DrawCircle(x + gridGap - 1, y + gridGap - 1, gridGap * 2 // 3)
            else: dc.DrawCircle(x + gridGap, y + gridGap, gridGap * 2 // 3)

    def drawAndGate(self, dc, pos, state, outputState):
        (x, y) = pos
        if state == 0: dc.SetPen(wx.Pen("GREY", 4, wx.SOLID))
        else: dc.SetPen(wx.Pen("BLACK", 4, wx.SOLID))
        dc.SetBrush(wx.Brush('', wx.TRANSPARENT))
        dc.DrawLine(x, y + gridGap // 2, x, y + gridGap * 7 // 2) #vertical
        dc.DrawLine(x, y + gridGap // 2, x + gridGap * 3 // 2, y + gridGap // 2) #horizontal up
        dc.DrawLine(x, y + gridGap * 7 // 2, x + gridGap * 3 // 2, y + gridGap * 7 // 2) #horizontal down
        dc.DrawArc(x + gridGap * 3 // 2, y + gridGap * 7 // 2, x + gridGap * 3 // 2, y + gridGap // 2, x + gridGap * 3 // 2, y + gridGap * 2)
        
    def drawNotGate(self, dc, pos, state, outputState):
        (x, y) = pos
        if state == 0: dc.SetPen(wx.Pen("GREY", 4, wx.SOLID))
        else: dc.SetPen(wx.Pen("BLACK", 4, wx.SOLID))
        dc.SetBrush(wx.Brush('', wx.TRANSPARENT))
        points = [(0, gridGap // 3), (0, gridGap * 5 // 3), (gridGap * 2, gridGap)]
        dc.DrawPolygon(points, x, y)
        dc.DrawCircle(x + gridGap * 5 // 2, y + gridGap, gridGap // 2)

    # about mouse event
    def getNearPosition(self,pos):
        lu = (pos[0] // gridGap * gridGap, pos[1] // gridGap * gridGap)
        ru = (lu[0] + gridGap, lu[1])
        ld = (lu[0], lu[1] + gridGap)
        rd = (lu[0] + gridGap, lu[1] + gridGap)
        if abs(lu[0] - pos[0]) <= gridGap // 2 and abs(lu[1] - pos[1]) <= gridGap // 2: return lu
        if abs(ru[0] - pos[0]) <= gridGap // 2 and abs(ru[1] - pos[1]) <= gridGap // 2: return ru
        if abs(ld[0] - pos[0]) <= gridGap // 2 and abs(ld[1] - pos[1]) <= gridGap // 2: return ld
        if abs(rd[0] - pos[0]) <= gridGap // 2 and abs(rd[1] - pos[1]) <= gridGap // 2: return rd
        assert(False)
 
    def pointToIndex(self, point):# only used to calculate mouseevent point
        return (point[0] // gridGap, (point[1] - offset) // gridGap)

    def indexToPoint(self, point):
        return (point[0] * gridGap, point[1] * gridGap + offset)
    
    def pointInRectangle(self, point, rectangle):
        (x1, y1, x2, y2) = rectangle
        index = self.pointToIndex(point)
        if index[0] > x1 and index[0] < x2 and index[1] > y1 and index[1] < y2: return True
        return False
    
    def pointInCircle(self, point, x, y, r):
        (tx, ty) = point
        return (tx - x) * (tx - x) + (ty - y) * (ty - y) <= r * r

    def addLines(self):
        count = 2
        notfound = True # p1 = x
        pos = (-1, -1) #pos->pos2 include p1
        for (P1, P2, State) in self.lines:
            if notfound == False: break
            if P1 == self.p1 or P2 == self.p1: notfound = False
            elif (P1[0] == self.p1[0] and P2[0] == self.p1[0] and (P1[1] - self.p1[1]) * (P2[1] - self.p1[1]) < 0) or (P1[1] == self.p1[1] and P2[1] == self.p1[1]  and (P1[0] - self.p1[0]) * (P2[0] - self.p1[0]) < 0):
                pos = P1 #P1,self.p1,P2
        if notfound and pos != (-1, -1):# gate->(-1,-1)
            self.lines.append((self.p1, pos, UNKNOWN))
            count = count + 1
        
        if self.direction == 0:
            self.lines.append((self.p1, (self.p1[0], self.p2[1]), UNKNOWN))
            if self.p2 != (self.p1[0], self.p2[1]): self.lines.append(((self.p1[0], self.p2[1]), self.p2, UNKNOWN))
            else: count = count - 1
        else :
            self.lines.append((self.p1, (self.p2[0], self.p1[1]), UNKNOWN))
            if (self.p2[0], self.p1[1]) != self.p2: self.lines.append(((self.p2[0], self.p1[1]), self.p2, UNKNOWN))
            else: count = count - 1
        return count

    def delLines(self, count):
        for i in range(0, count):
            self.lines.pop()

    def OnLeftDown(self, event):
        # lay gate
        pos = self.getNearPosition(event.GetPosition())
        pos = (pos[0], pos[1] + offset)
        for i in range(0, 4):
            if gateSelected[i]:
                gateSelected[i] = False
                gates[i][gateNum[i]] = (self.totID, 1, pos)
                self.state = NONE
                self.Draw(event)
                self.totID = self.totID + 1
                return 
        
        # choose a gate to move
        for i in range(0, 4):
            for j in range(0, gateNum[i]):
                if gates[i][j][1] == -1: continue
                if self.pointInRectangle(pos, gateRectangle[gates[i][j][0]]):
                    self.movingIndex = (i, j)
                    gates[i][j] = (gates[i][j][0], 0,gates[i][j][2])
                    return

        # draw a line, if not points then return
        # judge if a point can be choosed
        self.p1 = self.getNearPosition(event.GetPosition())
        self.p1 = (self.p1[0] ,self.p1[1] + offset)
        (x, y) = self.pointToIndex(self.p1)
        if(pointState[x][y] == 0): return
        self.state = DRAWING
        self.Draw(event)

    def gateInputsEnough(self, ID, kind):
        for i in range(0, inputsNum[kind]):
            if gateInputs[ID][i][0] == 2:
                return False
        return True
    
    def OnMove(self, event):
        # draw blur image
        position = self.getNearPosition(event.GetPosition())
        position = (position[0], position[1] + offset)
        if((position[0] >= 0 and position[0] <= gridGap * gridWid and position[1] >= 0 and position[1] <= gridGap * gridHeight) == False):return
        if self.movingIndex != (-1, -1):
            gates[self.movingIndex[0]][self.movingIndex[1]] = (gates[self.movingIndex[0]][self.movingIndex[1]][0], 0, position) #setPos

        #drawing line
        self.p2 = self.getNearPosition(event.GetPosition())
        self.SetStatusText("x:"+str(event.GetPosition().x)+", y:"+str(event.GetPosition().y)+"; "+str(self.p2))
        self.p2 = (self.p2[0] ,self.p2[1] + offset)
        if (self.state != DRAWING) or (event.LeftIsDown() == False):
            self.Draw(event)
            return
        if self.p2[1] == self.p1[1]: self.direction = 1 # same line
        if self.p1[0] == self.p2[0]: self.direction = 0 # same column
        count = self.addLines() 
        self.Draw(event)
        self.delLines(count) # delete temporary lines
        event.Skip()
        
    def OnLeftUp(self, event):
        if self.movingIndex != (-1, -1):
            gates[self.movingIndex[0]][self.movingIndex[1]] = (gates[self.movingIndex[0]][self.movingIndex[1]][0], 1, gates[self.movingIndex[0]][self.movingIndex[1]][2])
            self.movingIndex = (-1, -1)
            self.Draw(event)
            return
        if self.p1 == self.p2 or self.state != DRAWING: return
        self.state = NONE
        self.addLines()
        self.Draw(event)

    def OnRightDown(self, event):
        if self.movingIndex != (-1, -1): #删除
            gates[self.movingIndex[0]][self.movingIndex[1]] = (gates[self.movingIndex[0]][self.movingIndex[1]][0], -1, gates[self.movingIndex[0]][self.movingIndex[1]][2])
            if self.movingIndex[1] == gateNum[self.movingIndex[0]] - 1: #删除的下标为最大下标
                gateNum[self.movingIndex[0]] = gateNum[self.movingIndex[0]] - 1
            self.movingIndex = (-1, -1)
            self.Draw(event)
            return
        for i in range(0, gateNum[0]):
            pos = self.getNearPosition(event.GetPosition())
            pos = (pos[0], pos[1] + offset)
            if self.pointInRectangle(pos, gateRectangle[gates[0][i][0]]):
                gateOutput[gates[0][i][0]] = (gateOutput[gates[0][i][0]][0] ^ 1, gateOutput[gates[0][i][0]][1])
        for i in range(0, 4): gateSelected[i] = False
        self.Draw(event)
        event.Skip()

    def Draw(self, event):
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.SetPen(self.pen)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.SetBrush(self.brush)
        dc.Clear()
        queue = Queue(maxsize = 0)
        #initialize for drawing
        for i in range(1, 4): # not initialize input gate
            for j in range(0, gateNum[i]):
                ID = gates[i][j][0]
                gateInputs[ID][0] = (2, gateInputs[ID][0][1])
                gateInputs[ID][1] = (2, gateInputs[ID][1][1])
                gateOutput[ID] = (2, gateOutput[ID][1])
        for (index, (p1, p2, state)) in enumerate(self.lines):
            self.lines[index] = (p1, p2, 2)
        #initialize for points
        for i in range(0, gridWid):
            for j in range(0,gridHeight):
                pointState[j][i] = 0
        for i in range(0, 4):
            for j in range(0, gateNum[i]):
                ID = gates[i][j][0]
                (x, y) = self.pointToIndex(gates[i][j][2])
                if gates[i][j][1] == -1: continue
                if i == INPUT: 
                    pointState[x + 2][y + 1] = 1                # input gate
                    if gateOutput[ID][0] == UNKNOWN: gateOutput[ID] = (0, (x + 2, y + 1))
                    else: gateOutput[ID] = (gateOutput[ID][0], (x + 2, y + 1))
                    gateRectangle[ID] = (x, y, x + 2, y + 2)
                elif i == OUTPUT: 
                    pointState[x][y + 1] = 1; 
                    gateInputs[ID][0] = (2, (x, y + 1)) # output gate
                    gateRectangle[ID] = (x, y, x + 2, y + 2)
                elif i == ANDGATE: 
                    pointState[x][y + 1] = pointState[x][y + 3] = pointState[x + 3][y + 2] = 1
                    gateInputs[ID][0] = (2, (x, y + 1)); gateInputs[ID][1] = (2, (x, y + 3))  # and gate
                    gateOutput[ID] = (2, (x + 3, y + 2))
                    gateRectangle[ID] = (x, y, x + 3, y + 3)
                elif i == NOTGATE:
                    pointState[x][y + 1] = pointState[x + 3][y + 1] = 1  # not gate
                    gateInputs[ID][0] = (2, (x, y + 1))
                    gateOutput[ID] = (2, (x + 3, y + 1))
                    gateRectangle[ID] = (x, y, x + 3, y + 2)
        for (p1, p2, state) in self.lines:
            p1 = self.pointToIndex(p1)
            p2 = self.pointToIndex(p2)
            if p1[0] == p2[0]: 
                if p1[1] < p2[1]:
                    for i in range(p1[1], p2[1] + 1): pointState[p1[0]][i] = 1
                else:
                    for i in range(p2[1], p1[1] + 1): pointState[p2[0]][i] = 1
            else: 
                if p1[0] < p2[0]:
                    for i in range(p1[0], p2[0] + 1): pointState[i][p1[1]] = 1
                else:
                    for i in range(p2[0], p1[0] + 1): pointState[i][p2[1]] = 1
        (x, y) = self.getNearPosition(event.GetPosition())
        if self.state == NONE and pointState[x // gridGap][y // gridGap] == 1 and self.pointInCircle(event.GetPosition(), x, y, gridGap // 2):
            dc.SetPen(wx.Pen(ONECOL, 4, wx.SOLID))
            dc.SetBrush(self.brush)
            dc.DrawCircle(x, y + offset, gridGap // 2)
        #bfs
        for j in range(0, gateNum[0]):
            ID = gates[0][j][0]
            if gates[0][j][1] == 1:
                queue.put((gateOutput[ID]))
        while not queue.empty():
            tup = queue.get()
            for i in range(0, 4):
                for j in range(0, gateNum[i]):
                    ID = gates[i][j][0]
                    for k in range(0, inputsNum[i]):
                        if gateInputs[ID][k][1] == tup[1]: # pos same
                            if gateInputs[ID][k][0] != UNKNOWN:
                                if gateInputs[ID][k][0] != tup[0]:
                                    gateInputs[ID][k] = (ERROR, gateInputs[ID][k][1])
                                else:
                                    continue
                            gateInputs[ID][k] = (tup[0], gateInputs[ID][k][1])
                            if self.gateInputsEnough(ID, i):
                                if i == OUTPUT: gateOutput[ID] = (tup[0], gateOutput[ID][1])
                                elif i == ANDGATE: gateOutput[ID] = (gateInputs[ID][0][0]&gateInputs[ID][1][0], gateOutput[ID][1])
                                elif i == NOTGATE: 
                                    NOTtup = tup[0]
                                    if tup[0] == 0: NOTtup = 1
                                    elif tup[0] == 1: NOTtup = 0
                                    gateOutput[ID] = (NOTtup, gateOutput[ID][1])
                                if i != OUTPUT: queue.put((gateOutput[ID]))

            for (index, line) in enumerate(self.lines):
                (p1, p2, state) = line
                p1 = self.pointToIndex(p1)
                p2 = self.pointToIndex(p2)
                if state == tup[0] or (p1 != tup[1] and p2 != tup[1]):
                    continue
                if state != tup[0] and state != UNKNOWN:
                    self.lines[index] = (line[0], line[1], ERROR)
                    if p1 == tup[1]: queue.put((ERROR, p2))
                    else: queue.put((ERROR, p1))
                elif p1 == tup[1]:
                    self.lines[index] = (line[0], line[1], tup[0])
                    queue.put((tup[0], p2))
                elif p2 == tup[1]:
                    self.lines[index] = (line[0], line[1], tup[0])
                    queue.put((tup[0], p1))
        #drawing
        for i in range(0, 4):
            for j in range(0,gateNum[i]):
                ID = gates[i][j][0]
                if gates[i][j][1] == -1: continue
                if i == INPUT or i == OUTPUT: self.drawInOutGate(dc, gates[i][j][2], gates[i][j][1], gateOutput[ID][0], i == INPUT)
                elif i == ANDGATE: self.drawAndGate(dc, gates[i][j][2], gates[i][j][1], gateOutput[ID][0])
                else: self.drawNotGate(dc, gates[i][j][2], gates[i][j][1], gateOutput[ID][0])
        for (x1, y1),(x2, y2),state in self.lines:
            if state == ZERO:
                self.pen = wx.Pen(ZEROCOL, 6, wx.SOLID)
            elif state == ONE:
                self.pen = wx.Pen(ONECOL, 6, wx.SOLID)
            elif state == UNKNOWN:
                self.pen = wx.Pen(UNKNOWNCOL, 6, wx.SOLID)
            else:
                self.pen = wx.Pen(ERRORCOL, 6, wx.SOLID)
            dc.SetPen(self.pen)
            dc.DrawLine(x1, y1, x2, y2)

    def select(self, x):
        self.state = MOVEPIC
        for i in range(0, 4): 
            if gateSelected[i] == True:
                gateNum[i] = gateNum[i] - 1
                gateSelected[i] = False
        gateSelected[x] = True
        self.movingIndex = (x, gateNum[x])
        gates[x][gateNum[x]] = (self.totID, 0, (-5, -5))
        gateNum[x] = gateNum[x] + 1

    def inputOnClick(self, event): self.select(0)
    def outputOnClick(self, event): self.select(1)
    def andOnClick(self, event): self.select(2)
    def notOnClick(self, event): self.select(3)


app = wx.App(False)
frame = MainWindow(None, title="Logisimal")
frame.Show()
app.MainLoop()