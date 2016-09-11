from sklearn import svm
import Tkinter as tk
import os
"""
Note: files in SVM\samples\(databaseName) must be a comma delimited .txt or a .csv
      and their  first column is the classification, and the second column is the waveform number
"""
class Svmgen():
    def __init__(self, database, dirName):
        self.database = database
        self.dirName = dirName
        self.findFileData()
        self.findDatabaseOptions()
        self.setupWindow()
        self.root.mainloop()

    def findDatabaseOptions(self):
        databases = os.listdir(os.path.join(self.dirName, 'waveform_data'))
        self.databaseDataPoints = dict()
        for database in databases:
            if len(os.listdir(os.path.join(self.dirName, 'SVM', 'Samples', database))) and len(os.listdir(os.path.join(self.dirName, 'waveform_data', database, 'additional_data'))):
                currentDatabase = dict()
                for file in os.listdir(os.path.join(self.dirName, 'waveform_data', database, 'additional_data')):
                    for fileKey in self.dataPoints.keys():
                        if fileKey == file:
                            currentDatabase[file] = list()
                            f = open(os.path.join(self.dirName, 'waveform_data', database, 'additional_data', file))
                            dataLine = f.readline()
                            dataLine = dataLine[:len(dataLine)-1].split(',')
                            f.close()
                            for point in dataLine:
                                if self.dataPoints[fileKey].__contains__(point):
                                    currentDatabase[file].append(point)
                            if len(currentDatabase[file]) == 0:
                                currentDatabase.pop(file)
                            break
                if len(currentDatabase.keys()) != 0:
                    self.databaseDataPoints[database] = currentDatabase


    def findFileData(self):
        self.dataPoints = dict()
        for file in os.listdir(os.path.join(self.dirName, 'waveform_data', self.database, 'additional_data')):
            if file.endswith('.csv'):
                self.dataPoints[file] = list()
                dataFile = open(os.path.join(self.dirName, 'waveform_data', self.database, 'additional_data', file))
                line = dataFile.readline()
                dataTypes = line[:len(line)-1].split(',')
                for n in range(len(dataTypes)):
                    self.dataPoints[file].append(dataTypes[n])
                dataFile.close()

    def setupWindow(self):
        self.root = tk.Tk(className = 'svm')
        tk.Label(self.root, text = 'Sample Database:').grid(row = 0, column = 0)
        hasSamples = False
        for database in self.databaseDataPoints.keys():
            if database == self.database:
                hasSamples = True
        if hasSamples:
            self.sampleDatabase = tk.StringVar(self.root, self.database)
        else:
            self.sampleDatabase = tk.StringVar(self.root, self.databaseDataPoints.keys()[0])
        tk.OptionMenu(self.root, self.sampleDatabase, *self.databaseDataPoints.keys(), command = lambda e: self.updateSampleDatabase()).grid(row = 0, column = 1)
        tk.Label(self.root, text = 'Sample File:').grid(row = 1, column = 0)
        self.updateSamples()
        tk.Label(self.root, text = 'Use Data:').grid(row = 2, column = 0)
        self.generateFrames()
        tk.Label(self.root, text = 'Output Name:').grid(row = 4, column = 0)
        output = tk.StringVar(self.root)
        tk.Entry(self.root, textvariable = output).grid(row = 4, column = 1)
        genButton = tk.Button(self.root, text = 'generate', command = lambda: self.generate(output.get(), self.sample.get()))
        genButton.grid(row = 5, column = 0, columnspan = 2)

    def updateSampleDatabase(self):
        self.updateSamples()
        self.generateFrames()

    def updateSamples(self):
        try:
            self.root.grid_slaves(1, 1)[0].grid_forget()
        except IndexError:
            pass
        self.samples = list()
        for file in os.listdir(os.path.join(self.dirName, 'SVM', 'samples', self.sampleDatabase.get())):
            if file.endswith('.txt') or file.endswith('.csv'):
                self.samples.append(file)
        try:
            self.sample = tk.StringVar(self.root, self.samples[0])
        except IndexError:
            self.sample = tk.StringVar(self.root, str())
        tk.OptionMenu(self.root, self.sample, *self.samples).grid(row = 1, column = 1)
        
    def generateFrames(self):
        self.openData = tk.StringVar(self.root, self.databaseDataPoints[self.sampleDatabase.get()].keys()[0])
        tk.OptionMenu(self.root, self.openData, *self.databaseDataPoints[self.sampleDatabase.get()].keys(), command = self.flipFrame).grid(row = 2, column = 1)
        self.pointFrames = dict()
        self.checks = dict()
        for key in self.databaseDataPoints[self.sampleDatabase.get()].keys():
            self.checks[key] = list()
            self.pointFrames[key] = tk.Frame(self.root)
            for m in range(len(self.databaseDataPoints[self.sampleDatabase.get()][key])):
                self.checks[key].append(tk.BooleanVar(self.pointFrames[key], False))
                tk.Checkbutton(self.pointFrames[key], variable = self.checks[key][m], onvalue = True, offvalue = False, text = self.databaseDataPoints[self.sampleDatabase.get()][key][m]).grid(row = m/2, column = m%2, sticky = tk.W)
        self.flipFrame(self.openData.get())

    def flipFrame(self, fileName):
        try:
            self.root.grid_slaves(3, 0)[0].grid_forget()
        except IndexError:
            pass
        self.pointFrames[fileName].grid(row = 3, column = 0, columnspan = 2)

    def generate(self, outputName, sampleName):
        if len(outputName)==0:
            return
        self.root.destroy()
        self.offsets = dict()
        for file in os.listdir(os.path.join(self.dirName, 'waveform_data', self.sampleDatabase.get(), 'additional_data')):
            if file.endswith('.csv'):
                dataFile = open(os.path.join(self.dirName, 'waveform_data', self.sampleDatabase.get(), 'additional_data', file))
                offset = 0
                dataFile.seek(0)
                self.offsets[file] = list()
                for line in dataFile:
                    self.offsets[file].append(offset)
                    offset += len(line) + 1
                self.offsets[file] = self.offsets[file][1:]
                dataFile.close()
        self.usingSets = dict()
        for key in self.dataPoints.keys():
            buttons = self.checks[key]
            self.usingSets[key] = list()
            for m in range(len(buttons)):
                if buttons[m].get():
                    self.usingSets[key].append(m)
        sampleFile = open(os.path.join(self.dirName, 'SVM', 'samples', self.sampleDatabase.get(), sampleName))
        samples = sampleFile.readlines()
        sampleFile.close()
        pointList = list()
        typeList = list()
        for n in range(len(samples)):
            pointList.append(list())
            samples[n] = samples[n].split(',')
            typeList.append(samples[n][0])
            samples[n] = int(samples[n][1])
        self.scales = dict()
        for key in self.usingSets.keys():
            if len(self.usingSets[key]) != 0:
                dataFile = open(os.path.join(self.dirName, 'waveform_data', self.sampleDatabase.get(), 'additional_data', key))
                dataLines = dataFile.readlines()[1:]
                for m in range(len(dataLines)):
                    dataLines[m] = dataLines[m].split(',')
                    for l in range(len(dataLines[m])):
                        dataLines[m][l] = float(dataLines[m][l])
                data = zip(*dataLines)
                self.scales[key] = list()
                for m in range(len(data)):
                    self.scales[key].append(4/(max(data[m])-min(data[m])))
                for m in range(len(samples)):
                    dataFile.seek(self.offsets[key][samples[m]-1])
                    lineData = dataFile.readline().split(',')
                    for l in range(len(self.usingSets[key])):
                        pointList[m].append(float(lineData[self.usingSets[key][l]])*self.scales[key][self.usingSets[key][l]])
                dataFile.close()
        self.clf = svm.SVC(kernel = 'rbf')
        self.clf.fit(pointList, typeList)
        self.predict(outputName)

    def predict(self, outputName):
        file = open(os.path.join(self.dirName, 'SVM', 'returns', '{}.csv'.format(outputName)), 'w')
        file.write('Waveform,Classification\n')
        file.close()
        dataLines = dict()
        for n in range(len(self.usingSets.keys())):
            key = self.usingSets.keys()[n]
            dataFile = open(os.path.join(self.dirName, 'waveform_data', self.database, 'additional_data', key))
            dataLines[key] = dataFile.readlines()[1:]
            dataFile.close()
        for lineNumber in range(len(dataLines[dataLines.keys()[0]])):
            data = list()
            for n in range(len(dataLines.keys())):
                key = dataLines.keys()[n]
                lineData = dataLines[key][lineNumber].split(',')
                for m in range(len(self.usingSets[key])):
                    data.append(float(lineData[self.usingSets[key][m]])*self.scales[key][self.usingSets[key][m]])
            file = open(os.path.join(self.dirName, 'SVM\\returns', '{}.csv'.format(outputName)), 'a')
            file.write('{},{}\n'.format(lineNumber+1, self.clf.predict([data])[0]))
            file.close()
            if lineNumber%100==0:
                print lineNumber