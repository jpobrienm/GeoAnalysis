import tkinter
import numpy as np
import geoTools as gtls
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
import os
import matplotlib.pyplot as plt


child_dirs = ['Cc', 'Cfo', 'Kfc', 'Kp', 'Kv', 'P', 'Pm', 'Slope', 'T']
operations = ['C1', 'C2', 'Cc', 'Ci', 'Etp', 'Etr', 'Hd', 'Hsf', 'Hsi', 'Kfc', 'Kp', 'Kv', 'P', 'Pi', 'Pm', 'Ret', 'Rp'
              'Slope', 'T']
months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre"]
n_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
supported_files = ['.tif']


class GUI:

    def __init__(self):

        # Window
        self.root = tk.Tk()
        self.root.title("GeoAnalysis")
        self.entry_name = None
        self.new_window = None

        # Menu
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.filemenu = Menu(self.menubar)
        self.filemenu.add_command(label='Nuevo', command=self.new_project)
        self.filemenu.add_command(label='Abrir', command=self.open_project)
        self.menubar.add_cascade(label="Archivo", menu=self.filemenu)

        # Path
        self.path_root = ""

        #

        # Combobox
        self.combo = ttk.Combobox(self.root, state='readonly')
        self.combo['values'] = operations
        self.combo.grid(row=0, column=2)
        self.combo_value = self.combo.get()

        # File list
        self.listbox = Listbox(self.root, width=25, height=25)
        self.listbox.grid(row=1, column=0)

        # Canvas
        self.canvas = Canvas(self.root, width=400, height=400, bg='white')
        self.canvas.grid(row=1, column=1)

        # Stats
        self.label = Label(self.root)
        self.label.grid(row=1, column=2)

        self.root.mainloop()

    def new_project(self):

        # New File Window
        self.new_window = Toplevel(self.root)

        # New Project Name
        label_new = Label(self.new_window, text='Nombre del proyecto')
        self.entry_name = tk.Entry(self.new_window)
        create_folder_btn = Button(self.new_window, text='Seleccionar carpeta', command=self.ask_directory)
        label_new.grid(row=0, column=0)
        self.entry_name.grid(row=0, column=1)
        create_folder_btn.grid(row=1, column=0, columnspan=2)

    def ask_directory(self):
        folder_name = self.entry_name.get()
        if len(folder_name) == 0:
            print("error")
        else:
            self.path_root = filedialog.askdirectory(title="Seleccione Una carpeta de proyecto")
            for child in child_dirs:
                os.makedirs(os.path.join(self.path_root, folder_name, child))
            self.new_window.destroy()

    def open_project(self):
        root = filedialog.askdirectory(title="Seleccione Una carpeta de proyecto")


GUI()
