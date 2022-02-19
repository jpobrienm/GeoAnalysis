import numpy as np
import geoTools as gtls
import tkinter as tk
from tkinter import *
from tkinter import filedialog
import os
import matplotlib.pyplot as plt

def plot(array, title=''):
    plt.imshow(array)
    plt.title(title)
    plt.show()


child_dirs = ['Cc', 'Kfc', 'Kv', 'P', 'Pm', 'Slope', 'T']
months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
n_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
supported_files = ['.tif']

root = r'C:\Users\jpobr\Desktop\geotool\proyecto'
fix = '_fix'
cell = 12.5
base_raster_path = os.path.join(root, 'Slope', 'Pendientes.tif')

cfo = 0.12
slope, meta = gtls.Raster(os.path.join(root, 'Slope', 'Pendientes.tif'), cell).raster_array(True)
kp = gtls.kp(slope)
gtls.ArrayTools(kp).write_tif(meta, root, 'Kp' + fix, '')
kv = gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'Kv', 'KV.tif'))
gtls.ArrayTools(kv).write_tif(meta, root, 'Kv' + fix, '')
kfc = gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'Kfc', 'KFC.tif'))
gtls.ArrayTools(kfc).write_tif(meta, root, 'Kfc' + fix, '')
cc = gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'Cc', 'CC.tif'))
gtls.ArrayTools(cc).write_tif(meta, root, 'Cc' + fix, '')
pm = gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'Pm', 'PM.tif'))
gtls.ArrayTools(pm).write_tif(meta, root, 'Pm' + fix, '')
ci = gtls.ci(kp, kv, kfc)
gtls.ArrayTools(ci).write_tif(meta, root, 'Ci' + fix, '')

t = []
for i in range(len(months)):
    t.append(gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'T', 'T' + months[i] + '.tif')))

etp_arr = gtls.etp_thorn(t, 12, n_days)
max_month = 'Septiembre'
initial = 9
hsi = cc.copy()
rp_anual = []

for i in range(initial, initial + len(months)):
    p = gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'P', 'P' + months[i % 12] + '.tif'))
    gtls.ArrayTools(p).write_tif(meta, root, 'P' + fix, months[i % 12])
    ret = gtls.ret(p, np.full(p.shape, cfo))
    gtls.ArrayTools(ret).write_tif(meta, root, 'Ret' + fix, months[i % 12])
    pi = gtls.pi(ci, p, ret)
    gtls.ArrayTools(pi).write_tif(meta, root, 'Pi' + fix, months[i % 12])
    t = gtls.Raster(base_raster_path, cell).clip(os.path.join(root, 'T', 'T' + months[i % 12] + '.tif'))
    gtls.ArrayTools(t).write_tif(meta, root, 'T' + fix, months[i % 12])
    etp = etp_arr[i % 12]
    gtls.ArrayTools(etp).write_tif(meta, root, 'Etp' + fix, months[i % 12])
    c1 = gtls.c1(hsi, pm, pi, cc)
    gtls.ArrayTools(c1).write_tif(meta, root, 'C1' + fix, months[i % 12])
    c2 = gtls.c2(hsi, pm, pi, c1, cc, etp)
    gtls.ArrayTools(c2).write_tif(meta, root, 'C2' + fix, months[i % 12])
    hd = gtls.hd(pm, pi, hsi)
    gtls.ArrayTools(hd).write_tif(meta, root, 'Hd' + fix, months[i % 12])
    etr = gtls.etr(c1, c2, hd, etp)
    gtls.ArrayTools(etr).write_tif(meta, root, 'Etr' + fix, months[i % 12])
    hsf = gtls.hsf(pm, cc, etr, hd)
    gtls.ArrayTools(hsf).write_tif(meta, root, 'Hsf' + fix, months[i % 12])
    rp = gtls.rp(pi, etr, hsi, hsf)
    gtls.ArrayTools(rp).write_tif(meta, root, 'Rp' + fix, months[i % 12])
    gtls.ArrayTools(hsi).write_tif(meta, root, 'Hsi' + fix, months[i % 12])
    hsi = hsf.copy()
    if i == initial:
        rp_anual = rp
    else:
        rp_anual += rp
gtls.ArrayTools(rp_anual).write_tif(meta, root, 'Rp' + fix, 'anual')
rp_avg = np.divide(rp_anual.copy(), 12)
gtls.ArrayTools(rp_avg).write_tif(meta, root, 'Rp' + fix, 'avg')
