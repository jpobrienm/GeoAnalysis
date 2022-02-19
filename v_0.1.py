import os
import rasterio
from rasterio.enums import Resampling
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt



class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GeoAnalysis")


class Metadata:
    def __init__(self, path):
        self.path = path
        self.months = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        self.pi_files = [os.path.join(self.path, "Pi", "Pi_" + i + ".tif") for i in self.months]
        self.etr_files = [os.path.join(self.path, "Etr", "ETR_" + i + ".tif") for i in self.months]
        self.cc_file = os.path.join(self.path, "Cc", "Cc.tif")
        self.pm_file = os.path.join(self.path, "Pm", "Pm.tif")


class Raster:

    def __init__(self, route, cellsize):
        self.route = route
        self.cellSize = cellsize

    def raster_array(self, returnmeta):

        with rasterio.open(self.route) as src:
            meta = src.profile
            xupscale = abs(meta["transform"][0] / self.cellSize)
            yupscale = abs(meta["transform"][4] / self.cellSize)
            affine = meta['transform']

            meta.update(
                width=meta['width'] * xupscale,
                height=meta['height'] * yupscale,
                transform=rasterio.Affine(self.cellSize * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cellSize * abs(affine[4]) / affine[4], affine[5])
            )

            thumbnail = src.read(1, out_shape=(1, int(src.height * yupscale), int(src.width * xupscale)))
            thumbnail[thumbnail < 0] = np.nan

        if returnmeta:
            return thumbnail, meta
        else:
            return thumbnail


class GeoAnalysis:

    def etp(self, t, ps):
        return (8.10 + 0.46 * t) * ps

    def hd(self, pm, pi, hsi):
        output = np.zeros(min(hsi.shape, pm.shape, pi.shape)) * np.nan
        print(output.shape)
        for i in range(len(output)):
            for j in range(len(output[i])):
                output[i][j] = hsi[i][j] + pi[i][j] - pm[i][j]
        return output

    def hsf(self, pm, cc, etr, hd):
        output = np.zeros(min(hd.shape, pm.shape, etr.shape, cc.shape)) * np.nan
        for i in range(len(output)):
            for j in range(len(output[i])):
                if hd[i][j] + pm[i][j] - etr[i][j] < cc[i][j]:
                    output[i][j] = hd[i][j] + pm[i][j] - etr[i][j]
                elif hd[i][j] + pm[i][j] - etr[i][j] >= cc[i][j]:
                    output[i][j] = cc[i][j]
        return output

    def rp(self, pi, etr, hsi, hsf):
        output = np.zeros(min(pi.shape, hsi.shape, hsf.shape, etr.shape)) * np.nan
        for i in range(len(output)):
            for j in range(len(output[i])):
                if pi[i][j] + hsi[i][j] - hsf[i][j] - etr[i][j] <= 0:
                    output[i][j] = 0
                elif pi[i][j] + hsi[i][j] - hsf[i][j] - etr[i][j] > 0:
                    output[i][j] = pi[i][j] + hsi[i][j] - hsf[i][j] - etr[i][j]
        return output


class ArrayTools:
    def __init__(self, array):
        self.array = array

    def data_fixer(self, n_std):
        mean = np.mean(self.array)
        std = np.std(self.array)
        outliers = self.array[self.array > mean + n_std * std]
        return outliers

    def array_avg(self):
        valuescount = 0
        values_sum = 0
        for i in range(len(self.array)):
            for j in range(len(self.array[i])):
                if not np.isnan(self.array[i][j]):
                    valuescount += 1
                    values_sum += self.array[i][j]
        return values_sum / valuescount

    def write_tif(self, profile, path, target_folder, month):
        try:
            os.remove(os.path.join(path, target_folder, target_folder + '_' + month + ".tif"))
        except:
            print("error")
        with rasterio.open(os.path.join(path, target_folder, target_folder + "_" + month + ".tif"), 'w',
                           **profile) as dst:
            dst.write(self.array, 1)


metadata = Metadata(r"C:\Users\jpobr\Desktop\ivancho")
months = metadata.months
pm_file = metadata.pm_file
cc_file = metadata.cc_file
pi_files = metadata.pi_files
etr_files = metadata.etr_files

temps_high = [30.2, 31, 30.3, 28.2, 27.2, 26.1, 26.1, 27.5, 28.6, 28.4, 28.5, 29.2]
temps_low = [19.5, 20.6, 20.9, 19.7, 18.5, 17.7, 17.1, 17.8, 18.2, 19.0, 19.2, 18.7]
avg_temps = [(temps_high[i] + temps_low[i]) / 2 for i in range(len(temps_high))]
daylight_hrs = [11.9, 12, 12.1, 12.2, 12.3, 12.4, 12.3, 12.3, 12.1, 12.0, 11.9, 11.9]
insolation_hrs = [7.7, 9.6, 10.1, 8.5, 8.3, 9.4, 9.9, 10.2, 9.3, 9.0, 9.3, 9.6]

cell_size = 12.5
hsi_array = []
rp_annual = []
meta = ''

pi_arrays = [Raster(pi_files[i], cell_size).raster_array(False) for i in range(len(months))]
pi_avgs = [ArrayTools(i).array_avg() for i in pi_arrays]
months_above_etp = []

for i in range(len(months)):
    etp = GeoAnalysis().etp(avg_temps[i], daylight_hrs[i])
    if pi_avgs[i] > etp:
        months_above_etp.append(i)

max_month = pi_avgs.index(max(pi_avgs))

for i in range(len(months)):

    pm_array, meta = Raster(pm_file, cell_size).raster_array(True)
    cc_array = Raster(cc_file, cell_size).raster_array(False)
    etr_array = Raster(etr_files[(max_month + i) % 12], cell_size).raster_array(False)

    if i == 0:
        hsi_array = cc_array

    hd_array = GeoAnalysis().hd(pm_array, pi_arrays[(max_month + i) % 12], hsi_array)
    ArrayTools(hd_array).write_tif(meta, r"C:\Users\jpobr\Desktop\ivancho", "Hd", months[(max_month + i) % 12])
    hsf_array = GeoAnalysis().hsf(pm_array, cc_array, etr_array, hd_array)
    ArrayTools(hsf_array).write_tif(meta, r"C:\Users\jpobr\Desktop\ivancho", "Hsf", months[(max_month + i) % 12])
    rp_array = GeoAnalysis().rp(pi_arrays[(max_month + i) % 12], etr_array, hsi_array, hsf_array)
    if i == 0:
        rp_annual = rp_array
    else:
        rp_annual += rp_array
    ArrayTools(hsi_array).write_tif(meta, r"C:\Users\jpobr\Desktop\ivancho", "Hsi", months[(max_month + i) % 12])
    hsi_array = hsf_array
    ArrayTools(rp_array).write_tif(meta, r"C:\Users\jpobr\Desktop\ivancho", "Rp", months[(max_month + i) % 12])
    print(months[(max_month + i) % 12])

ArrayTools(rp_annual).write_tif(meta, r"C:\Users\jpobr\Desktop\ivancho", "Rp", "anual")

