import tkinter as tk
import time

class SplashScreen(tk.Frame):
    def __init__(self, master, imageFilepath=None, imageData=None,
        sleepTime=1):
        super().__init__()
        if imageData and imageFilepath:
            err = 'SplashScreen uses only one of filepath or data'
            raise ValueError(err)
        if imageData:
            self.image = tk.PhotoImage(data=imageData)
        elif imageFilepath:
            self.image = tk.PhotoImage(file=imageFilepath)
        else:
            raise ValueError('SplashScreen requires filepath or data')
        self.pack(side='top', fill='both', expand='yes')
        self.screenWidth = self.master.winfo_screenwidth()
        self.screenHeight = self.master.winfo_screenheight()
        self.imageWidth = self.image.width()
        self.imageHeight = self.image.height()
        self.splashPosX = (self.screenWidth//2) - (self.imageWidth//2)
        self.splashPosY = (self.screenHeight//2) - (self.imageHeight//2)

        self.master.withdraw()
        self.splash = tk.Toplevel()
        self.splash.overrideredirect(True)
        self.splash.geometry('+{:d}+{:d}'.format(self.splashPosX,
            self.splashPosY))
        tk.Label(self.splash,image=self.image,cursor='watch').pack()
        self.splash.update()
        time.sleep(sleepTime)

        self.splash.destroy()
        self.master.deiconify()

        return None
