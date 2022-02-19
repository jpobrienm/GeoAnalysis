import rasterio
from rasterio.enums import Resampling
import numpy as np
import os


class Raster:

    def __init__(self, path, cellsize):
        self.path = path
        self.cellSize = cellsize

    def raster_array(self, returnmeta):

        with rasterio.open(self.path) as src:
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

            thumbnail = src.read(1, out_shape=(1, int(src.height * yupscale), int(src.width * xupscale)),
                                 resampling=Resampling.nearest).astype('float64')

            thumbnail[thumbnail < -1e-5] = np.nan

        if returnmeta:
            return thumbnail, meta
        else:
            return thumbnail

    def clip2(self, path_toclip):

        with rasterio.open(self.path) as src, rasterio.open(path_toclip) as srctoclip:
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

            meta1 = srctoclip.profile
            xupscale = abs(meta["transform"][0] / self.cellSize)
            yupscale = abs(meta["transform"][4] / self.cellSize)
            affine = meta['transform']

            meta1.update(
                width=meta['width'] * xupscale,
                height=meta['height'] * yupscale,
                transform=rasterio.Affine(self.cellSize * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cellSize * abs(affine[4]) / affine[4], affine[5])
            )

            thumbnail = src.read(1, out_shape=(1, int(src.height), int(src.width))).astype('float64')
            thumbnail[thumbnail < -1e-5] = np.nan
            thumbnailtoclip = srctoclip.read(1, out_shape=(1, int(srctoclip.height), int(srctoclip.width))).astype('float64')
            thumbnailtoclip[thumbnailtoclip < -1e-5] = np.nan
            clippedthumbnail = np.zeros(np.shape(thumbnail)) * np.nan
            flag = False
            for i in range(len(thumbnail)):
                for j in range(len(thumbnail[i])):
                    if thumbnail[i][j] >= 0:
                        coords = src.xy(i, j)
                        try:
                            index = srctoclip.index(coords[0], coords[1])
                            clippedthumbnail[i][j] = thumbnailtoclip[index[0]][index[1]]
                        except:
                            flag = True
            if flag:
                print('error in coordinates')
        return clippedthumbnail

    def clip(self, path_toclip):

        with rasterio.open(self.path) as src, rasterio.open(path_toclip) as srctoclip:
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

            meta1 = srctoclip.profile
            xupscale = abs(meta["transform"][0] / self.cellSize)
            yupscale = abs(meta["transform"][4] / self.cellSize)
            affine = meta['transform']

            meta1.update(
                width=meta['width'] * xupscale,
                height=meta['height'] * yupscale,
                transform=rasterio.Affine(self.cellSize * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cellSize * abs(affine[4]) / affine[4], affine[5])
            )

            thumbnail = src.read(1, out_shape=(1, int(src.height), int(src.width))).astype('float64')
            thumbnail[thumbnail < -1e5] = np.nan
            thumbnailtoclip = srctoclip.read(1, out_shape=(1, int(srctoclip.height), int(srctoclip.width))).astype('float64')
            thumbnailtoclip[thumbnailtoclip < -1e5] = np.nan

            top_left_thumbnail = src.xy(0, 0)
            index = srctoclip.index(top_left_thumbnail[0], top_left_thumbnail[1])
            clipped_thumbnail = thumbnailtoclip[index[0]: index[0] + len(thumbnail), index[1]:index[1] + len(thumbnail[0])]
            clipped_thumbnail[np.isnan(thumbnail)] = np.nan

        return clipped_thumbnail


class ArrayTools:
    def __init__(self, array):
        self.array = array

    def data_fixer(self, n_std):
        mean = np.mean(self.array)
        std = np.std(self.array)
        outliers = self.array[self.array > mean + n_std * std]
        return outliers

    def write_tif(self, profile, path, target_folder, month):
        with rasterio.open(os.path.join(path, target_folder, target_folder + '_' + month + ".tif"), 'w',
                           **profile) as dst:
            dst.write(self.array, 1)


