import os
import gdal
import numpy as np


def raster_to_array(route, band, return_gt, return_proj):
    data = gdal.Open(route)
    gt = data.GetGeoTransform()
    proj = data.GetProjection()
    band = data.GetRasterBand(band)
    array = band.ReadAsArray()
    new_array = np.zeros(array.shape) * np.nan
    for i in range(len(array)):
        for j in range(len(array[i])):
            if array[i][j] > 0:
                new_array[i][j] = array[i][j]
    if return_gt:
        if return_proj:
            return new_array, gt, proj
        else:
            return new_array, gt
    else:
        return new_array


def array_to_raster(array, gt, proj, name):

    driver = gdal.GetDriverByName("Gtiff")
    driver.Register()
    outds = driver.Create(name+".tif", xsize=array.shape[1], ysize=array.shape[0], bands=1, eType=gdal.GDT_CFloat64)
    outds.SetGeoTransform(gt)
    outds.SetProjection(proj)
    outband = outds.GetRasterBand(1)
    outband.WriteArray(array)
    outband.SetNoDataValue(np.nan)
    outband.FlushCache()
    outband = None
    outds = None

    return outband, outds


def ret(p, cfo):
    Ret = np.zeros(p.shape) * np.nan
    for i in range(len(p)):
        for j in range(len(p[i])):
            if p[i][j] <= 5:
                Ret[i][j] = p[i][j]
            elif cfo[i][j] * p[i][j] >= 5:
                Ret[i][j] = cfo[i][j] * p[i][j]
            elif p[i][j] > 5 and cfo[i][j] * p[i][j] < 5:
                Ret[i][j] = 5
    return Ret


def kfc(fc):
    Kfc = np.zeros(fc.shape) * np.nan
    for i in range(len(fc)):
        for j in range(len(fc[i])):
            if fc[i][j] < 16:
                Kfc[i][j] = (0.0148/16) * fc[i][j]
            elif 16 <= fc[i][j] <= 1568:
                Kfc[i][j] = 0.267 * np.log(fc[i][j]) - 0.000154 * fc[i][j] - 0.723
            else:
                Kfc[i][j] = 1
    return Kfc


def ci(kp, kv, kfc):
    Ci = np.zeros(kp.shape) * np.nan
    for i in range(len(kp)):
        for j in range(len(kp[i])):
            if kp[i][j] + kv[i][j] + kfc[i][j] > 1:
                Ci[i][j] = 1
            elif kp[i][j] + kv[i][j] + kfc[i][j] <= 1:
                Ci[i][j] = kp[i][j] + kv[i][j] + kfc[i][j]
    return Ci


def pi(ci, p, ret):
    Pi = np.zeros(min(p.shape, ci.shape, ret.shape)) * np.nan
    for i in range(len(Pi)):
        for j in range(len(Pi[i])):
            Pi[i][j] = ci[i][j] * (p[i][j]-ret[i][j])
    return Pi


def esc(p, ret, pi):
    Esc = np.zeros(min(p.shape, ret.shape, pi.shape)) * np.nan
    for i in range(len(Esc)):
        for j in range(len(Esc[i])):
            Esc[i][j] = p[i][j] - ret[i][j] - pi[i][j]
    return Esc


def etpr(hs, pm, et, cc):
    Etpr = np.zeros(hs.shape) * np.nan
    for i in range(len(hs)):
        for j in range(len(hs[i])):
            Etpr[i][j] = (hs[i][j] - pm[i][j]) * (et[i][j])/(cc[i][j]-pm[i][j])
    return Etpr


def etp(t, ps):
    Etp = np.zeros(t.shape) * np.nan
    for i in range(len(t)):
        for j in range(len(t[i])):
            Etp[i][j] = (8.10 + 0.46*t[i][j])*ps[i][j]
    return Etp


def porcent_vol(porcent_suelo, densidad_ap):
    Porcent_vol = np.zeros(porcent_suelo.shape) * np.nan
    for i in range(len(porcent_suelo)):
        for j in range(len(porcent_suelo[i])):
            Porcent_vol[i][j] = porcent_suelo[i][j] * densidad_ap[i][j]
    return Porcent_vol


