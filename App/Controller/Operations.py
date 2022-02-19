import App.Models.Raster as Raster
import App.Controller.VariableHandler as VariableHandler
import numpy as np
import rasterio
import os


class Operations:

    def __init__(self, folder_path, cell):
        self.folder_path = folder_path
        self.cell = cell
        self.initial_month = 0
        self.variableHandler = VariableHandler.VariableHandler(folder_path)
        self.months_identifiers = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        self.days_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def write_tif(self, raster, out_path, name, month):
        profile = raster.getMeta()[0]
        array = raster.rasterArray()
        with rasterio.open(os.path.join(out_path, name + month + ".tif"), 'w',
                           **profile) as dst:
            dst.write(array.astype(rasterio.float64), 1)

    def etp_thorn_escalar(self, n_hours, out_path):
        indice_calor = 0
        for month in self.months_identifiers:
            t_var = self.variableHandler.gather_var("t", month)
            t_raster = Raster.Raster(t_var, self.cell)
            t_array = t_raster.rasterArray()
            indice_calor += (t_array / 5) ** 1.514
        a = 675e-9 * (indice_calor ** 3) - 771e-7 * (indice_calor ** 2) + 1792e-5 * indice_calor + 0.49239
        for month in self.months_identifiers:
            t_var = self.variableHandler.gather_var("t", month)
            t_raster = Raster.Raster(t_var, self.cell)
            t_array = t_raster.rasterArray()
            t_profile = t_raster.getMeta()[0]
            etp = 16 * np.power((10 * t_array / indice_calor), a) * \
                  (n_hours * self.days_month[self.months_identifiers.index(month)] / 360)
            with rasterio.open(os.path.join(out_path, "etp_" + month + ".tif"), 'w',
                               **t_profile) as dst:
                dst.write(etp.astype(rasterio.float64), 1)

    def ret(self, cfo, out_path, month):
        p_var = self.variableHandler.gather_var("p", month)
        p_raster = Raster.Raster(p_var, self.cell)
        p_profile = p_raster.getMeta()[0]
        p_array = p_raster.rasterArray()
        output = np.zeros(p_array.shape) * np.nan
        for i in range(len(p_array)):
            for j in range(len(p_array[i])):
                if p_array[i][j] <= 5:
                    output[i][j] = p_array[i][j]
                elif cfo * p_array[i][j] >= 5:
                    output[i][j] = cfo * p_array[i][j]
                elif p_array[i][j] > 5 and cfo * p_array[i][j] < 5:
                    output[i][j] = 5
        output[output < 0] = 0
        with rasterio.open(os.path.join(out_path, "ret_" + month + ".tif"), 'w',
                           **p_profile) as dst:
            dst.write(output.astype(rasterio.float64), 1)

    def kp(self, out_path):
        slope_var = self.variableHandler.gather_var("pendientes")
        slope_raster = Raster.Raster(slope_var, self.cell)
        slope_profile = slope_raster.getMeta()[0]
        slope_array = slope_raster.rasterArray()
        output = slope_array.copy()
        for i in range(len(slope_array)):
            for j in range(len(slope_array[0])):
                if slope_array[i][j] <= 0.06:
                    output[i][j] = 0.3
                elif slope_array[i][j] <= 0.4:
                    output[i][j] = 0.2
                elif slope_array[i][j] <= 2:
                    output[i][j] = 0.15
                elif slope_array[i][j] <= 7:
                    output[i][j] = 0.1
                else:
                    output[i][j] = 0.06
        with rasterio.open(os.path.join(out_path, "kp.tif"), 'w',
                           **slope_profile) as dst:
            dst.write(output.astype(rasterio.float64), 1)

    def ci(self, out_path):
        kp_var = self.variableHandler.gather_var("kp")
        kv_var = self.variableHandler.gather_var("kv")
        kfc_var = self.variableHandler.gather_var("kfc")
        kp_raster = Raster.Raster(kp_var, self.cell)
        kv_raster = Raster.Raster(kv_var, self.cell)
        kfc_raster = Raster.Raster(kfc_var, self.cell)
        kp_profile = kp_raster.getMeta()[0]
        kp_array = kp_raster.rasterArray()
        kv_array = kv_raster.rasterArray()
        kfc_array = kfc_raster.rasterArray()
        ci_array = kp_array + kv_array + kfc_array
        ci_array[ci_array > 1] = 1
        ci_array[ci_array < 0] = 0
        with rasterio.open(os.path.join(out_path, "ci.tif"), 'w',
                           **kp_profile) as dst:
            dst.write(ci_array.astype(rasterio.float64), 1)

    def pi(self, out_path, month):
        ci_var = self.variableHandler.gather_var("ci")
        ci_raster = Raster.Raster(ci_var, self.cell)
        ci_profile = ci_raster.getMeta()[0]
        ci_array = ci_raster.rasterArray()
        p_var = self.variableHandler.gather_var("p", month)
        ret_var = self.variableHandler.gather_var("ret", month)
        p_array = Raster.Raster(p_var, self.cell).rasterArray()
        ret_array = Raster.Raster(ret_var, self.cell).rasterArray()
        pi_array = np.multiply(ci_array, p_array - ret_array)
        pi_array[pi_array < 0] = 0
        with rasterio.open(os.path.join(out_path, "pi_" + month + ".tif"), 'w',
                           **ci_profile) as dst:
            dst.write(pi_array.astype(rasterio.float64), 1)

    def esc(self, out_path, month):
        p_var = self.variableHandler.gather_var("p", month)
        ret_var = self.variableHandler.gather_var("ret", month)
        pi_var = self.variableHandler.gather_var("pi", month)
        p_raster = Raster.Raster(p_var, self.cell)
        p_profile = p_raster.getMeta()[0]
        p_array = Raster.Raster(p_var, self.cell).rasterArray()
        ret_array = Raster.Raster(ret_var, self.cell).rasterArray()
        pi_array = Raster.Raster(pi_var, self.cell).rasterArray()
        esc_array = p_array - ret_array - pi_array
        esc_array[esc_array < 0] = 0
        with rasterio.open(os.path.join(out_path, "esc_" + month + ".tif"), 'w',
                           **p_profile) as dst:
            dst.write(esc_array.astype(rasterio.float64), 1)

    def set_initial_month(self):
        feasible_months = []
        for month in self.months_identifiers:
            pi_var = self.variableHandler.gather_var("pi", month)
            etp_var = self.variableHandler.gather_var("etp", month)
            pi_array = Raster.Raster(pi_var, self.cell).rasterArray()
            etp_array = Raster.Raster(etp_var, self.cell).rasterArray()
            if np.nanmean(pi_array) > np.nanmean(etp_array):
                feasible_months.append(month)
        for month in feasible_months:
            if self.months_identifiers[min(self.months_identifiers.index(month) + 1, 11)] not in feasible_months:
                self.initial_month = min(self.months_identifiers.index(month) + 1, 11)

    def initial_hsi(self, out_path):
        cc_var = self.variableHandler.gather_var("cc")
        cc_raster = Raster.Raster(cc_var, self.cell)
        cc_profile = cc_raster.getMeta()[0]
        cc_array = cc_raster.rasterArray()
        with rasterio.open(os.path.join(out_path, "hsi_" + self.months_identifiers[self.initial_month] + ".tif"), 'w',
                           **cc_profile) as dst:
            dst.write(cc_array.astype(rasterio.float64), 1)


    def c1(self, out_path, month):
        hsi_var = self.variableHandler.gather_var("hsi", month)
        pm_var = self.variableHandler.gather_var("pm")
        pi_var = self.variableHandler.gather_var("pi", month)
        cc_var = self.variableHandler.gather_var("cc")
        cc_raster = Raster.Raster(cc_var, self.cell)
        cc_profile = cc_raster.getMeta()[0]
        hsi_array = Raster.Raster(hsi_var, self.cell).rasterArray()
        pm_array = Raster.Raster(pm_var, self.cell).rasterArray()
        pi_array = Raster.Raster(pi_var, self.cell).rasterArray()
        cc_array = cc_raster.rasterArray()
        c1_array = np.divide(hsi_array - pm_array + pi_array, cc_array - pm_array + 0.0001)
        with rasterio.open(os.path.join(out_path, "c1_" + month + ".tif"), 'w',
                           **cc_profile) as dst:
            dst.write(c1_array.astype(rasterio.float64), 1)

    def c2(self, out_path, month):
        hsi_var = self.variableHandler.gather_var("hsi", month)
        pm_var = self.variableHandler.gather_var("pm")
        pi_var = self.variableHandler.gather_var("pi", month)
        c1_var = self.variableHandler.gather_var("c1", month)
        cc_var = self.variableHandler.gather_var("cc")
        etp_var = self.variableHandler.gather_var("etp", month)
        cc_raster = Raster.Raster(cc_var, self.cell)
        cc_profile = cc_raster.getMeta()[0]
        hsi_array = Raster.Raster(hsi_var, self.cell).rasterArray()
        pm_array = Raster.Raster(pm_var, self.cell).rasterArray()
        pi_array = Raster.Raster(pi_var, self.cell).rasterArray()
        c1_array = Raster.Raster(c1_var, self.cell).rasterArray()
        cc_array = cc_raster.rasterArray()
        etp_array = Raster.Raster(etp_var, self.cell).rasterArray()
        etr1_array = np.multiply(c1_array, etp_array)
        c2_array = np.divide(hsi_array - pm_array + pi_array - etr1_array, cc_array - pm_array + 0.0001)
        with rasterio.open(os.path.join(out_path, "c2_" + month + ".tif"), 'w',
                           **cc_profile) as dst:
            dst.write(c2_array.astype(rasterio.float64), 1)

    def hd(self, out_path, month):
        pm_var = self.variableHandler.gather_var("pm")
        pi_var = self.variableHandler.gather_var("pi", month)
        hsi_var = self.variableHandler.gather_var("hsi", month)
        hsi_raster = Raster.Raster(hsi_var, self.cell)
        hsi_profile = hsi_raster.getMeta()[0]
        pm_array = Raster.Raster(pm_var, self.cell).rasterArray()
        pi_array = Raster.Raster(pi_var, self.cell).rasterArray()
        hsi_array = Raster.Raster(hsi_var, self.cell).rasterArray()
        hd_array = hsi_array + pi_array - pm_array
        with rasterio.open(os.path.join(out_path, "hd_" + month + ".tif"), 'w',
                           **hsi_profile) as dst:
            dst.write(hd_array.astype(rasterio.float64), 1)

    def etr(self, out_path, month):
        c1_var = self.variableHandler.gather_var("c1", month)
        c2_var = self.variableHandler.gather_var("c2", month)
        hd_var = self.variableHandler.gather_var("hd", month)
        etp_var = self.variableHandler.gather_var("etp", month)
        c1_raster = Raster.Raster(c1_var, self.cell)
        c1_profile = c1_raster.getMeta()[0]
        c1_array = c1_raster.rasterArray()
        c2_array = Raster.Raster(c2_var, self.cell).rasterArray()
        hd_array = Raster.Raster(hd_var, self.cell).rasterArray()
        etp_array = Raster.Raster(etp_var, self.cell).rasterArray()
        etr_array = np.multiply((c1_array + c2_array)/2, etp_array)
        etr_array = np.minimum(etr_array, hd_array)
        with rasterio.open(os.path.join(out_path, "etr_" + month + ".tif"), 'w',
                           **c1_profile) as dst:
            dst.write(etr_array.astype(rasterio.float64), 1)

    def hsf(self, out_path, month, hsi_mode=False):
        pm_var = self.variableHandler.gather_var("pm")
        cc_var = self.variableHandler.gather_var("cc")
        etr_var = self.variableHandler.gather_var("etr", month)
        hd_var = self.variableHandler.gather_var("hd", month)
        pm_raster = Raster.Raster(pm_var, self.cell)
        pm_profile = pm_raster.getMeta()[0]
        pm_array = pm_raster.rasterArray()
        cc_array = Raster.Raster(cc_var, self.cell).rasterArray()
        etr_array = Raster.Raster(etr_var, self.cell).rasterArray()
        hd_array = Raster.Raster(hd_var, self.cell).rasterArray()
        hsf_array = hd_array + pm_array - etr_array
        hsf_array = np.minimum(hsf_array, cc_array)
        with rasterio.open(os.path.join(out_path, "hsf_" + month + ".tif"), 'w',
                           **pm_profile) as dst:
            dst.write(hsf_array.astype(rasterio.float64), 1)

    def rp(self, out_path, month):
        pi_var = self.variableHandler.gather_var("pi", month)
        etr_var = self.variableHandler.gather_var("etr", month)
        hsi_var = self.variableHandler.gather_var("hsi", month)
        hsf_var = self.variableHandler.gather_var("hsf", month)
        pi_raster = Raster.Raster(pi_var, self.cell)
        pi_profile = pi_raster.getMeta()[0]
        pi_array = pi_raster.rasterArray()
        etr_array = Raster.Raster(etr_var, self.cell).rasterArray()
        hsi_array = Raster.Raster(hsi_var, self.cell).rasterArray()
        hsf_array = Raster.Raster(hsf_var, self.cell).rasterArray()
        rp_array = pi_array + hsi_array - hsf_array - etr_array
        rp_array[rp_array < 0] = 0
        with rasterio.open(os.path.join(out_path, "rp_" + month + ".tif"), 'w',
                           **pi_profile) as dst:
            dst.write(rp_array.astype(rasterio.float64), 1)