def write_tif(array, profile, path, target_folder, month):
    with rasterio.Env():
        profile_ = profile
        profile.update(
            dtype=rasterio.float64,
            count=1,
            compress='lzw')
    with rasterio.open(os.path.join(path, target_folder, target_folder + '_' + month + ".tif"), 'w',
                       **profile_) as dst:
        dst.write(array.astype(rasterio.float64), 1)


def etp(t, ps):
    return (np.full(t.shape, 8.10) + 0.46 * t) * ps


def etp_thorn(t_months, n_hours, days_month):
    indice_calor = np.power(t_months[0].copy() / 5, 1.514)
    etp_arr = []
    for i in range(1, len(t_months)):
        indice_calor += np.power(t_months[i] / 5, 1.514)

    a = 675 * (10 ** -9) * np.power(indice_calor, 3) - 771 * (10 ** -7) * np.power(indice_calor, 2) + 1792 * (10 ** -5) \
        * indice_calor + np.full(indice_calor.shape, 0.49239)

    for i in range(len(t_months)):
        base = np.divide(10 * t_months[i].copy(), indice_calor)
        etp_arr.append(16 * np.power(base, a) * (n_hours * days_month[i] / 360))

    return etp_arr


def etp_thorn_escalar(t_months, n_hours, days_month):
    indice_calor = 0
    etp_arr = []
    for i in range(len(t_months)):
        t = np.nanmean(t_months[i])
        indice_calor += (t/5) ** 1.514
    a = 675e-9 * (indice_calor ** 3) - 771e-7 * (indice_calor ** 2) + 1792e-5 * indice_calor + 0.49239
    for i in range(len(t_months)):
        etp_arr.append(16 * np.power((10 * t_months[i] / indice_calor), a) * (n_hours * days_month[i] / 360))
    return etp_arr


def ret(p, cfo):
    output = np.zeros(p.shape) * np.nan
    for i in range(len(p)):
        for j in range(len(p[i])):
            if p[i][j] <= 5:
                output[i][j] = p[i][j]
            elif cfo[i][j] * p[i][j] >= 5:
                output[i][j] = cfo[i][j] * p[i][j]
            elif p[i][j] > 5 and cfo[i][j] * p[i][j] < 5:
                output[i][j] = 5
    output[output < 0] = 0
    return output


def ret_const(p, cfo):
    size = np.min(p.shape, cfo.shape)
    print(size)
    output = np.zeros(p.shape) * np.nan
    for i in range(size[0] - 1):
        for j in range(size[1] - 1):
            if p[i][j] <= 5:
                output[i][j] = p[i][j]
            elif cfo * p[i][j] >= 5:
                output[i][j] = cfo * p[i][j]
            elif p[i][j] > 5 and cfo * p[i][j] < 5:
                output[i][j] = 5
    output[output < 0] = 0
    return output


def ret2(p, cfo):
    size = np.min(p.shape, cfo.shape)
    p_cut = p.copy()[:size[0], :size[1]]
    cfo_cut = cfo.copy()[:size[0], :size[1]]
    product = np.multiply(p_cut, cfo_cut)
    p_cut[p_cut <= 5] = -999


def kp2(slope):
    output = slope.copy()
    output[slope <= 93] = 0.06
    output[slope <= 7] = 0.1
    output[slope <= 2] = 0.15
    output[slope <= 0.4] = 0.2
    output[slope <= 0.06] = 0.3
    return output


def kp(slope):
    output = slope.copy()
    for i in range(len(slope)):
        for j in range(len(slope[0])):
            if slope[i][j] <= 0.06:
                output[i][j] = 0.3
            elif slope[i][j] <= 0.4:
                output[i][j] = 0.2
            elif slope[i][j] <= 2:
                output[i][j] = 0.15
            elif slope[i][j] <= 7:
                output[i][j] = 0.1
            else:
                output[i][j] = 0.06
    return output


