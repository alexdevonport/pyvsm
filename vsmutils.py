"""
Helper classes for the pyvsm program.

-- AD 2017-02-17

TODO 2017-02-20: a lot of cruft accumulating in __init__ methods,
maybe good to factorize. So far have settled on multi-level dict
as main data structure for VSM data, seemed the best way to handle 3
levels of 2-value categories for the data (easy vs hard, up vs down,
raw data vs fit). Honestly seems easier to deal with than a pandas
multi-index dataframe.

"""


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shelve
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import itertools as it
import analysisutils


class VsmSession:
    def __init__(self, name='Untitled VSM session', samples=[],
        settings={}):
        self.name = name
        self.samples = samples
        self.settings = settings
        if self.samples:
            self.currentWorkingSample = samples[0]
        else:
            self.currentWorkingSample = None
        return None

    def addSample(self, name, makeCurrent=False):
        newSample = VsmSample(name=name)
        self.samples.append(newSample)
        if makeCurrent:
            self.currentWorkingSample = self.samples[-1]
        return None


    def renameCurrentWorkingSample(self, newname):
        if newname != '':
            self.currentWorkingSample.name = newname
        return None

    
    def removeCurrentWorkingSample(self):
        idx = self.samples.index(self.currentWorkingSample)
        self.samples.remove(self.currentWorkingSample)
        try:
            self.currentWorkingSample = self.samples[idx-1]
        except IndexError:
            self.currentWorkingSample = None

    def save(self):
        return None


class VsmSample:
    """
    VsmSession stores a list of these, one for each physical
    sample under analysis. contains raw data and analysis results
    for easy and hard axis, however much data is available.

    The GUI will have a scrollbox allowing you to select which
    data set will be the current working data set.

    Every data set gets its own analyzer, for custon configuration.
    """
    def __init__(self, name):
        self.name = name
        self.results = {}
        self.analyzer = analysisutils.VsmAnalyzer(self)
        self.data = {}
        self.easyAxisDataFilepath = ''
        self.hardAxisDataFilepath = ''
        idx_tups = list(it.product(['easy', 'hard'],
            ['data','fit'],
            ['up','down']))
        for idx in idx_tups:
            self.data[' '.join(idx)] = {'H':np.array([]), 
                'M':np.array([])}
        return None


    def importData(self, filepath, axis):
        """
        Read M-H data from a CSV, and update either the 
        easy axis or the hard axis data frame. Any data
        previously in the data frame 
        """
        # read raw data from CSV
        a=pd.read_csv(filepath, header=9,sep='\t', names=['h','m'])
        hpts = a['h']
        mpts = a['m']
        hup, mup, hdn, mdn = self.splitupdn(hpts, mpts)
        # insert split data into the easy or hard data frame.
        self.data[axis+' data up'] = {'H':np.array(hup), 
            'M':np.array(mup)}
        self.data[axis+' data down'] = {'H':np.array(hdn), 
            'M':np.array(mdn)}

        if axis == 'easy':
            self.easyAxisDataFilepath = filepath
        else:
            self.hardAxisDataFilepath = filepath
        return None

    def splitupdn(self,hpts, mpts):
        hup = []
        mup = []
        hdn = []
        mdn = []
        dh = np.diff(hpts)
        for k,dhk in enumerate(dh):
            if dhk > 0:
                hup.append(hpts[k])
                mup.append(mpts[k])
            else:
                hdn.append(hpts[k])
                mdn.append(mpts[k])
        return hup, mup, hdn, mdn


    def analyzeData(self):
        self.analyzer.analyzeData()
        print(self.results)


