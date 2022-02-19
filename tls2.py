import numpy as np
import rasterio


def rastertoarray(raster):
    with rasterio.open(raster) as src:
        thumbnail = src.read(1, out_shape=(1, int(src.height), int(src.width)))
        thumbnail[thumbnail < 0] = np.nan
    return thumbnail


def getmeta(raster):
    with rasterio.open(raster) as src:
        return src.profile


def clip(raster, rastertoclip):
    with rasterio.open(raster) as src, rasterio.open(rastertoclip) as srctoclip:
        thumbnail = src.read(1, out_shape=(1, int(src.height), int(src.width)))
        thumbnailtoclip = srctoclip.read(1, out_shape=(1, int(srctoclip.height), int(srctoclip.width)))
        clippedthumbnail = np.zeros(np.shape(thumbnail)) * np.nan
        for i in range(len(thumbnail)):
            for j in range(len(thumbnail[i])):
                if thumbnail[i][j] >= 0:
                    coords = src.xy(i, j)
                    try:
                        index = srctoclip.index(coords[0], coords[1])
                        clippedthumbnail[i][j] = thumbnailtoclip[index[0]][index[1]]
                    except:
                        print("error in coordinates")

    return clippedthumbnail


def overlap(smallraster, bigraster):
    with rasterio.open(smallraster) as src, rasterio.open(bigraster) as srcbg:
        smallthumb = src.read(1, out_shape=(1, int(src.height), int(src.width)))
        bigthumb = srcbg.read(1, out_shape=(1, int(srcbg.height), int(srcbg.width)))
        for i in range(len(smallthumb)):
            for j in range(len(smallthumb[i])):
                coords = src.xy(i, j)
                try:
                    index = srcbg.index(coords[0], coords[1])
                    bigthumb[index[0]][index[1]] = smallthumb[i][j]
                except:
                    print("bad coordinates")
    return bigthumb

def array_fixer(array):
    print(np.nanmean(array))


def arrayavg(array):
    valuescount = 0
    values_sum = 0
    for i in range(len(array)):
        for j in range(len(array[i])):
            if not np.isnan(array[i][j]):
                valuescount += 1
                values_sum += array[i][j]
    return values_sum/valuescount


def etp(t, ps):
    return (8.10 + 0.46 * t) * ps


def hd(hsi, pm, pi):
    hd_array = np.zeros(min(hsi.shape, pm.shape, pi.shape)) * np.nan
    for i in range(len(hd_array)):
        for j in range(len(hd_array[i])):
            hd_array[i][j] = hsi[i][j] + pi[i][j] - pm[i][j]
    return hd_array


def hsf(hd, pm, etr, cc):
    hsf_array = np.zeros(min(hd.shape, pm.shape, etr.shape, cc.shape)) * np.nan
    for i in range(len(hsf_array)):
        for j in range(len(hsf_array[i])):
            if hd[i][j] + pm[i][j] - etr[i][j] < cc[i][j]:
                hsf_array[i][j] = hd[i][j] + pm[i][j] - etr[i][j]
            elif hd[i][j] + pm[i][j] - etr[i][j] >= cc[i][j]:
                hsf_array[i][j] = cc[i][j]
    return hsf_array