path = r"C:\Users\jpobr\Desktop\AAA\cropped"
etp_path = os.path.join(path, "Etp")
ret_path = os.path.join(path, "Ret")
ci_path = os.path.join(path, "Ci")
pi_path = os.path.join(path, "Pi")
esc_path = os.path.join(path, "Esc")
c1_path = os.path.join(path, "C1")
c2_path = os.path.join(path, "C2")
hd_path = os.path.join(path, "Hd")
etr_path = os.path.join(path, "Etr")
hsi_path = os.path.join(path, "Hsi")
hsf_path = os.path.join(path, "Hsf")
rp_path = os.path.join(path, "Rp")
operations = Operations(path, 10)
#operations.etp_thorn_escalar(12, etp_path)
#operations.ret(0.12, ret_path)
#operations.ci(ci_path)
#operations.pi(pi_path)
#operations.esc(esc_path)
operations.set_initial_month()
operations.initial_hsi(hsi_path)

for i in range(12):
    month = operations.months_identifiers[(operations.initial_month + i) % 12]
    next_month = operations.months_identifiers[(operations.initial_month + i + 1) % 12]
    operations.c1(c1_path, month)
    operations.c2(c2_path, month)
    operations.hd(hd_path, month)
    operations.etr(etr_path, month)
    operations.hsf(hsf_path, month)
    operations.rp(rp_path, month)
    if i < 11:
        varHandler = VariableHandler.VariableHandler(path)
        hsi_var = varHandler.gather_var("hsf", month)
        operations.write_tif(Raster.Raster(hsi_var, 10), hsi_path, "hsi_" + next_month + ".tif", next_month)