def mm_agua(humedad_vol, profundidad):
    mm_Agua = np.zeros(humedad_vol.shape) * np.nan
    for i in range(len(humedad_vol)):
        for j in range(len(humedad_vol[i])):
            mm_Agua[i][j] = humedad_vol[i][j] * profundidad[i][j]
    return mm_Agua


def c1(hsi, pm, pi, cc):
    C1 = np.zeros(hsi.shape) * np.nan
    for i in range(len(hsi)):
        for j in range(len(hsi[i])):
            if cc[i][j] - pm[i][j] == 0:
                C1[i][j] = 0
            else:
                C1[i][j] = (hsi[i][j] - pm[i][j] + pi[i][j]) / (cc[i][j] - pm[i][j])
    return C1


def c2(hsi, pm, pi, c1, cc, etp):
    C2 = np.zeros(hsi.shape) * np.nan
    for i in range(len(hsi)):
        for j in range(len(hsi[i])):
            if cc[i][j] - pm[i][j] == 0:
                C2[i][j] = 0
            else:
                Etr1 = c1[i][j] * etp[i][j]
                C2[i][j] = (hsi[i][j] - pm[i][j] + pi[i][j] - Etr1[i][j])/(cc[i][j] - pm[i][j])
    return C2


def etpr_alt(c1, c2, etp):
    Etpr = np.zeros(c1.shape) * np.nan
    for i in range(len(Etpr)):
        for j in range(len(Etpr[i])):
            Etpr[i][j] = etp[i][j] * ((c1[i][j] + c2[i][j])/2)
    return Etpr


def hd(hsi, pm, pi):
    Hd = np.zeros(hsi.shape) * np.nan
    for i in range(len(Hd)):
        for j in range(len(Hd[i])):
            Hd[i][j] = hsi[i][j] + pi[i][j] - pm[i][j]
    return Hd


def etr(c1, c2, hd, etp):
    Etr = np.zeros(c1.shape) * np.nan
    for i in range(len(Etr)):
        for j in range(len(Etr[i])):
            if etp[i][j] * ((c1[i][j] + c2[i][j])/2) <= hd[i][j]:
                Etr[i][j] = etp[i][j] * ((c1[i][j] + c2[i][j])/2)
            else:
                Etr[i][j] = hd[i][j]
    return Etr


def hsf(hd, pm, etr, cc):
    Hsf = np.zeros(hd.shape) * np.nan
    for i in range(len(Hsf)):
        for j in range(len(Hsf[i])):
            if hd[i][j] + pm[i][j] -etr[i][j] < cc[i][j]:
                Hsf[i][j] = hd[i][j] + pm[i][j] -etr[i][j]
            else:
                Hsf[i][j] = cc[i][j]
    return Hsf


def rp(pi, hsi, hsf, etr):
    Rp = np.zeros(min(pi.shape, hsi.shape, hsf.shape, etr.shape)) * np.nan
    for i in range(len(Rp)):
        for j in range(len(Rp[i])):
            if pi[i][j] + hsi[i][j] - hsf[i][j] - etr[i][j] < 0:
                Rp[i][j] = 0
            elif pi[i][j] + hsi[i][j] - hsf[i][j] - etr[i][j] > 0:
                Rp[i][j] = pi[i][j] + hsi[i][j] - hsf[i][j] - etr[i][j]
    return Rp


def dcc(cc, hsf):
    Dcc = np.zeros(min(cc.shape, hsf.shape)) * np.nan
    for i in range(len(Dcc)):
        for j in range(len(Dcc[i])):
            Dcc[i][j] = cc[i][j] - hsf[i][j]
    return Dcc


def nr(dcc, etr, etp):
    Nr = np.zeros(min(dcc.shape, etr.shape, etp.shape)) * np.nan
    for i in range(len(Nr)):
        for j in range(len(Nr[i])):
            Nr[i][j] = dcc[i][j] - etr[i][j] + etp[i][j]
    return Nr