class VsmPlotter(tk.Frame):
    """
    Class to contain the matplotlib graphs and to interface
    with the current working sample to get information.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.fig = Figure(figsize=(8,4))
        self.fig.patch.set_facecolor('#d9d9d9')
        self.easyax = self.fig.add_subplot(121)
        self.easyax.set_title('Easy Axis')
        self.easyax.set_xlabel('field (Oe)')
        self.easyax.set_ylabel('moment (emu$\\times 10^{-6}$)')
        self.hardax = self.fig.add_subplot(122, sharey=self.easyax)
        self.hardax.set_title('Hard Axis')
        self.hardax.set_xlabel('field (Oe)')
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(side=tk.LEFT)
        self.canvas._tkcanvas.pack(side=tk.LEFT, fill=tk.BOTH, 
            expand=1)
        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)
        self.fig.tight_layout(pad=2)
        return None


    def redraw(self, sample):
        """
        redraw easy and hard axis plots.
        """
        self.easyax.lines = []
        self.hardax.lines = []
        if sample:
            ds = sample.data
            plotArgs = [('data up', 'k', ':'),
                        ('data down', 'k', ':'),
                        ('fit up', 'k', '--'),
                        ('fit down', 'k', '--')]
            for key, color, linestyle in plotArgs:
                self.easyax.plot(ds['easy '+key]['H'], 
                    ds['easy '+key]['M']*1E6, color=color, 
                    linestyle=linestyle)
                self.hardax.plot(ds['hard '+key]['H'], 
                    ds['hard '+key]['M']*1E6, color=color, 
                    linestyle=linestyle)
        else:
            self.easyax.plot([],[])
            self.hardax.plot([],[])
        self.canvas.show()
        return None


class DataSetsFrame(tk.Frame):
    """
    Frame that displays a tree of the samples entered by the user,
    and the data files uploaded for those samples. Also Gives the user
    options to upload and manage samples.
    """
    def __init__(self):
        super().__init__()
        self.samplesLabel = tk.Label(self,text='samples', relief='sunken')
        self.samplesLabel.pack(fill='x')
        self.spacerLabel = tk.Label(self)
        self.spacerLabel.pack(fill='x')
        self.dataSetList = tk.Listbox(self)
        self.dataSetList.pack(fill='y')
        self.addSampleButton = tk.Button(self, text='Add Sample')
        self.addSampleButton.pack(fill='x')
        self.renameSampleButton = tk.Button(self, text='Rename Sample')
        self.renameSampleButton.pack(fill='x')
        self.removeSampleButton = tk.Button(self, text='Remove Sample')
        self.removeSampleButton.pack(fill='x')
        self.spacerLabel = tk.Label(self,text='')
        self.spacerLabel.pack(fill='both')
        return None


class AnalysisManagerFrame(tk.Frame):
    """
    Frame that is used to organize analysis of data sets 
    from the loaded samples.
    """
    def __init__(self):
        super().__init__()
        self.analysisLabel = tk.Label(self, text='Analysis',
            relief='sunken')
        self.analysisLabel.pack(fill='x')
        self.spacerLabel = tk.Label(self, text='')
        self.spacerLabel.pack(fill='x')
        self.easyAxisDataLabel = tk.Label(self, text='easy axis data file',
            relief='sunken')
        self.easyAxisDataLabel.pack(fill='x')
        self.easyAxisFileSelector = FileSelectorButton(self)
        self.easyAxisFileSelector.pack()
        self.hardAxisDataLabel = tk.Label(self, text='hard axis data file',
            relief='sunken')
        self.hardAxisDataLabel.pack(fill='x')
        self.hardAxisFileSelector = FileSelectorButton(self)
        self.hardAxisFileSelector.pack()

        self.analysisOptionsButton = tk.Button(self, 
            text='Analysis options')
        self.analysisOptionsButton.pack(fill='x')

        self.analyzeButton = tk.Button(self, text='Analyze')
        self.analyzeButton.pack(fill='x')

        return None


class AxisDialog:
    """
    Dialog prompting the user to indicate if a data file
    contains easy axis or hard axis data.
    """
    def __init__(self, parent, ax):
        self.top = tk.Toplevel(parent)
        l = tk.Label(self.top, 
            text='Importing easy axis or hard axis data?')
        l.pack(padx=10)
        ebutton = tk.Radiobutton(self.top, text='Easy Axis',
            variable=ax, value='easy').pack(padx=20)
        hbutton = tk.Radiobutton(self.top, text='Hard Axis',
            variable=ax, value='hard').pack(padx=20)
        b = tk.Button(self.top, text='OK', command=self.ok)
        b.pack(pady=5)
        return None


    def ok(self):
        self.top.destroy()
        return None


def askAxis(master):
    axVariable = tk.StringVar()
    ad = AxisDialog(master, axVariable)
    master.wait_window(ad.top)
    return axVariable.get()
    

class StringDialog:
    """
    Dialog prompting the user to enter a string.
    """
    def __init__(self, parent, title, prompt, textvar, init=''):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        l = tk.Label(self.top, 
            text=prompt)
        l.pack(padx=10)
        e = tk.Entry(self.top, textvariable=textvar)
        textvar.set(init)
        e.pack(pady=5)
        b = tk.Button(self.top, text='OK', command=self.ok)
        b.pack(pady=5)
        return None


    def ok(self):
        self.top.destroy()
        return None


def askstring(master, title, prompt, init=''):
    var = tk.StringVar()
    sd = StringDialog(master, title, prompt, var)
    master.wait_window(sd.top)
    return var.get()


class FileSelectorButton(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.filepath = tk.StringVar()
        self.fileChangeCallback = None
        self.filepathEntry = tk.Entry(self, state='readonly',
            textvariable=self.filepath, justify='left')
        self.filepathEntry.pack(side='left', ipady=3)
        self.browseButton = tk.Button(self, text='browse',
            command=self.browse)
        self.browseButton.pack(side='right')
        return None


    def browse(self):
        newFilePath = filedialog.askopenfilename()
        self.filepath.set(newFilePath)
        if newFilePath != '' and self.fileChangeCallback:
            self.fileChangeCallback()
        return None


