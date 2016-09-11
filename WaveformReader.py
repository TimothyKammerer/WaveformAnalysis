"""
Master Class for waveform reader and analyser
Reads and catalogues text files for display and analysis
"""

import Tkinter as tk
import os
import sys
import inspect

fileName = inspect.getfile(inspect.currentframe())
moduleDirName = os.path.realpath(os.path.dirname(fileName))
sys.path.append(moduleDirName)
sys.path.append(os.path.join(moduleDirName, "numpy\\Lib\\site-packages\\numpy-1.11.1-py2.7-win-amd64.egg"))

from Display import Display
from Analysis import Analysis
from Svmgen import Svmgen
import FileExporter

standardWidth = 525 + 90
standardHeight = 250 + 60
screenSize = [2, 2]
defaultOverlayColor = 'red'

"""
Tuple of filters which can be applied to waveforms

All elements follow format:
Element 1: filter name
               e.g.-Lowpass
Element 2: filters which must have been applied in order to apply filter
               e.g.-Christmas_Tree filter requires a waveform filtered with a Bottomreturn_Isolation
Element 3: filters which cannot have been applied in order to apply filter
               e.g.-Bottomreturn_Isolation filter requires a waveform which has not been filtered with a Bottomreturn_Isolation
Element 4: names of datatypes stored in a .csv file if, when bulk filtering, additional data is stored
"""
filters = (('Lowpass', tuple(), tuple(['Christmas_Tree']), tuple()),
           ('Raw_Bottomreturn_Isolation', tuple(), ('LogAmp', 'Bottomreturn_Isolation', 'Raw_Bottomreturn_Isolation', 'Derivative'), ('BR peak', 'BR length', 'Leading Edge')),
           ('Bottomreturn_Isolation', tuple(['Noise_Reduction']),('Bottomreturn_Isolation', 'Raw_Bottomreturn_Isolation', 'Derivative'), ('BR peak', 'BR length', 'Leading Edge')),
           ('Christmas_Tree', tuple(['Bottomreturn_Isolation']), ('Christmas_Tree', 'Derivative'), ('CT peak', 'CT length', 'XRCOV', 'slope left', 'slope right', 'R2 left', 'R2 right')),
           ('Christmas_Tree', tuple(['Raw_Bottomreturn_Isolation']), ('Christmas_Tree', 'Derivative'), ('CT peak', 'CT length', 'XRCOV', 'slope left', 'slope right', 'R2 left', 'R2 right')),
           ('LogAmp', tuple(), ('Bottomreturn_Isolation', 'Christmas_Tree', 'Lowpass', 'Derivative', 'LogAmp'), tuple()),
           ('Noise_Reduction', tuple(), ('Bottomreturn_Isolation', 'Christmas_Tree', 'Derivative'), tuple()),
           ('Derivative', tuple(), tuple(), tuple()),
           ('None', tuple(), tuple(), tuple()),
           ('Increase', tuple(), tuple(), tuple()))

