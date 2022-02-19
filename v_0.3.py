import numpy as np
import geoTools as gtls
import tkinter as tk
from tkinter import *
from tkinter import filedialog
import os
import matplotlib.pyplot as plt

child_dirs = ['Cc', 'Kfc', 'Kv', 'P', 'Pm', 'Slope', 'T']
months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre"]
n_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
supported_files = ['.tif']


def plot(array, title=''):
    plt.imshow(array)
    plt.title(title)
    plt.show()

class GUI:

    def __init__(self):

        # Window
        self.root = tk.Tk()
        self.root.title("GeoAnalysis")

        # Menu
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.filemenu = Menu(self.menubar)
        self.filemenu.add_command(label='Nuevo', command=self.new_project)
        self.filemenu.add_command(label='Abrir', command=self.open_project)
        self.menubar.add_cascade(label="Archivo", menu=self.filemenu)

        # Path
        self.path_root = ""

        # File list
        self.listbox = Listbox(self.root, height=25, width=25)
        self.listbox.grid(row=1, column=0)

        self.root.mainloop()

    def new_project(self):
        root = filedialog.askdirectory(title="Seleccione Una carpeta de proyecto")
        self.path_root = root
        for child in child_dirs:
            os.makedirs(os.path.join(root, child))

    def open_project(self):
        root = filedialog.askdirectory(title="Seleccione Una carpeta de proyecto")


root = r'C:\Users\jpobr\Desktop\Recarga_2.0'
initial = 10
target = r'C:\Users\jpobr\Desktop\Rp_sebastian'
cell = 12.5

kv, meta = gtls.Raster(os.path.join(root, 'kv.tif'), cell).raster_array(True)
kp = gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'kp.tif'))
kfc = gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'kfc.tif'))
cfo = gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'Cfo.tif'))
cc = gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'CC.tif'))
pm = gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'PM.tif'))
t = []

for i in range(len(months)):
    t.append(gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'T', 'T' + '_' + months[(initial + i) % 12] + '.tif')))

etp_arr = gtls.etp_thorn(t, 12, n_days)
etp_esc = gtls.etp_thorn_escalar(t, 12, n_days)
for i in range(len(etp_arr)):
    print(gtls.ArrayTools(etp_esc[i]).array_avg(), gtls.ArrayTools(etp_arr[i]).array_avg())

ci = gtls.ci(kp, kv, kfc)
hsi = cc.copy()
rp_anual = []

for i in range(initial, initial + len(months)):
    p = gtls.Raster(os.path.join(root, 'kv.tif'), cell).clip(os.path.join(root, 'P', 'P' + '_' + months[i % 12] + '.tif'))
    gtls.ArrayTools(p).write_tif(meta, target, 'P', months[i % 12])
    ret = gtls.ret(p, cfo)
    gtls.ArrayTools(ret).write_tif(meta, target, 'Ret', months[i % 12])
    pi = gtls.pi(ci, p, ret)
    gtls.ArrayTools(pi).write_tif(meta, target, 'Pi', months[i % 12])
    c1 = gtls.c1(hsi, pm, pi, cc)
    gtls.ArrayTools(c1).write_tif(meta, target, 'C1', months[i % 12])
    etp = etp_arr[i % 12]
    gtls.ArrayTools(etp).write_tif(meta, target, 'Etp', months[i % 12])
    c2 = gtls.c2(hsi, pm, pi, c1, cc, etp)
    gtls.ArrayTools(c2).write_tif(meta, target, 'C2', months[i % 12])
    hd = gtls.hd(pm, pi, hsi)
    gtls.ArrayTools(hd).write_tif(meta, target, 'Hd', months[i % 12])
    etr = gtls.etr(c1, c2, hd, etp)
    gtls.ArrayTools(etr).write_tif(meta, target, 'Etr', months[i % 12])
    hsf = gtls.hsf(pm, cc, etr, hd)
    gtls.ArrayTools(hsf).write_tif(meta, target, 'Hsf', months[i % 12])
    gtls.ArrayTools(hsi).write_tif(meta, target, 'Hsi', months[i % 12])
    hsi = hsf.copy()
    rp = gtls.rp(pi, etr, hsi, hsf)
    if i == initial:
        rp_anual = rp
    else:
        rp_anual += rp
    gtls.ArrayTools(rp).write_tif(meta, target, 'Rp', months[i % 12])
gtls.ArrayTools(rp_anual).write_tif(meta, target, 'Rp', 'anual')






