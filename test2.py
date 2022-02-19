import os
import rasterio
from rasterio.enums import Resampling
import numpy as np
import tkinter as tk
import time
import matplotlib.pyplot as plt
import geoTools as gtls
from scipy import stats

path = r"C:\Users\jpobr\Desktop\ivancho"
desktop = r"C:\Users\jpobr\Desktop"

HD_base = gtls.Raster(os.path.join(desktop, "HD_ene.tif"), 50).raster_array(False)
hd = gtls.Raster(os.path.join(path, 'Hd', 'Hd_ene.tif'), 50).raster_array(False)

base_mean = np.nansum(HD_base)/HD_base[~np.isnan(HD_base)].size
base_std = np.nanstd(HD_base)
base_max = np.nanmax(HD_base)
base_min = np.nanmin(HD_base)
base_strip = strip = np.resize(HD_base.copy(), (1, HD_base.shape[0] * HD_base.shape[1]))
our_mean = np.nansum(hd)/hd[~np.isnan(hd)].size
our_std = np.nanstd(hd)
our_max = np.nanmax(hd)
our_min = np.nanmin(hd)
our_strip = np.resize(hd.copy(), (1, hd.shape[0] * hd.shape[1]))
print(base_mean, base_std, base_max, base_min, stats.mode(base_strip, nan_policy='omit'))
print(our_mean, our_std, base_max, base_min, stats.mode(our_strip, nan_policy='omit'))
