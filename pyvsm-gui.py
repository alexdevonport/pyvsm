import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import vsmutils
import pickle

"""
Camel case, bitches
"""


def main():
    root = tk.Tk()
    root.title('PyVSM')
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 0, weight=1)
    app = PyVsmApplication(root)
    app.mainloop()

class PyVsmApplication(tk.Frame):
    """
    Main frame of the pyvsm GUI, and controller of program flow.
    The only item to be placed directly on root.

    Uses the following helper classes, which will be in vsmutils.py:
      - VsmSession (stores other classes & data structure for saving)
      - VsmSample (iterable object which loads VSM data & metadata,
        also includes fits and analysis results)
      - VsmAnalyzer (class to configure & interface with analysis routines)
      - VsmPlotter (interface between VsmSamples and matplotlib/tkinter)
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.session = vsmutils.VsmSession()
        self.addSample(name='unnamed sample')
        return None


    def create_widgets(self):
        self.create_menu()
        self.dataSetsFrame = vsmutils.DataSetsFrame()
        self.dataSetsFrame.pack(side=tk.LEFT, anchor='n')
        self.dataSetsFrame.dataSetList.bind('<<ListboxSelect>>', 
            self.updateCurrentWorkingSample)
        self.dataSetsFrame.addSampleButton.config(command=self.addSample)

        self.plotter = vsmutils.VsmPlotter(self.master)
        self.plotter.pack(side=tk.LEFT, expand=1)

        self.analysisManager = vsmutils.AnalysisManagerFrame()
        self.analysisManager.easyAxisFileSelector \
            .fileChangeCallback = lambda: self.importData(axis='easy',
            fp=self.analysisManager.easyAxisFileSelector.filepath.get())
        self.analysisManager.hardAxisFileSelector \
            .fileChangeCallback = lambda: self.importData(axis='hard',
            fp=self.analysisManager.hardAxisFileSelector.filepath.get())
        self.analysisManager.pack(side=tk.LEFT, expand=1,
            anchor='n')
        return None


    def create_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Open VSM session',
            command=self.loadSession)
        filemenu.add_command(label='Save VSM session',
            command=self.saveSession)
        filemenu.add_command(label='import data',
            command=lambda: self.importData())
        filemenu.add_command(label='Quit', command=self.safequit)
        menubar.add_cascade(label='File', menu=filemenu)
        sessionmenu = tk.Menu(menubar, tearoff=0)
        sessionmenu.add_command(label='print session name', 
            command=self.printSessionName)
        sessionmenu.add_command(label='Rename session',
            command=self.renameSession)
        sessionmenu.add_command(label='Add Sample',
            command=self.addSample)
        sessionmenu.add_command(label='Rename Sample',
            command=self.renameCurrentworkingSample)
        menubar.add_cascade(label='Session', menu=sessionmenu)
        self.master.config(menu=menubar)
        return None

    
    def loadSession(self):
        f = filedialog.askopenfile(mode='rb')
        s = pickle.load(f)
        self.session = s
        self.update()
        return None

    
    def saveSession(self):
        f = filedialog.asksaveasfile(mode='wb')
        pickle.dump(self.session, f)
        return None


    def printSessionName(self):
        print(self.session.name)
        return None


    def renameSession(self):
        newname = vsmutils.askstring(self.master, 'new session name', 
            'Enter new session name: ')
        self.session.name = newname
        return None


    def importData(self, fp='', axis=''):
        if fp == '':
            fp = filedialog.askopenfilename()
        if axis == '':
            axis = vsmutils.askAxis(self.master)
        if self.session.currentWorkingSample:
            self.session.currentWorkingSample.importData(fp, axis)
        else:  # no current sample, make a new one
            self.addSample(name='unnamed sample')
        self.update()
        return None
    
    

    def addSample(self, name=None):
        if not name:
            name = vsmutils.askstring(self.master, 'new sample',
                'Name of new sample:')
        self.session.addSample(name, True)
        self.dataSetsFrame.dataSetList.insert(tk.END, name)
        self.update()
        return None
    

    def renameCurrentworkingSample(self):
        newname = vsmutils.askstring(self.master, 'new sample name',
            'enter new name for current sample',
            init=self.session.currentWorkingSample.name)
        # modify to handle more whitespace cases
        # what if user tries to name the sample ' \t  '?
        if newname != '': 
            self.session.currentWorkingSample.name = newname
        self.update()
        return None


    def safequit(self):
        confirmed = messagebox.askyesno('Quit', 
            'Are you sure you want to quit?')
        if confirmed:
            self.master.destroy()
        return None


    def hi(self):
        print('hi')


    def update(self):
        """
        Master update method, calls update methods of all subclasses.
        """
        self.updateSamples()
        self.updatePlotter()
        self.updateAnalysisManager()


    def updateSamples(self):
        self.dataSetsFrame.dataSetList.delete(0,tk.END)
        for sample in self.session.samples:
            self.dataSetsFrame.dataSetList.insert(tk.END, sample.name)
        return None


    def updateCurrentWorkingSample(self, evt):
        newCurrentWorkingSampleIndex = self.dataSetsFrame \
            .dataSetList.curselection()
        self.session.currentWorkingSample = self.session. \
            samples[newCurrentWorkingSampleIndex[0]]
        print(self.session.currentWorkingSample.name)
        self.update()
        return None
   

    def updatePlotter(self):
        # set plotter up with new data
        data = self.session.currentWorkingSample  # for now
        self.plotter.redraw(data)
        return None


    def updateAnalysisManager(self):
        self.analysisManager.easyAxisFileSelector.filepath.set(
            self.session.currentWorkingSample.easyAxisDataFilepath)
        self.analysisManager.hardAxisFileSelector.filepath.set(
            self.session.currentWorkingSample.hardAxisDataFilepath)
        return None

if __name__ == '__main__':
    main()