"""
Master Class of program
Used to:
-update display objects
-call file analyses
-call single analyses
-update selected database
-perform edit menu functions
    -i.e. undo, redo, cut, copy, paste, delete
"""
class WaveformReader():
    def __init__(self, display = True):
        self.dirName = moduleDirName
        if os.path.exists(os.path.join(os.path.realpath(moduleDirName), 'memory', 'waveform_option_memory.txt')):
            execfile(os.path.join(os.path.realpath(moduleDirName), 'memory', 'waveform_option_memory.txt'))
        else:
            os.makedirs(os.path.join(self.dirName, 'memory'))
            open(os.path.join(self.dirName, 'memory', 'waveform_option_memory.txt'), 'w').close()
        global screenSize
        self.setupFileSorting()
        if display:
            self.setupClassVariables()
            self.setupDisplay()
            self.setupMenubar()
            for x in range(len(self.screen)):
                for y in range(len(self.screen[x])):
                    self.screen[x][y].updateWaveform()
            self.window.after(1, self.loop)
            self.window.mainloop()

    """
    Sets up the file sorting system in the form:
    -WaveformReader
        -SVM
            -formulae
            -returns
            -samples
        -waveform_data
            -databasename0
                -additional_data
                    -filtered_data.csv
                    -anotherfilter_data.csv
                    ...
                -raw_data.txt
                -filtered.txt
                -anotherfilter.txt
                ...
            -databasename1
                -additional_data
                    ...
                -raw_data.txt
                ...
            ...
    called by __init__
    """
    def setupFileSorting(self):
        if not os.path.exists(os.path.join(self.dirName, 'SVM')):
            os.makedirs(os.path.join(self.dirName, 'SVM'))
        if not os.path.exists(os.path.join(self.dirName, 'SVM', 'samples')):
            os.makedirs(os.path.join(self.dirName, 'SVM', 'samples'))
        if not os.path.exists(os.path.join(self.dirName, 'SVM', 'returns')):
            os.makedirs(os.path.join(self.dirName, 'SVM', 'returns'))
        if not os.path.exists(os.path.join(self.dirName, 'waveform_data')):
            os.makedirs(os.path.join(self.dirName, 'waveform_data'))
        for file in os.listdir(self.dirName):
            if file.endswith('.txt'):
                if os.path.exists(os.path.join(self.dirName, 'waveform_data', file[:len(file) - 4])):
                    n = 0
                    while True:
                        if not os.path.exists(os.path.join(self.dirName, 'waveform_data', '_'.join((file[:len(file) - 4], str(n))))):
                            os.makedirs(os.path.join(self.dirName, 'waveform_data', '_'.join((file[:len(file) - 4], str(n)))))
                            os.makedirs(os.path.join(self.dirName, 'waveform_data', '_'.join((file[:len(file) - 4], str(n))), 'additional_data'))
                            os.makedirs(os.path.join(self.dirName, 'SVM', 'samples', '_'.join((file[:len(file) - 4], str(n)))))
                            self.processRaw(os.path.join(self.dirName, file), os.path.join(self.dirName, 'waveform_data', '_'.join((file[:len(file) - 4], str(n))), 'raw_data.txt'))
                            break
                        n+=1
                else:
                    os.makedirs(os.path.join(self.dirName, 'waveform_data', file[:len(file) - 4]))
                    os.makedirs(os.path.join(self.dirName, 'waveform_data',file[:len(file) - 4], 'additional_data'))
                    os.makedirs(os.path.join(self.dirName, 'SVM', 'samples', file[:len(file) - 4]))
                    self.processRaw(os.path.join(self.dirName, file), os.path.join(self.dirName, 'waveform_data', file[:len(file) - 4], 'raw_data.txt'))
        self.databaseOptions = list()
        for dir in os.listdir(os.path.join(self.dirName, 'waveform_data')):
            self.databaseOptions.append(dir)

    """
    Processes raw .txt data files by spliting the lines by commas,
    removing the first two elements, and appending a :0 to each line,
    which signifies that the waveform's start is offset by 0 nanoseconds
    called by setupFileSorting
    """
    def processRaw(self, oldPath, newPath):
        lines = open(oldPath, 'r').readlines()
        saveFile = open(newPath, 'w')
        for n in range(len(lines)):
            saveFile.write(':'.join([','.join(lines[n].split(',')[2:])[:len(','.join(lines[n].split(',')[2:]))-1], '0\n']))
        saveFile.write('None')
        saveFile.close()
        os.remove(oldPath)

    """
    Sets up a screenSize[0] x screenSize[1](width x height) array of waveform displays
    called by __init__
    """
    def setupDisplay(self):
        self.window = tk.Tk(className = 'Waveform Display')
        self.window.geometry('{0}x{1}+0+0'.format(standardWidth*screenSize[0], standardHeight*screenSize[1]))
        self.databaseNameplate = tk.Label(self.window, text = 'Current Database: None', bg = 'gray95')
        self.databaseNameplate.grid(row = 0, column = 0, columnspan = screenSize[0])
        self.screen = list()
        for x in range(screenSize[0]):
            screenRow = list()
            for y in range(screenSize[1]):
                screenRow.append(Display(self, standardHeight, standardWidth, x, y))
            self.screen.append(screenRow)
        self.focused = [1, 1]
        self.screen[0][0].waveform.focus_force()
        self.screen[0][0].selected = True
        self.secondaryFocused = [2, 1]
        self.screen[1][0].secondarySelected = True
        self.hovering = [1, 1]

    """
    Sets up the empty class variables, which are used for opening waveforms,
    copying waveforms and tell whether extrema and the grid are displayed
    called by __init__
    """
    def setupClassVariables(self):
        self.databases = dict()
        self.databaseLineOffsets = dict()
        self.clipBoard = ['', 0, [0, 0], 0, '']
        self.extremaOn, self.gridOn = False, False
        self.actions = list()
        self.looping = True

    """
    Sets up the file, edit, display, and analysis menus
    called by __init__
    """
    def setupMenubar(self):
        menubar = tk.Menu(self.window)
        #Create file menu
        self.fileMenu = tk.Menu(menubar, tearoff = 0)
        self.databaseMenu = tk.Menu(self.fileMenu, tearoff = 1)
        self.databaseSelectors = dict()
        for n in range(len(self.databaseOptions)):
            self.databaseSelectors[self.databaseOptions[n]] = self.DatabaseSelect(self, self.databaseMenu, self.databaseOptions[n])
        self.fileMenu.add_cascade(label = 'Change Database', menu = self.databaseMenu)
        self.fileMenu.add_command(label = 'Export to Excel', command = lambda: FileExporter.Excel(self.currentDatabase), state = tk.DISABLED)
        #Create edit menu
        self.editMenu = tk.Menu(menubar, tearoff = 0)
        self.editMenu.add_command(label = 'Undo', command = self.undoAction, state = tk.DISABLED)
        self.editMenu.add_command(label = 'Redo', command = self.redoAction, state = tk.DISABLED)
        self.editMenu.add_separator()
        self.editMenu.add_command(label = 'Cut', command = self.cutScreen, state = tk.DISABLED)
        self.editMenu.add_command(label = 'Copy', command = self.copyScreen, state = tk.DISABLED)
        self.editMenu.add_command(label = 'Paste', command = self.pasteScreen, state = tk.DISABLED)
        self.editMenu.add_command(label = 'Delete', command = self.deleteScreen, state = tk.DISABLED)
        #Create display menu
        self.displayMenu = tk.Menu(menubar, tearoff = 0)
        self.displayMenu.add_command(label = 'Change Waveform', command = self.changeWaveform, state = tk.DISABLED)
        self.displayMenu.add_command(label = 'Add Overlay', command = self.addOverlay, state = tk.DISABLED)
        self.displayMenu.add_command(label = 'Transfer to Overlay', command = self.overlayTransfer)
        self.grid = tk.BooleanVar(self.window)
        self.displayMenu.add_checkbutton(label = 'Show Grid', variable = self.grid, onvalue = True, offvalue = False, command = self.updateGlobalVariables)
        #Create analysis menu
        self.analysisMenu = tk.Menu(menubar, tearoff = 0)
        self.extrema = tk.BooleanVar(self.window)
        self.analysisMenu.add_checkbutton(label = 'Show Extrema', variable = self.extrema, onvalue = True, offvalue = False, command = self.updateGlobalVariables)
        self.filterMenu = tk.Menu(self.analysisMenu, tearoff = 0)
        self.filterMenu.add_command(label = 'Single', command = self.openSingleFilter, state = tk.DISABLED)
        self.filterMenu.add_command(label = 'File', command = self.openBulkFilter, state = tk.DISABLED)
        self.analysisMenu.add_cascade(label = 'Run Filter', menu = self.filterMenu)
        self.analysisMenu.add_command(label = 'Graph Data Density', command = self.openCreateDataDensityGraph, state = tk.DISABLED)
        self.analysisMenu.add_command(label = 'SVM', command = lambda: Svmgen(self.currentDatabase, self.dirName), state = tk.DISABLED)
        #Create preference menu
        preferenceMenu = tk.Menu(menubar, tearoff = 0)
        preferenceMenu.add_command(label = 'Change Root Directory', command = self.openChangeRootDirectory)
        #Format menubar
        menubar.add_cascade(label = 'File', menu = self.fileMenu)
        menubar.add_cascade(label = 'Edit', menu = self.editMenu)
        menubar.add_cascade(label = 'Display', menu = self.displayMenu)
        menubar.add_cascade(label = 'Analysis', menu = self.analysisMenu)
        menubar.add_cascade(label = 'Preferences', menu = preferenceMenu)
        self.window.config(menu = menubar, bg = 'gray95')

    """
    Displays the mouse coordinates while it hovers over a particular display, and
    adjusts the display size to match the master window
    """
    def loop(self):
        self.updateWaveformSize()
        self.updateMouseCoords()
        if self.looping:
            self.window.after(1, self.loop)

    """
    updates the edit menu, so that cut, copy, and delete are only active if a
    display with a waveform displayed is selected
    """
    def updateEditMenu(self):
        if len(self.screen[self.focused[0]-1][self.focused[1]-1].values) < 2:
            self.editMenu.entryconfig(3, state = tk.DISABLED)
            self.editMenu.entryconfig(4, state = tk.DISABLED)
            self.editMenu.entryconfig(6, state = tk.DISABLED)
        else:
            self.editMenu.entryconfig(3, state = tk.ACTIVE)
            self.editMenu.entryconfig(4, state = tk.ACTIVE)
            self.editMenu.entryconfig(6, state = tk.ACTIVE)

    """
    adjusts the display size to match the master window
    called by loop
    """
    def updateWaveformSize(self):
        global screenSize
        width, height = self.screen[0][0].getDimensions()
        if screenSize[1] == 1:
            height+=18
        winWidth, winHeight = self.window.winfo_width()/screenSize[0], self.window.winfo_height()/screenSize[1]
        if winWidth != width or winHeight != height:
            print 'update'
            for x in range(len(self.screen)):
                for y in range(len(self.screen[x])):
                    if y == len(self.screen[x])-1:
                        self.screen[x][y].setDimensions(winWidth, winHeight-18)
                    else:
                        self.screen[x][y].setDimensions(winWidth, winHeight)

    """
    Opens a window for defining variables used to create an overlay
    triggered by 'Add Overlay' in the display menu
    """
    def addOverlay(self):
        global showCoords
        self.changeOverlay = tk.Tk(className = 'Add Overlay')
        tk.Label(self.changeOverlay, text = 'Data Type = ').grid(row = 0, column = 0)
        dataType = tk.StringVar(self.changeOverlay)
        dataType.set('raw_data')
        tk.OptionMenu(self.changeOverlay, dataType, *self.databases[self.currentDatabase].keys()).grid(row = 0, column = 1)
        tk.Label(self.changeOverlay, text = 'Waveform Number:').grid(row = 2, column = 0)
        overlayEntry = tk.Entry(self.changeOverlay)
        overlayEntry.insert(0, 1)
        overlayEntry.selection_range(0, tk.END)
        overlayEntry.grid(row = 2, column = 1, columnspan = 2)
        overlayEntry.bind('<Up>', lambda e: self.changeFilter(-1, dataType, self.databases[self.currentDatabase].keys()))
        overlayEntry.bind('<Down>', lambda e: self.changeFilter(1, dataType, self.databases[self.currentDatabase].keys()))
        overlayEntry.focus_force()
        colorOptions = ('red', 'blue', 'purple', 'green')
        color = tk.StringVar(self.changeOverlay, colorOptions[0])
        tk.Label(self.changeOverlay, text = 'Color: ').grid(row = 3, column = 0)
        tk.OptionMenu(self.changeOverlay, color, *colorOptions).grid(row = 3, column = 1, columnspan = 2)
        overlayChangeButton = tk.Button(self.changeOverlay, text = 'Update', command = lambda: self.testOverlayUpdate(dataType.get(), overlayEntry.get(), color.get()))
        overlayChangeButton.grid(row = 5, column = 0, columnspan = 3)
        overlayEntry.bind('<Return>', lambda e: overlayChangeButton.invoke())
        overlayChangeButton.bind('<Return>', lambda e: overlayChangeButton.invoke())
        self.changeOverlay.mainloop()

    """
    Checks if the number of the waveform entered into the window created in addOverlay is valid
    """
    def testOverlayUpdate(self, dataType, entry, color):
        try:
            entry = int(entry)
        except ValueError:
            entry = -1
        if entry >= 0 and entry <= len(self.databaseLineOffsets[self.currentDatabase][dataType])-1:
            self.updateOverlays(dataType, entry, color)
            self.changeOverlay.destroy()
        else:
            tk.Label(self.changeWave, text = 'INVALID ENTRY').grid(row = 4, column = 0, columnspan = 3)

    """
    Adds an overlay of a waveform to a display, which already possesses a primary waveform
    the overlay can be displayed in a variety of colors
    """
    def updateOverlays(self, dataType, update, color):
        winX, winY = self.focused[0]-1, self.focused[1]-1
        openedFile = open(self.databases[self.currentDatabase][dataType], 'r')
        openedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType][update-1])
        line = openedFile.readline()
        openedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType][len(self.databaseLineOffsets[self.currentDatabase][dataType])-1])
        openedFile.close()
        data = line.split(',')
        tempVar = data[len(data)-1].split(':')
        data[len(data)-1] = tempVar[0]
        start = int(tempVar[1])
        for n in range(len(data)):
            data[n] = float(data[n])
        screenData = self.screen[winX][winY].data
        oldAdditions = [list(self.screen[winX][winY].overlays), list(self.screen[winX][winY].hPoints), list(self.screen[winX][winY].hLinesRaw)]
        self.screen[winX][winY].addOverlay(data, start, color)
        newAdditions = [list(self.screen[winX][winY].overlays), list(self.screen[winX][winY].hPoints), list(self.screen[winX][winY].hLinesRaw)]
        self.appendAction([[[winX, winY], screenData, screenData, newAdditions, oldAdditions]])

    """
    Copies the primary selected waveform and pastes it onto the secondary selected waveform as an overlay
    triggered on <Control-Shift-o>
    """
    def openOverlayCopy(self, data, start):
        global defaultOverlayColor
        if len(self.screen[self.secondaryFocused[0]-1][self.secondaryFocused[1]-1].values)>3:
            self.screen[self.secondaryFocused[0]-1][self.secondaryFocused[1]-1].addOverlay(list(data), int(start), defaultOverlayColor)

    """
    Copies the primary selected waveform and pastes it onto the secondary selected waveform as an overlay
    triggered by 'Transfer to Overlay' in the display menu
    """
    def overlayTransfer(self):
        global defaultOverlayColor
        if len(self.screen[self.secondaryFocused[0]-1][self.secondaryFocused[1]-1].values)>3 and len(self.screen[self.focused[0]-1][self.focused[1]-1].values)>3:
            data = list(self.screen[self.focused[0]-1][self.focused[0]-1].values)
            start = int(self.screen[self.focused[0]-1][self.focused[0]-1].start)
            self.screen[self.secondaryFocused[0]-1][self.secondaryFocused[1]-1].addOverlay(data, start, defaultOverlayColor)

    def openBulkFilter(self):
        global filters
        self.bulkFilterWin = tk.Tk(className = 'Run Filter')
        tk.Label(self.bulkFilterWin, text = 'Data Type = ').grid(row = 0, column = 0)
        dataType = tk.StringVar(self.bulkFilterWin)
        exists = False
        for n in range(len(self.databases[self.currentDatabase].keys())):
            if self.databases[self.currentDatabase].keys()[n]=='raw_data':
                exists = True
        if exists:
            dataType.set('raw_data')
        else:
            dataType.set(self.databases[self.currentDatabase].keys()[0])
        tk.OptionMenu(self.bulkFilterWin, dataType, *self.databases[self.currentDatabase].keys(), command = lambda e: self.updateFilterOptions(dataType, filterApplying)).grid(row = 0, column = 1)
        tk.Label(self.bulkFilterWin, text = 'Filter Type = ').grid(row = 1, column = 0)
        selectedFile = open(self.databases[self.currentDatabase][dataType.get()], 'r')
        selectedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType.get()][len(self.databaseLineOffsets[self.currentDatabase][dataType.get()])-1])
        line = selectedFile.readline()
        selectedFile.close()
        filtersApplied = line.split(',')
        filterNames = list()
        for a in range(len(filters)):
            numberApplied = 0
            for b in range(len(filters[a][1])):
                for c in range(len(filtersApplied)):
                    if filtersApplied[c] == filters[a][1][b]:
                        numberApplied += 1
                        break
            passing = True
            for b in range(len(filters[a][2])):
                for c in range(len(filtersApplied)):
                    if filtersApplied[c] == filters[a][2][b]:
                        passing = False
                        break
                if not passing:
                    break
            if passing and numberApplied == len(filters[a][1]):
                filterNames.append(filters[a][0])
        filterApplying = tk.StringVar(self.bulkFilterWin, filterNames[0])
        self.filterOptions = tk.OptionMenu(self.bulkFilterWin, filterApplying, *filterNames)
        self.filterOptions.grid(row = 1, column = 1)
        fileReturn = tk.BooleanVar(self.bulkFilterWin, False)
        tk.Checkbutton(self.bulkFilterWin, text = 'Store Additional Data?', variable = fileReturn, onvalue = True, offvalue = False).grid(row = 2, column = 0, columnspan = 2)
        tk.Label(self.bulkFilterWin, text = 'Save New Data as:').grid(row = 3, column = 0)
        fileEntry = tk.Entry(self.bulkFilterWin)
        fileEntry.grid(row = 3, column = 1)
        actButton = tk.Button(self.bulkFilterWin, text = 'Apply', command = lambda: self.testRunBulkFilter(dataType.get(), filterApplying.get(), fileEntry.get(), fileReturn.get()))
        actButton.grid(row = 4, column = 0, columnspan = 2)
        fileEntry.bind('<Return>', lambda e: actButton.invoke())
        actButton.bind('<Return>', lambda e: actButton.invoke())
        self.bulkFilterWin.mainloop()

    def updateFilterOptions(self, dataType, filterApplying):
        selectedFile = open(self.databases[self.currentDatabase][dataType.get()], 'r')
        selectedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType.get()][len(self.databaseLineOffsets[self.currentDatabase][dataType.get()])-1])
        line = selectedFile.readline()
        selectedFile.close()
        filtersApplied = line.split(',')
        filterNames = list()
        for a in range(len(filters)):
            numberApplied = 0
            for b in range(len(filters[a][1])):
                for c in range(len(filtersApplied)):
                    if filtersApplied[c] == filters[a][1][b]:
                        numberApplied += 1
                        break
            passing = True
            for b in range(len(filters[a][2])):
                for c in range(len(filtersApplied)):
                    if filtersApplied[c] == filters[a][2][b]:
                        passing = False
                        break
                if not passing:
                    break
            if passing and numberApplied == len(filters[a][1]):
                filterNames.append(filters[a][0])
        filterApplying.set(filterNames[0])
        self.filterOptions.destroy()
        self.filterOptions = tk.OptionMenu(self.bulkFilterWin, filterApplying, *filterNames)
        self.filterOptions.grid(row = 1, column = 1)

    def testRunBulkFilter(self, dataType, filterType, fileName, fileReturns):
        for file in os.listdir(os.path.join(self.dirName, 'waveform_data', self.currentDatabase)):
            if file[:len(file) - 4] == fileName:
                self.overwriting = tk.Tk()
                tk.Label(self.overwriting, text = 'File Already Exists').grid(row = 0, column = 0, columnspan = 2)
                tk.Label(self.overwriting, text = 'Overwrite?').grid(row = 1, column = 0, columnspan = 2)
                yes = tk.Button(self.overwriting, text = 'Yes', command = lambda: self.runBulkFilter(dataType, filterType, fileName, fileReturns))
                yes.grid(row = 2, column = 0)
                yes.bind('<Return>', lambda e: yes.invoke())
                yes.focus_force()
                no = tk.Button(self.overwriting, text = 'No', command = self.overwriting.destroy)
                no.grid(row = 2, column = 1)
                no.bind('<Return>', lambda e: no.invoke())
                self.overwriting.mainloop()
                return
        self.runBulkFilter(dataType, filterType, fileName, fileReturns)

    def runBulkFilter(self, dataType, filterType, fileName, fileReturns):
        global filters
        self.looping = False
        self.bulkFilterWin.destroy()
        try:
            self.overwriting.destroy()
        except:
            pass
        filterBarMaster = tk.Tk(className = ''.join(('Processing ', filterType, '...')))
        filterBar = tk.Canvas(filterBarMaster, width = 150, height = 76)
        filterBar.pack()
        filterBar.create_text(75, 38, text = '/'.join((str(0), str(len(self.databaseLineOffsets[self.currentDatabase][dataType])))))
        saveFile = open('.'.join((os.path.join(self.dirName, 'waveform_data', self.currentDatabase, fileName), 'txt')), 'w+')
        filterBarMaster.update()
        if fileReturns:
            dataFile = open('.'.join((os.path.join(self.dirName, 'waveform_data', self.currentDatabase, 'additional_data', '{}_data'.format(fileName)), 'csv')), 'w+')
            for n in range(len(filters)):
                if filterType == filters[n][0]:
                    filterNum = int(n)
            for n in range(len(filters[filterNum][3])):
                dataFile.write(filters[filterNum][3][n])
                if n != len(filters[filterNum][3])-1:
                    dataFile.write(',')
                else:
                    dataFile.write('\n')
        for n in range(len(self.databaseLineOffsets[self.currentDatabase][dataType])):
            filterBar.delete('all')
            filterBar.create_text(75, 38, text = '/'.join((str(n+1), str(len(self.databaseLineOffsets[self.currentDatabase][dataType])))))
            filterBarMaster.update()
            openedFile = open(self.databases[self.currentDatabase][dataType], 'r')
            openedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType][n])
            line = openedFile.readline()
            openedFile.close()
            data = line.split(',')
            if n != len(self.databaseLineOffsets[self.currentDatabase][dataType])-1:
                tempVar = data[len(data)-1].split(':')
                data[len(data)-1] = tempVar[0]
                start = int(tempVar[1])
                start
                for n in range(len(data)):
                    data[n] = float(data[n])
                fileData, filterData = list(), list()
                startPoint = 0
                if not fileReturns:
                    exec('filterData, startPoint, fileData = Analysis(data).apply{}(start)'.format(filterType))
                else:
                    exec('filterData, startPoint, fileData = Analysis(data).apply{}(start, True)'.format(filterType))
                    for m in range(len(fileData)):
                        dataFile.write(str(fileData[m]))
                        if m != len(fileData) - 1:
                            dataFile.write(',')
                        else:
                            dataFile.write('\n')
                for m in range(len(filterData)):
                    saveFile.write(str(round(filterData[m], 2)))
                    if m != len(filterData) - 1:
                        saveFile.write(',')
                    else:
                        saveFile.write(''.join((':', str(startPoint), '\n')))
            else:
                if filterType == 'None':
                    saveFile.write(line)
                else:
                    written = False
                    for m in range(len(data)):
                        if data[m] == filterType:
                            written = True
                        if data[m] != 'None':
                            saveFile.write(''.join((data[m], ',')))
                    if not written:
                        saveFile.write(filterType)
        saveFile.close()
        try:
            dataFile.close()
        except NameError:
            pass
        filterBarMaster.destroy()
        self.updateDatabase(self.currentDatabase)
        self.looping = True
        self.window.after(1, self.loop)

    def openSingleFilter(self):
        global filters
        self.singleFilterWin = tk.Tk(className = 'Run Filter')
        filtersApplied = self.screen[self.focused[0]-1][self.focused[1]-1].filtersApplied
        filterNames = list()
        for a in range(len(filters)):
            numberApplied = 0
            for b in range(len(filters[a][1])):
                for c in range(len(filtersApplied)):
                    if filtersApplied[c] == filters[a][1][b]:
                        numberApplied += 1
                        break
            passing = True
            for b in range(len(filters[a][2])):
                for c in range(len(filtersApplied)):
                    if filtersApplied[c] == filters[a][2][b]:
                        passing = False
                        break
                if not passing:
                    break
            if passing and numberApplied == len(filters[a][1]):
                filterNames.append(filters[a][0])
        filterName = tk.StringVar(self.singleFilterWin, filterNames[0])
        tk.Label(self.singleFilterWin, text = 'Filter: ').grid(row = 2, column = 0)
        tk.OptionMenu(self.singleFilterWin, filterName, *filterNames).grid(row = 2, column = 1, columnspan = 2)
        filterButton = tk.Button(self.singleFilterWin, text = 'Run Filter', command = lambda: self.runSingleFilter(filterName.get()))
        filterButton.grid(row = 3, column = 0, columnspan = 3)
        filterButton.focus_force()
        filterButton.bind('<Return>', lambda e: filterButton.invoke())
        filterButton.bind('<Up>', lambda e: self.changeFilter(-1, filterName, filterNames))
        filterButton.bind('<Down>', lambda e: self.changeFilter(1, filterName, filterNames))
        self.singleFilterWin.mainloop()

    def changeFilter(self, increment, filterName, filterNames):
        for n in range(len(filterNames)):
            if filterName.get()==filterNames[n]:
                break
        if n+increment > len(filterNames)-1:
            filterName.set(filterNames[0])
        elif n+increment < 0:
            filterName.set(filterNames[len(filterNames)-1])
        else:
            filterName.set(filterNames[n+increment])

    def runSingleFilter(self, filterName):
        self.singleFilterWin.destroy()
        xIn, yIn = self.focused[0]-1, self.focused[1]-1
        xOut, yOut = self.secondaryFocused[0]-1, self.secondaryFocused[1]-1
        filterData, startPoint, filedata = self.screen[xIn][yIn].applyFilter(filterName)
        filtersApplied = list(self.screen[xIn][yIn].filtersApplied)
        filtersApplied.append(filterName)
        oldData = list(self.screen[xOut][yOut].data)
        inOldData = list(self.screen[xIn][yIn].data)
        oldAdditions = [list(self.screen[xOut][yOut].overlays), list(self.screen[xOut][yOut].hPoints), list(self.screen[xOut][yOut].hLinesRaw)]
        inOldAdditions = [list(self.screen[xIn][yIn].overlays), list(self.screen[xIn][yIn].hPoints), list(self.screen[xIn][yIn].hLinesRaw)]
        newData = [filterName, int(self.screen[xIn][yIn].waveNum), filterData, startPoint, filtersApplied]
        self.screen[xOut][yOut].updateWaveformData(newData)
        inNewData = list(self.screen[xIn][yIn].data)
        newAdditions = [list(self.screen[xOut][yOut].overlays), list(self.screen[xOut][yOut].hPoints), list(self.screen[xOut][yOut].hLinesRaw)]
        inNewAdditions = [list(self.screen[xIn][yIn].overlays), list(self.screen[xIn][yIn].hPoints), list(self.screen[xIn][yIn].hLinesRaw)]
        if xIn == xOut and yIn == xIn:
            self.appendAction([[[xOut, yOut], newData, oldData, newAdditions, oldAdditions]])
        else:
            self.appendAction([[[xOut, yOut], newData, oldData, newAdditions, oldAdditions], [[xIn, yIn], inNewData, inOldData, inNewAdditions, inOldAdditions]])

    def changeWaveform(self):
        global showCoords
        self.changeWave = tk.Tk(className = 'Change Waveform')
        tk.Label(self.changeWave, text = 'Data Type = ').grid(row = 0, column = 0)
        dataType = tk.StringVar(self.changeWave, 'raw_data')
        tk.OptionMenu(self.changeWave, dataType, *self.databases[self.currentDatabase].keys()).grid(row = 0, column = 1)
        tk.Label(self.changeWave, text = 'Waveform Number:').grid(row = 2, column = 0)
        waveEntry = tk.Entry(self.changeWave)
        waveEntry.insert(0, 1)
        waveEntry.selection_range(0, tk.END)
        waveEntry.grid(row = 2, column = 1, columnspan = 2)
        waveEntry.bind('<Return>', lambda e: self.waveChangeButton.invoke())
        waveEntry.bind('<Up>', lambda e: self.changeFilter(-1, dataType, self.databases[self.currentDatabase].keys()))
        waveEntry.bind('<Down>', lambda e: self.changeFilter(1, dataType, self.databases[self.currentDatabase].keys()))
        waveEntry.focus_force()
        self.waveChangeButton = tk.Button(self.changeWave, text = 'Update', command = lambda: self.testWaveformUpdate(dataType.get(), waveEntry.get()))
        self.waveChangeButton.grid(row = 4, column = 0, columnspan = 3)
        self.waveChangeButton.bind('<Return>', lambda e: self.waveChangeButton.invoke())
        self.changeWave.mainloop()

    def testWaveformUpdate(self, dataType, entry):
        try:
            entry = int(entry)
        except ValueError:
            entry = -1
        if entry >= 0 and entry <= len(self.databaseLineOffsets[self.currentDatabase][dataType])-1:
            self.updateWaveformNum(dataType, entry)
            self.changeWave.destroy()
        else:
            tk.Label(self.changeWave, text = 'INVALID ENTRY').grid(row = 3, column = 0, columnspan = 3)

    def updateWaveformNum(self, dataType, update):
        winX, winY = self.focused[0]-1, self.focused[1]-1
        openedFile = open(self.databases[self.currentDatabase][dataType], 'r')
        openedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType][update-1])
        line = openedFile.readline()
        openedFile.seek(self.databaseLineOffsets[self.currentDatabase][dataType][len(self.databaseLineOffsets[self.currentDatabase][dataType])-1])
        filtersApplied = openedFile.readline().split(',')
        openedFile.close()
        data = line.split(',')
        tempVar = data[len(data)-1].split(':')
        data[len(data)-1] = tempVar[0]
        start = int(tempVar[1])
        for n in range(len(data)):
            data[n] = float(data[n])
        oldData = list(self.screen[winX][winY].data)
        oldAdditions = [list(self.screen[winX][winY].overlays), list(self.screen[winX][winY].hPoints), list(self.screen[winX][winY].hLinesRaw)]
        newData = [dataType, update, data, start, filtersApplied]
        self.screen[winX][winY].updateWaveformData(newData)
        newAdditions = [list(self.screen[winX][winY].overlays), list(self.screen[winX][winY].hPoints), list(self.screen[winX][winY].hLinesRaw)]
        self.appendAction([[[winX, winY], newData, oldData, newAdditions, oldAdditions]])

    def openCreateDataDensityGraph(self):
        self.densityWin = tk.Tk(className = 'Graph Density')
        tk.Label(self.densityWin, text = 'Data Type = ').grid(row = 0, column = 0)
        dataType = tk.StringVar(self.densityWin, 'raw_data')
        tk.OptionMenu(self.densityWin, dataType, *self.databases[self.currentDatabase].keys()).grid(row = 0, column = 1)
        densityButton = tk.Button(self.densityWin, text = 'Create Graph', command = lambda:self.createDataDensityGraph(dataType.get()))
        densityButton.grid(row = 1, column = 0, columnspan = 2)
        densityButton.bind('<Return>', lambda e: densityButton.invoke())
        densityButton.bind('<Up>', lambda e: self.changeFilter(-1, dataType, self.databases[self.currentDatabase].keys()))
        densityButton.bind('<Down>', lambda e: self.changeFilter(1, dataType, self.databases[self.currentDatabase].keys()))

    def createDataDensityGraph(self, dataType):
        self.densityWin.destroy()
        densityData = list()
        readFile = open(os.path.join(self.dirName, 'waveform_data', self.currentDatabase, '{}.txt'.format(str(dataType))))
        first = readFile.readline().split(',')
        densityStart = int(first[len(first)-1].split(':')[1])
        fileLength = len(self.databaseLineOffsets[self.currentDatabase][dataType])
        l = 0
        for line in readFile:
            if l < fileLength-2:
                data = line.split(',')
                tempVar = data[len(data)-1].split(':')
                data[len(data)-1] = tempVar[0]
                start = int(tempVar[1])
                if start<densityStart:
                    appension = list()
                    for n in range(densityStart-start):
                        appension.append(0)
                    densityData = appension + densityData
                    densityStart = int(start)
                for n in range(len(data)):
                    if len(densityData)-1 < n+start-densityStart:
                        densityData.append(float(data[n]))
                    else:
                        densityData[n+start-densityStart]+=float(data[n])
            l+=1
        x, y = self.focused[0]-1, self.focused[1]-1
        self.screen[x][y].updateWaveformData(['{}_density'.format(dataType), 0, densityData, densityStart, ['Density']])

    def updateGlobalVariables(self):
        self.extremaOn, self.gridOn = self.extrema.get(), self.grid.get()
        if len(self.databases.keys()) != 0:
            for x in range(len(self.screen)):
                for y in range(len(self.screen[x])):
                    self.screen[x][y].updateWaveform()

    def switchGrid(self, event):
        if self.grid.get():
            self.grid.set(False)
        else:
            self.grid.set(True)
            
        self.updateGlobalVariables()

    def switchExtrema(self, event):
        if self.extrema.get():
            self.extrema.set(False)
        else:
            self.extrema.set(True)
        self.updateGlobalVariables()

    def openDatabaseChange(self):
        self.dataChange = tk.Tk()
        directSelect = tk.StringVar(self.dataChange, self.databaseOptions[0])
        tk.OptionMenu(self.dataChange, directSelect, *self.databaseOptions).grid(row = 0, column = 0)
        selectButton = tk.Button(self.dataChange, text = 'Update', command = lambda:self.runUpdateDatabase(directSelect.get()))
        selectButton.bind('<Up>', lambda e: self.changeFilter(-1, directSelect, self.databaseOptions))
        selectButton.bind('<Down>', lambda e: self.changeFilter(1, directSelect, self.databaseOptions))
        selectButton.bind('<Return>', lambda e: selectButton.invoke())
        selectButton.grid(row = 1, column = 0)
        selectButton.focus_force()
        self.dataChange.mainloop()
        
    def runUpdateDatabase(self, name):
        self.dataChange.destroy()
        self.databaseMenu.invoke(name)

    def updateDatabase(self, databaseName):
        '''Used to update the line spacings for the databases and define which databases have been updated'''
        database = dict()
        thisDatabaseLineOffsets = dict()
        for file in os.listdir(os.path.join(self.dirName, 'waveform_data', databaseName)):
            if file.endswith('.txt'):
                database[file[:len(file) - 4]] = os.path.join(self.dirName, 'waveform_data', databaseName, file)
                openedFile = open(os.path.join(self.dirName, 'waveform_data', databaseName, file))
                fileLineOffsets = list()
                offset = 0
                for line in openedFile:
                    fileLineOffsets.append(offset)
                    offset += len(line) + 1
                thisDatabaseLineOffsets[file[:len(file) - 4]] = fileLineOffsets
                openedFile.close()
        self.databases[databaseName] = database
        self.databaseLineOffsets[databaseName] = thisDatabaseLineOffsets
        self.currentDatabase = databaseName
        self.databaseNameplate.config(text = ' '.join(('Current Database:', self.currentDatabase)))
        self.databaseSelectors[databaseName].switchMode()
        self.displayMenu.entryconfig(0, state = tk.ACTIVE)
        self.displayMenu.entryconfig(1, state = tk.ACTIVE)
        self.filterMenu.entryconfig(0, state = tk.ACTIVE)
        self.filterMenu.entryconfig(1, state = tk.ACTIVE)
        self.fileMenu.entryconfig(1, state = tk.ACTIVE)
        self.editMenu.entryconfig(4, state = tk.ACTIVE)
        self.analysisMenu.entryconfig(2, state = tk.ACTIVE)
        
        databaseHasSample = False
        for database in self.databaseOptions:
            if len(os.listdir(os.path.join(self.dirName, 'SVM', 'samples', database))) != 0:
                databaseHasSample = True
        if databaseHasSample:
            self.analysisMenu.entryconfig(3, state = tk.ACTIVE)
        else:
            self.analysisMenu.entryconfig(3, state = tk.DISABLED)
        if len(self.databases.keys()) == 1:
            for x in range(len(self.screen)):
                for y in range(len(self.screen[x])):
                    self.screen[x][y].updateWaveform()
                    self.screen[x][y].waveform.bind('<Control-w>', lambda e: self.changeWaveform())
                    self.screen[x][y].waveform.bind('<Control-F>', lambda e: self.openBulkFilter())

    def openDatabase(self, databaseName):
        self.currentDatabase = databaseName
        self.databaseNameplate.config(text = ' '.join(('Current Database:', self.currentDatabase)))

    def openChangeRootDirectory(self):
        self.rootDirChange = tk.Tk()
        rootDirEntry = tk.StringVar(self.rootDirChange, self.dirName)
        tk.Label(self.rootDirChange, text = 'New Directory:').grid(row = 0, column = 0)
        tk.Entry(self.rootDirChange, textvariable = rootDirEntry, width = 30).grid(row = 1, column = 0)
        tk.Button(self.rootDirChange, text = 'Update Root Directory', command = lambda: self.changeRootDirectory(rootDirEntry.get())).grid(row = 2, column = 0)

    def changeRootDirectory(self, newDir):
        self.rootDirChange.destroy()
        newDir = '\\\\'.join(newDir.split('\\'))
        self.dirName = newDir
        self.updateMemory()
        self.window.destroy()
        self.__init__()

    def updateMemory(self):
        memoryFile = open(os.path.join(moduleDirName, 'memory', 'waveform_option_memory.txt'), 'w')
        memoryFile.write('self.dirName = "{}"'.format(self.dirName))
        memoryFile.close()

    def updateUndoMenu(self):
        if len(self.actions) > 0:
            self.editMenu.entryconfig(0, state = tk.ACTIVE)
        else:
            self.editMenu.entryconfig(0, state = tk.DISABLED)
        if len(self.undoneActions) > 0:
            self.editMenu.entryconfig(1, state = tk.ACTIVE)
        else:
            self.editMenu.entryconfig(1, state = tk.DISABLED)

    def appendAction(self, sets):
        self.actions.append(sets)
        if len(self.actions) > 10:
            del self.actions[0]
        self.undoneActions = list()
        self.updateUndoMenu()

    def undoAction(self):
        try:
            self.actions[len(self.actions)-1]
        except IndexError:
            return
        for n in range(len(self.actions[len(self.actions)-1])):
            action = self.actions[len(self.actions)-1][n]
            x, y = action[0][0], action[0][1]
            data = action[2]
            overlays = action[4][0]
            hPoints = action[4][1]
            hLines = action[4][2]
            self.screen[x][y].updateWaveformData(data)
            for n in range(len(overlays)):
                self.screen[x][y].addOverlay(*overlays[n])
            for n in range(len(hPoints)):
                self.screen[x][y].addHighlightPoint(*hPoints[n])
            for n in range(len(hLines)):
                self.screen[x][y].addHighlightLine(*hLines[n])
        self.undoneActions.append(list(self.actions[len(self.actions)-1]))
        del self.actions[len(self.actions)-1]
        self.updateUndoMenu()
        self.updateEditMenu()

    def redoAction(self):
        try:
            self.undoneActions[len(self.undoneActions)-1]
        except IndexError:
            return
        for n in range(len(self.undoneActions[len(self.undoneActions)-1])):
            action = self.undoneActions[len(self.undoneActions)-1][n]
            x, y = action[0][0], action[0][1]
            data = action[1]
            overlays = action[3][0]
            hPoints = action[3][1]
            hLines = action[3][2]
            self.screen[x][y].updateWaveformData(data)
            for n in range(len(overlays)):
                self.screen[x][y].addOverlay(*overlays[n])
            for n in range(len(hPoints)):
                self.screen[x][y].addHighlightPoint(*hPoints[n])
            for n in range(len(hLines)):
                self.screen[x][y].addHighlightLine(*hLines[n])
        self.actions.append(self.undoneActions[len(self.undoneActions)-1])
        del self.undoneActions[len(self.undoneActions)-1]
        self.updateUndoMenu()
        self.updateEditMenu()

    def cutScreen(self):
        self.screen[self.focused[0]-1][self.focused[1]-1].cut()

    def copyScreen(self):
        self.screen[self.focused[0]-1][self.focused[1]-1].copy()

    def pasteScreen(self):
        self.screen[self.focused[0]-1][self.focused[1]-1].paste()

    def deleteScreen(self):
        self.screen[self.focused[0]-1][self.focused[1]-1].clearValues()

