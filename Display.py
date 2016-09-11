import Tkinter as tk
from Analysis import Analysis
scaleDistances = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 40, 50, 100, 150, 200, 250, 300, 400, 500, 1000,
                  2000, 3000, 4000, 5000, 10000, 15000, 20000, 25000, 30000, 40000, 50000, 100000, 150000,
                  200000, 250000, 300000, 400000, 500000, 1000000, 1500000, 2000000, 2500000, 3000000,
                  4000000, 5000000, 10000000, 15000000, 20000000, 25000000, 30000000, 40000000, 50000000,
                  1000000000, 150000000, 200000000, 250000000, 300000000, 400000000, 500000000, 10000000000]
class Display():
    def __init__(self, master, windowHeight, windowWidth, winX, winY):
        self.master = master
        self.waveform = tk.Canvas(master.window, width = windowWidth, height = windowHeight, highlightthickness = 0, bg = 'gray95')
        self.waveform.grid(row = winY+1, column = winX)
        self.coords = (winX+1, winY+1)
        self.values = [0, 0]
        self.start = 0
        self.hPoints, self.hLines, self.hLinesRaw, self.overlays = list(), list(), list(), list()
        self.secondarySelected = False
        self.selected = False
        self.zooming = False
        self.isDragging = False
        self.unBlocked = False
        self.data = ['', 0, [0, 0], 0, '']
        self.setDimensions(windowWidth, windowHeight)
        self.setKeyBindings()

    """
    sets all initial key bindings for displays
    """
    def setKeyBindings(self):
        self.waveform.bind('<Button-1>', self.selectWidget)
        self.waveform.bind('<ButtonRelease-1>', self.waveDragEnd)
        self.waveform.bind('<Button-3>', self.secondarySelectWidget)
        self.waveform.bind('<Control-v>', lambda e:self.paste())
        self.waveform.bind('<Delete>', lambda e:self.clearValues())
        self.waveform.bind('<Control-g>', self.master.switchGrid)
        self.waveform.bind('<Control-e>', self.master.switchExtrema)
        self.waveform.bind('<Control-d>', lambda e: self.master.openDatabaseChange())
        self.waveform.bind('<Up>', self.moveUp)
        self.waveform.bind('<Left>', self.moveLeft)
        self.waveform.bind('<Down>', self.moveDown)
        self.waveform.bind('<Right>', self.moveRight)
        self.waveform.bind('<Control-Up>', self.moveSecondUp)
        self.waveform.bind('<Control-Left>', self.moveSecondLeft)
        self.waveform.bind('<Control-Down>', self.moveSecondDown)
        self.waveform.bind('<Control-Right>', self.moveSecondRight)
        self.waveform.bind('<Control-z>', lambda e: self.master.undoAction())
        self.waveform.bind('<Control-y>', lambda e: self.master.redoAction())
        self.waveform.bind('<F11>', lambda e: self.master.toggleFullscreen())
        self.waveform.bind('<MouseWheel>', self.master.hoverZoom)
        self.waveform.bind('<Escape>', lambda e: self.master.window.destroy())
        self.waveform.bind('<Enter>', lambda e: self.master.setHover(self.coords))
        self.waveform.bind('<Leave>', self.cover)

    """
    changes the zoom level
    triggered on <mousewheel>
    """
    def zoomDelta(self, delta):
        if len(self.values)>2:
            x, y = self.waveform.winfo_pointerx()-self.waveform.winfo_rootx(), self.waveform.winfo_pointery()-self.waveform.winfo_rooty()
            mouseX = (x-90)/self.scalingFactor[0]
            mouseY = (self.dimensions[1]-60-y)/self.scalingFactor[1]
            if x>90 and x<self.waveform.winfo_width() and y>0 and y<self.waveform.winfo_height()-60 and self.unBlocked:
                if delta == 120 and self.zoomLevel < round(pow(len(self.values), .5)):
                    self.zoomLevel += 1
                    self.bL[0] += mouseX/(self.zoomLevel)
                    self.bL[1] += mouseY/(self.zoomLevel)
                elif delta == -120 and self.zoomLevel > 1:
                    self.zoomLevel -= 1
                    self.bL[0] -= mouseX/(self.zoomLevel)
                    self.bL[1] -= mouseY/(self.zoomLevel)
                self.testBounds()
                self.updateWaveform()
    """
    Starts the map dragging by setting initial coordinates
    triggered on <Button-1>(primary mouse button is depressed)
    """
    def waveDragStart(self, x, y):
        mouseX = (x-90)/self.scalingFactor[0]
        mouseY = (self.dimensions[1]-60-y)/self.scalingFactor[1]
        self.dragCoords = [mouseX, mouseY]
        self.isDragging = True
    
    """
    Changes the positions of the graph relative to the viewer
    Executes while Button-1 is pressed
    """
    def waveDragMoving(self, x, y):
        mouseX = (x-90)/self.scalingFactor[0]
        mouseY = (self.dimensions[1]-60-y)/self.scalingFactor[1]
        deltaX = self.dragCoords[0] - mouseX
        deltaY = self.dragCoords[1] - mouseY
        self.bL[0] += deltaX
        self.bL[1] += deltaY
        self.dragCoords = [mouseX, mouseY]
        self.testBounds()
        self.updateWaveform()
    
    """
    Ends the map dragging
    triggered on <ButtonRelease-1>(primary mouse button is released)
    """
    def waveDragEnd(self, event):
        self.isDragging = False

    """
    Checks whether the viewing screen is within the bounds of the graph and rectifies it if it isn't
    executes when dragging the map or zooming
    """
    def testBounds(self):
            if self.bL[0] < 0:
                self.bL[0] = 0
            elif self.bL[0]+len(self.values)/self.zoomLevel > len(self.values):
                self.bL[0] = len(self.values)-len(self.values)/self.zoomLevel
            if self.bL[1] < 0:
                self.bL[1] = 0
            elif self.bL[1]+self.graphHeight/self.zoomLevel> self.graphHeight:
                self.bL[1] = self.graphHeight-self.graphHeight/self.zoomLevel

    """
    Selects this screen as the primary screen
    Selection denoted by a hollow black circle
    The primary screen receives waveform changes, and sends filter data and overlay transfers
    The primary screen sends cut, copied, and deleted data, and receives pasted data
    triggered on <Button-1>
    """
    def selectWidget(self, event):
        if len(self.values) > 2:
            self.waveDragStart(event.x, event.y)
        self.master.screen[self.master.focused[0]-1][self.master.focused[1]-1].selected = False
        self.master.screen[self.master.focused[0]-1][self.master.focused[1]-1].updateWaveform()
        self.master.focused = list(self.coords)
        self.master.updateEditMenu()
        self.waveform.focus_set()
        self.selected = True
        self.updateWaveform()

    """
    moves the primary screen selection up
    triggered on <Up>
    """
    def moveUp(self, event):
        if self.coords[1] != 1:
            self.master.screen[self.coords[0]-1][self.coords[1]-2].selectWidget(event)
            self.selected = False
            self.updateWaveform()

    """
    moves the primary screen selection left
    triggered on <Left>
    """
    def moveLeft(self, event):
        if self.coords[0] != 1:
            self.master.screen[self.coords[0]-2][self.coords[1]-1].selectWidget(event)
            self.selected = False
            self.updateWaveform()

    """
    moves the screen selection down
    triggered on <Down>
    """
    def moveDown(self, event):
        if self.coords[1] != len(self.master.screen[0]):
            self.master.screen[self.coords[0]-1][self.coords[1]].selectWidget(event)
            self.selected = False
            self.updateWaveform()

    """
    moves the screen selection right
    triggered on <right>
    """
    def moveRight(self, event):
        if self.coords[0] != len(self.master.screen):
            self.master.screen[self.coords[0]][self.coords[1]-1].selectWidget(event)
            self.selected = False
            self.updateWaveform()

    """
    Selects this screen as the secondary screen
    Selection denoted by a solid red circle
    The secondary screen receives filters and overlay transfers
    triggered on <Button-3>(Secondary mouse button depressed)
    """
    def secondarySelectWidget(self, event):
        self.master.screen[self.master.secondaryFocused[0]-1][self.master.secondaryFocused[1]-1].secondarySelected = False
        self.master.screen[self.master.secondaryFocused[0]-1][self.master.secondaryFocused[1]-1].updateWaveform()
        self.secondarySelected = True
        self.master.secondaryFocused = list(self.coords)
        self.updateWaveform()

    """
    moves the secondary screen selection up
    triggered on <Control-Up>
    """
    def moveSecondUp(self, event):
        x, y = self.master.secondaryFocused[0], self.master.secondaryFocused[1]
        if y != 1:
            self.master.secondaryFocused = [x, y-1]
            self.master.screen[x-1][y-2].secondarySelected = True
            self.master.screen[x-1][y-1].secondarySelected = False
            self.master.screen[x-1][y-2].updateWaveform()
            self.master.screen[x-1][y-1].updateWaveform()

    """
    moves the secondary screen selection left
    triggered on <Control-Left>
    """
    def moveSecondLeft(self, event):
        x, y = self.master.secondaryFocused[0], self.master.secondaryFocused[1]
        if x != 1:
            self.master.secondaryFocused = [x-1, y]
            self.master.screen[x-2][y-1].secondarySelected = True
            self.master.screen[x-1][y-1].secondarySelected = False
            self.master.screen[x-2][y-1].updateWaveform()
            self.master.screen[x-1][y-1].updateWaveform()

    """
    moves the secondary screen selection down
    triggered on <Control-Down>
    """
    def moveSecondDown(self, event):
        x, y = self.master.secondaryFocused[0], self.master.secondaryFocused[1]
        if y != len(self.master.screen[0]):
            self.master.secondaryFocused = [x, y+1]
            self.master.screen[x-1][y].secondarySelected = True
            self.master.screen[x-1][y-1].secondarySelected = False
            self.master.screen[x-1][y].updateWaveform()
            self.master.screen[x-1][y-1].updateWaveform()

    """
    moves the secondary screen selection right
    triggered on <Control-Right>
    """
    def moveSecondRight(self, event):
        x, y = self.master.secondaryFocused[0], self.master.secondaryFocused[1]
        if x != len(self.master.screen):
            self.master.secondaryFocused = [x+1, y]
            self.master.screen[x][y-1].secondarySelected = True
            self.master.screen[x-1][y-1].secondarySelected = False
            self.master.screen[x][y-1].updateWaveform()
            self.master.screen[x-1][y-1].updateWaveform()

    """
    Copies the waveform data from the selected waveform onto the clipboard
    triggered on <Control-c>
    """
    def copy(self):
        self.master.clipboard = self.data

    """
    Pastes the saved waveform data from the clipboard onto the selected display
    triggered on <Control-v>
    """
    def paste(self):
        oldData = list(self.data)
        oldAdditions = [self.overlays, self.hPoints, self.hLinesRaw]
        self.updateWaveformData(self.master.clipboard)
        newAdditions = [self.overlays, self.hPoints, self.hLinesRaw]
        self.master.appendAction([[self.coords[0]-1, self.coords[1]-1], self.data, oldData, newAdditions, oldAdditions])
        self.master.updateEditMenu()

    """
    Copies the waveform data from the selected waveform onto the clipboard
    Deletes the selected waveform
    triggered on <Control-x>
    """
    def cut(self):
        self.master.clipboard = self.data
        self.values = list()
        self.updateWaveform()
        self.waveform.bind('<Control-f>', lambda e: None)
        self.waveform.bind('<Control-o>', lambda e: None)
        self.waveform.bind('<Control-O>', lambda e: None)
        self.waveform.bind('<Control-c>', lambda e: None)
        self.waveform.bind('<Control-x>', lambda e: None)
        self.master.updateEditMenu()

    """
    Deletes the selected waveform, and the selected waveform's overlays, and highlights
    triggered on <Delete>
    """
    def clearValues(self):
        self.values = list()
        self.clearAdditions()
        self.master.updateEditMenu()

    """
    Deletes the selected waveform's overlays, and highlights
    """
    def clearAdditions(self):
        self.hPoints, self.hLines, self.hLinesRaw, self.overlays = list(), list(), list(), list()

    """
    Updates the data stored in the waveform
    Data takes the form of a list:
    Element 1: Waveform type
                -Displayed below the graph
    Element 2: Waveform number
                -Displayed below the graph
    Element 3: Dataset to be graphed
    Element 4: offset of the graph from zero
    Element 5: filters which have been applied to dataset
    """
    def updateWaveformData(self, data):
        self.data = data
        self.values = data[2]
        self.start = data[3]
        self.analyser = Analysis(self.values, self)
        self.maxima, self.minima = self.analyser.findExtrema()
        self.waveType = data[0]
        self.waveNum = data[1]
        self.filtersApplied = data[4]
        try:
            maximum = self.analyser.findGlobalExtrema()[0]
        except ValueError:
            maximum = 0
        self.graphHeight = 1.25*self.values[maximum]
        self.zoomLevel = 1
        self.bL = [0, 0]
        if len(self.values)>3:
            self.waveform.bind('<Control-f>', lambda e: self.master.openSingleFilter())
            self.waveform.bind('<Control-o>', lambda e: self.master.addOverlay())
            self.waveform.bind('<Control-O>', lambda e: self.master.openOverlayCopy(self.values, self.start))
            self.waveform.bind('<Control-c>', lambda e:self.copy())
            self.waveform.bind('<Control-x>', lambda e:self.cut())
        self.master.updateEditMenu()
        self.clearAdditions()
        self.updateWaveform()

    """
    Portal to analyser for applying single filters
    """
    def applyFilter(self, filterName):
        returnedValues = list()
        exec('returnedValues = self.analyser.apply{}(self.start, True)'.format(filterName))
        self.updateWaveform()
        return returnedValues

    """
    Overlays another waveform onto the primary waveform
    """
    def addOverlay(self, data, start, color):
        self.overlays.append([data, start, color])
        self.updateWaveform()
    
    """
    Causes the mouseHUD to stop updating mouse coordinates,
    and changes the cursor back to the standard arrow
    """
    def cover(self, event):
        self.waveform.delete('mouseHUD')
        self.unBlocked = False
        self.waveform.config(cursor = 'arrow')

    """
    Updates the mouse position on the screen, and updates the maps position when being dragged
    Triggered by loop
    """
    def updateMouseHUD(self):
        self.waveform.delete('mouseHUD')
        x, y = self.waveform.winfo_pointerx()-self.waveform.winfo_rootx(), self.waveform.winfo_pointery()-self.waveform.winfo_rooty()
        if self.isDragging:
            self.waveDragMoving(x, y)
        if x>90 and x<self.waveform.winfo_width() and y>0 and y<self.waveform.winfo_height()-60 and len(self.values) > 2 and self.unBlocked:
            xTestVal = int(round((x-90)/self.scalingFactor[0]+self.bL[0]))
            xScreen = (xTestVal - self.bL[0])*self.scalingFactor[0]+90
            if xTestVal < len(self.values):
                yScreen = self.dimensions[1]-60-(self.values[xTestVal]-self.bL[1])*self.scalingFactor[1]
            else:
                yScreen = self.dimensions[1]-60-(self.values[len(self.values)-1]-self.bL[1])*self.scalingFactor[1]
            if xScreen > 90 and xScreen < self.waveform.winfo_width() and yScreen > 0 and yScreen < self.waveform.winfo_height()-60:
                self.waveform.create_line(xScreen-5, yScreen-5, xScreen+6, yScreen+6, tag = 'mouseHUD')
                self.waveform.create_line(xScreen-5, yScreen+6, xScreen+6, yScreen-5, tag = 'mouseHUD')
                self.waveform.create_text(135, self.waveform.winfo_height()-30, text = '({}, {})'.format(xTestVal+self.start, round(self.values[xTestVal], 4)), tag = 'mouseHUD')
            self.waveform.create_line(90, y, self.waveform.winfo_width(), y, tag = 'mouseHUD')
            self.waveform.create_line(x, 0, x, self.waveform.winfo_height()-60, tag = 'mouseHUD')
            self.waveform.create_text(45, self.waveform.winfo_height()-30, text = '({}, {})'.format(round((x-90)/self.scalingFactor[0]+self.bL[0], 2), round((self.dimensions[1]-60-y)/self.scalingFactor[1]+self.bL[1], 2)), tag = 'mouseHUD')
            self.waveform.config(cursor = 'none')
        else:
            self.waveform.config(cursor = 'arrow')

    """
    Updates the image of the waveform
    """
    def updateWaveform(self):
        global scaleDistances
        #clears the waveform image
        self.waveform.delete('toDelete')
        """creates the axes and axis labels"""
        self.waveform.create_text((self.dimensions[0] - 25)/2 + 45, self.dimensions[1] - 40, anchor = tk.N, text = 'Time (ns)', tag = 'toDelete')
        self.waveform.create_text(10, self.dimensions[1]/2 - 30, anchor = tk.W, text = 'Intensity', tag = 'toDelete')
        self.waveform.create_line(90, self.dimensions[1] - 60, self.dimensions[0], self.dimensions[1] - 60, tag = 'toDelete')
        self.waveform.create_line(90, self.dimensions[1] - 60, 90, 0, tag = 'toDelete')
        """creates the primary and secondary selection indicators"""
        if self.selected:
            self.waveform.create_oval(5, 5, 20, 20, tag = 'toDelete')
        if self.secondarySelected:
            self.waveform.create_oval(8, 8, 17, 17, tag = 'toDelete', fill = 'red', width = 0)
        """checks if a database has been opened and writes 'NO DATABASE', if none has been opened"""
        if len(self.master.databases) == 0:
            self.waveform.create_text((self.dimensions[0] - 25)/2 + 45, self.dimensions[1]/2 - 30, text = 'NO DATABASE', font = ('calabri', str(20)), tag = 'toDelete')
            return
        """checks if the display has been handed a valid dataset and writes 'NO DATA', if no data has been handed"""
        if len(self.values) < 3:
            self.waveform.create_text((self.dimensions[0] - 25)/2 + 45, self.dimensions[1]/2 - 30, text = 'NO DATA', font = ('calabri', str(20)), tag = 'toDelete')
            return
        if self.graphHeight == 0:
            self.waveform.create_text((self.dimensions[0] - 25)/2 + 45, self.dimensions[1]/2 - 30, text = 'NO DATA', font = ('calabri', str(20)), tag = 'toDelete')
            return
        """creates the waveform title"""
        self.waveform.create_text((self.dimensions[0] - 25)/2 + 45, self.dimensions[1] - 20, anchor = tk.N, text = ' '.join((self.waveType, str(self.waveNum))), tag = 'toDelete')
        """determines the vertical and horizontal scales of the waveform"""
        self.scaleLength = [14, 14]
        self.scaleDistance = [-1, -1]
        while self.scaleLength[0] > 13:
            self.scaleDistance[0] += 1
            self.scaleLength[0] = len(self.values)/(self.zoomLevel*scaleDistances[self.scaleDistance[0]])
        while self.scaleLength[1] > 13:
            self.scaleDistance[1] += 1
            self.scaleLength[1] = int(self.graphHeight)/(self.zoomLevel*scaleDistances[self.scaleDistance[1]])
        self.scalingFactor = [(self.dimensions[0]-90.)*self.zoomLevel/len(self.values), (self.dimensions[1] - 60.)*self.zoomLevel/self.graphHeight]
        """creates the scale along the axes and the grid, if on"""
        for n in range(self.scaleLength[0]):
            self.waveform.create_text(90 + n*self.scalingFactor[0]*scaleDistances[self.scaleDistance[0]], self.dimensions[1] - 55, anchor = tk.N, text = str(self.start+n*scaleDistances[self.scaleDistance[0]]+int(self.bL[0])), tag = 'toDelete')
            if self.master.gridOn == True:
                self.waveform.create_line(90 + n*self.scalingFactor[0]*scaleDistances[self.scaleDistance[0]], self.dimensions[1] - 60, 90 + n*self.scalingFactor[0]*scaleDistances[self.scaleDistance[0]], 0, fill = 'gray50', tag = 'toDelete')
        for n in range(self.scaleLength[1]):
            self.waveform.create_text(85, self.dimensions[1]-60-n*self.scalingFactor[1]*scaleDistances[self.scaleDistance[1]], anchor = tk.E, text = str(n*scaleDistances[self.scaleDistance[1]]+int(self.bL[1])), tag = 'toDelete')
            if self.master.gridOn == True:
                self.waveform.create_line(90, self.dimensions[1]-60-n*self.scalingFactor[1]*scaleDistances[self.scaleDistance[1]], self.dimensions[0], self.dimensions[1]-60-n*self.scalingFactor[1]*scaleDistances[self.scaleDistance[1]], fill = 'gray50', tag = 'toDelete')
        """creates the extrema points if display extrema is on"""
        if self.master.extremaOn == True:
            for n in range(len(self.maxima)):
                x, y = self.maxima[n], self.values[self.maxima[n]]
                if x > self.bL[0] and y > self.bL[1]:
                    self.waveform.create_oval(88 + (self.maxima[n]-self.bL[0])*self.scalingFactor[0], self.dimensions[1] - 58 - (self.values[self.maxima[n]]-self.bL[1])*self.scalingFactor[1], 92 + (self.maxima[n]-self.bL[0])*self.scalingFactor[0], self.dimensions[1] - 62 - (self.values[self.maxima[n]]-self.bL[1])*self.scalingFactor[1], width = 0, fill = 'red', tag = 'toDelete')
            for n in range(len(self.minima)):
                x, y = self.minima[n], self.values[self.minima[n]]
                if x > self.bL[0] and y > self.bL[1]:
                    self.waveform.create_oval(88 + (self.minima[n]-self.bL[0])*self.scalingFactor[0], self.dimensions[1] - 58 - (self.values[self.minima[n]]-self.bL[1])*self.scalingFactor[1], 92 + (self.minima[n]-self.bL[0])*self.scalingFactor[0], self.dimensions[1] - 62 - (self.values[self.minima[n]]-self.bL[1])*self.scalingFactor[1], width = 0, fill = 'cornflowerblue', tag = 'toDelete')
        """draws the main waveform, overlays, and highlights"""
        self.drawGraphLines(self.values)
        for n in range(len(self.overlays)):
            self.drawGraphLines(self.overlays[n][0], self.overlays[n][2], self.overlays[n][1]-self.start)
        for n in range(len(self.hPoints)):
            self.highlightPoint(self.hPoints[n][0], self.hPoints[n][1], self.hPoints[n][2])
        for n in range(len(self.hLines)):
            self.drawGraphLines(self.hLines[n][0], self.hLines[n][1])
    """
    Draws waveforms onto the graph
    """
    def drawGraphLines(self, values, color = 'black', offset = 0):
        renderFirst = True
        try:
            m = self.bL[0]-offset
            m = values[int(self.bL[0]-offset)+1]-values[int(self.bL[0]-offset)]
        except IndexError:
            renderFirst = False
        if renderFirst and self.bL[0] >= offset:
            if m*(self.bL[0]-int(self.bL[0]))+values[int(self.bL[0]-offset)]-self.bL[1] >= 0 and values[int(self.bL[0]-offset+1)]-self.bL[1] >= 0:
                self.waveform.create_line(90, self.dimensions[1]-60-(m*(self.bL[0]-int(self.bL[0]))+values[int(self.bL[0]-offset)]-self.bL[1])*self.scalingFactor[1], (int(self.bL[0])+1-self.bL[0])*self.scalingFactor[0]+90, self.dimensions[1]-60-(values[int(self.bL[0]-offset+1)]-self.bL[1])*self.scalingFactor[1], fill = color, tag = 'toDelete')
            elif values[int(self.bL[0]-offset+1)]-self.bL[1] >= 0 and m!= 0:
                x = (self.bL[1]-values[int(self.bL[0]-offset)])/m+int(self.bL[0])-offset
                self.waveform.create_line((x-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60, (int(self.bL[0])+1-self.bL[0])*self.scalingFactor[0]+90, self.dimensions[1]-60-(values[int(self.bL[0]-offset+1)]-self.bL[1])*self.scalingFactor[1], fill = color, tag = 'toDelete')
            elif m*(self.bL[0]-int(self.bL[0]))+values[int(self.bL[0]-offset)]-self.bL[1] >= 0 and m != 0:
                x = (self.bL[1]-values[int(self.bL[0]-offset)])/m+int(self.bL[0])-offset
                self.waveform.create_line(90, self.dimensions[1]-60-(m*(self.bL[0]-int(self.bL[0]))+values[int(self.bL[0]-offset)]-self.bL[1])*self.scalingFactor[1], (x-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60, fill = color, tag = 'toDelete')
        if int(self.bL[0]+1) < offset:
            rangeStart = 0
        else:
            rangeStart = int(self.bL[0]+1 - offset)
        for n in range(rangeStart, len(values) - 1):
            if values[n]-self.bL[1] >= 0 and values[n+1]-self.bL[1] >= 0:
                self.waveform.create_line((n-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60-(values[n]-self.bL[1])*self.scalingFactor[1], (n+1-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60-(values[n+1]-self.bL[1])*self.scalingFactor[1], fill = color, tag = 'toDelete')
            elif values[n]-self.bL[1] >= 0:
                m = values[n+1]-values[n]
                if m != 0:
                    x = (self.bL[1]-values[n])/m+n
                    self.waveform.create_line((n-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60-(values[n]-self.bL[1])*self.scalingFactor[1], (x-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60, fill = color, tag = 'toDelete')
            elif values[n+1]-self.bL[1] >= 0:
                m = values[n+1]-values[n]
                if m != 0:
                    x = (self.bL[1]-values[n])/m+n
                    self.waveform.create_line((x-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60, (n+1-self.bL[0]+offset)*self.scalingFactor[0]+90, self.dimensions[1]-60-(values[n+1]-self.bL[1])*self.scalingFactor[1], fill = color, tag = 'toDelete')

    """
    Highlights the given point in the given color
    """
    def highlightPoint(self, x, y, color):
        if x > self.bL[0] and y > self.bL[1]:
            self.waveform.create_oval((x-self.bL[0])*self.scalingFactor[0]+88, self.dimensions[1]-62-(y-self.bL[1])*self.scalingFactor[1], (x-self.bL[0])*self.scalingFactor[0]+92, self.dimensions[1]-58-(y-self.bL[1])*self.scalingFactor[1], fill = color, width = 0, tag = 'toDelete')

    """
    Appends a point and color to the points to be highlighted
    """
    def addHighlightPoint(self, x, y, color = 'green'):
        self.hPoints.append([x, y, color])

    """
    Appends a line and color to the lines to be highlighted
    """
    def addHighlightLine(self, xStart, yStart, xEnd, yEnd, color = 'black'):
        m = float(yStart-yEnd)/(xStart-xEnd)
        b = yStart-m*xStart
        if m!=0:
            xInt = (yStart-b)/m
        values = list()
        if m==0:
            for n in range(len(self.values)):
                values.append(b)
        elif xInt > len(self.values) or xInt < 0:
            for n in range(int(xInt+1)):
                values.append(m*n+b)
        else:
            for n in range(len(self.values)):
                values.append(m*n+b)
        self.hLinesRaw.append([xStart, yStart, xEnd, yEnd, color])
        self.hLines.append([values, color])

    """
    Sets the width and height of the display
    """
    def setDimensions(self, width, height):
        self.waveform.config(width = width, height = height)
        self.dimensions = (width, height)
        self.updateWaveform()

    """
    returns the width and height of the display
    """
    def getDimensions(self):
        return self.dimensions[0], self.dimensions[1]