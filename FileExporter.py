"""
Exports a .txt waveform file to a .csv file
"""
import Tkinter as tk
import os
class Excel():
    """
    Initializes the file origin and destination selection window
    """
    def __init__(self, currentDatabase):
        self.excelWindow = tk.Tk(className = 'export')
        exportOptions = list()
        for file in os.listdir(os.path.join('waveform_data', currentDatabase)):
            if file.endswith('.txt'):
                exportOptions.append(file[:len(file)-4])
        exportChoice = tk.StringVar(self.excelWindow, exportOptions[0])
        tk.Label(self.excelWindow, text = 'Export from: ').grid(row = 0, column = 0)
        exportMenu = tk.OptionMenu(self.excelWindow, exportChoice, *exportOptions)
        exportMenu.grid(row = 0, column = 1)
        tk.Label(self.excelWindow, text = 'Export to: ').grid(row = 1, column = 0)
        exportEntry = tk.Entry(self.excelWindow)
        exportEntry.grid(row = 1, column = 1)
        exportEntry.selection_range(0, tk.END)
        exportEntry.focus_force()
        exportButton = tk.Button(self.excelWindow, text = 'Export', command = lambda: self.exportFile(currentDatabase, exportChoice.get(), exportEntry.get()))
        exportButton.grid(row = 2, column = 0, columnspan = 2)
        exportEntry.bind('<Return>', lambda e: exportButton.invoke())
        exportButton.bind('<Return>', lambda e: exportButton.invoke())
        self.excelWindow.mainloop()

    """
    Exports the waveform file from the current database to a new location with type .csv
    """
    def exportFile(self, currentDatabase, currentFileName, newFileLocation):
        self.excelWindow.destroy()
        oldFile = open(os.path.join('waveform_data', currentDatabase, '{}.txt'.format(currentFileName)))
        lines = oldFile.readlines()
        oldFile.close()
        newFile = open('{}.csv'.format(newFileLocation), 'w')
        for n in range(len(lines)-1):
            newFile.write('{}\n'.format(lines[n].split(':')[0]))