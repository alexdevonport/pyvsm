import tkinter as tk

class ReadOnlyText(tk.Text):
    """
    A Tkinter text box 
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.config(relief='sunken', 
            background=self.master.cget('background'),
            state='disabled')
        self.bind("<1>", lambda event: self.focus_set())
        return None

    def insert(self, *args, **kwargs):
        self.config(state='normal')
        # By calling super().insert, we can call the insert() method
        # of the regular Text function to insert text into our ReadOnly
        # widget
        super().insert(*args, **kwargs)
        self.config(state='disabled')
        return None


    def delete(self, *args, **kwargs):
        self.config(state='normal')
        super().delete(*args, **kwargs)
        self.config(state='disabled')
        return None