#Viewing controls:
    def toggleFullscreen(self):
        global screenSize
        if self.window.attributes('-fullscreen'):
            self.window.attributes('-fullscreen', False)
            self.window.geometry(self.prevGeom)
        else:
            self.prevGeom = '{0}x{1}+0+0'.format(self.window.winfo_width(), self.window.winfo_height())
            self.window.attributes('-fullscreen', True)
        for x in range(len(self.screen)):
            for y in range(len(self.screen[x])):
                self.screen[x][y].setDimensions(self.window.winfo_width()/screenSize[0], self.window.winfo_height()/screenSize[1])

    def setHover(self, coords):
        self.screen[self.hovering[0]-1][self.hovering[1]-1].updateMouseHUD()
        self.hovering = coords
        self.screen[self.hovering[0]-1][self.hovering[1]-1].unBlocked = True

    def updateMouseCoords(self):
        self.screen[self.hovering[0]-1][self.hovering[1]-1].updateMouseHUD()

    def hoverZoom(self, event):
        self.screen[self.hovering[0]-1][self.hovering[1]-1].zoomDelta(event.delta)


    class DatabaseSelect():
        def __init__(self, window, menu, databaseName):
            self.name = databaseName
            self.menu = menu
            self.master = window
            menu.add_command(label = str(self.name), command = lambda: window.updateDatabase(self.name))
        def switchMode(self):
            self.menu.entryconfig(self.name, command = lambda: self.master.openDatabase(self.name))

test = WaveformReader()