def ci(kp_input, kv_input, kfc_input):
    size = min(kp_input.shape, kv_input.shape, kfc_input.shape)
    output = kp_input[:size[0], :size[1]] + kv_input[:size[0], :size[1]] + kfc_input[:size[0], :size[1]]
    output[output < 0] = 0
    output[output > 1] = 1
    return output


def pi(ci_input, p_input, ret_input):
    size = min(p_input.shape, ci_input.shape, ret_input.shape)
    output = np.multiply(ci_input[:size[0], :size[1]], p_input[:size[0], :size[1]] - ret_input[:size[0], :size[1]])
    output[output < 0] = 0
    return output


def esc(p_input, ret_input, pi_input):
    size = min(p_input.shape, ret_input.shape, pi_input.shape)
    return p_input[:size[0], :size[1]] - ret_input[:size[0], :size[1]] - pi_input[:size[0], :size[1]]


def kv(cov):
    output = cov.copy()


def c1(hsi_input, pm_input, pi_input, cc_input):
    size = min(hsi_input.shape, pm_input.shape, pi_input.shape, cc_input.shape)
    output = np.divide(hsi_input[:size[0], :size[1]] - pm_input[:size[0], :size[1]] + pi_input[:size[0], :size[1]],
                       cc_input[:size[0], :size[1]] - pm_input[:size[0], :size[1]] + 0.00000000001)
    output[output < 0] = 0
    output[output > 1] = 1
    return output


def c2(hsi_input, pm_input, pi_input, c1_input, cc_input, etp_input):
    size = min(hsi_input.shape, pm_input.shape, pi_input.shape, c1_input.shape, cc_input.shape, cc_input.shape, etp_input.shape)
    etr1 = np.multiply(c1_input, etp_input)
    output = np.divide(hsi_input[:size[0], :size[1]] - pm_input[:size[0], :size[1]] + pi_input[:size[0], :size[1]] -
                       etr1, cc_input[:size[0], :size[1]] - pm_input[:size[0], :size[1]] + 0.0000001)
    output[output < 0] = 0
    output[output > 1] = 1
    return output


def etpr_alt(c1_input, c2_input, etp_input):
    size = min(c1_input.shape, c2_input.shape, etp_input.shape)
    output = np.multiply(etp_input[:size[0], :size[1]], (c1_input[:size[0], :size[1]] + c2_input[:size[0], :size[1]]) / 2)
    output[output < 0] = 0
    return output


def hd(pm_input, pi_input, hsi_input):
    size = min(hsi_input.shape, pm_input.shape, pi_input.shape)
    output = hsi_input[:size[0], :size[1]] + pi_input[:size[0], :size[1]] - pm_input[:size[0], :size[1]]
    output[output < 0] = 0
    return output


def etr(c1, c2, hd, etp):
    size = min(c1.shape, c2.shape, hd.shape, etp.shape)
    output = np.multiply((c1[:size[0], : size[1]] + c2[:size[0], : size[1]]) / 2, etp[:size[0], : size[1]])
    output = np.minimum(output, hd[:size[0], : size[1]])
    output[output < 0] = 0
    return output


def hsf(pm_input, cc_input, etr_input, hd_input):
    size = min(hd_input.shape, pm_input.shape, etr_input.shape, cc_input.shape)
    output = np.empty(size)
    for i in range(size[0]):
        output[i] = np.minimum(hd_input[i][:size[1]] + pm_input[i][:size[1]] - etr_input[i][:size[1]],
                               cc_input[i][:size[1]])
    output[output < 0] = 0
    return output


def rp(pi_input, etr_input, hsi_input, hsf_input):
    size = min(pi_input.shape, hsi_input.shape, hsf_input.shape, etr_input.shape)
    output = pi_input[:size[0], :size[1]] + hsi_input[:size[0], :size[1]] - hsf_input[:size[0], :size[1]] - \
                      etr_input[:size[0], :size[1]]
    output[output < 0] = 0
    return output
