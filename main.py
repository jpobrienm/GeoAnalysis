import os
import re
import sys
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import pyqtgraph as pg
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
import geoTools as gt
import numpy as np


class Raster:
    def __init__(self, path, cellsize):
        self.path = path
        self.cellSize = cellsize

    def raster_array(self, return_meta=False):
        with rasterio.open(self.path) as src:
            meta = src.profile
            xupscale = abs(meta["transform"][0] / self.cellSize)
            yupscale = abs(meta["transform"][4] / self.cellSize)
            affine = meta['transform']
            src.profile.update(
                width=int(meta['width'] * xupscale),
                height=int(meta['height'] * yupscale),
                transform=rasterio.Affine(self.cellSize * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cellSize * abs(affine[4]) / affine[4], affine[5])
            )
            thumbnail = src.read(1, out_shape=(1, int(src.height * yupscale), int(src.width * xupscale)),
                                 resampling=Resampling.average).astype('float64')
            thumbnail[thumbnail < -1e5] = np.nan
            thumbnail[thumbnail > 1e5] = np.nan
        if return_meta:
            return thumbnail, meta
        else:
            return thumbnail

    def clip(self, path_toclip):

        with rasterio.open(self.path) as src, rasterio.open(path_toclip) as srctoclip:
            meta = src.profile
            xupscale = abs(meta["transform"][0] / self.cellSize)
            yupscale = abs(meta["transform"][4] / self.cellSize)
            affine = meta['transform']
            crs = meta['crs']

            src.profile.update(
                width=meta['width'] * xupscale,
                height=meta['height'] * yupscale,
                transform=rasterio.Affine(self.cellSize * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cellSize * abs(affine[4]) / affine[4], affine[5])
            )

            meta = srctoclip.profile
            xupscale = abs(meta["transform"][0] / self.cellSize)
            yupscale = abs(meta["transform"][4] / self.cellSize)
            affine = meta['transform']

            srctoclip.profile.update(
                width=meta['width'] * xupscale,
                height=meta['height'] * yupscale,
                crs=crs,
                transform=rasterio.Affine(self.cellSize * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cellSize * abs(affine[4]) / affine[4], affine[5])
            )

            thumbnail = src.read(1, out_shape=(1, int(src.height), int(src.width))).astype('float64')
            thumbnail[thumbnail < -1e5] = np.nan
            thumbnail[thumbnail > 1e5] = np.nan
            thumbnailtoclip = srctoclip.read(1, out_shape=(1, int(srctoclip.height), int(srctoclip.width))).astype(
                'float64')
            thumbnailtoclip[thumbnailtoclip < -1e5] = np.nan
            thumbnailtoclip[thumbnailtoclip > 1e5] = np.nan

            top_left_thumbnail = src.xy(0, 0)
            index = srctoclip.index(top_left_thumbnail[0], top_left_thumbnail[1])
            clipped_thumbnail = thumbnailtoclip[index[0]: index[0] + len(thumbnail),
                                index[1]:index[1] + len(thumbnail[0])]
            #clipped_thumbnail[np.isnan(thumbnail)] = np.nan

        return clipped_thumbnail


class Metadata:
    def __init__(self):
        self.variables = ['C1', 'C2', 'Cc', 'Ci', 'Cfo', 'Etp', 'Etr', 'Esc', 'Hd', 'Hsf', 'Hsi', 'Kfc', 'Kp', 'Kv',
                          'P', 'Pi', 'Pm', 'Ret', 'Rp', 'Pendientes', 'T']
        self.basic_vars = ["cc", "cfo", "kfc", "kp", "kv", "pm", "p", "pendientes", "t"]
        self.months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                       "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.days_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        self.month_ids = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        self.repo_dir = ''
        self.repo_dict = {}
        self.proj_dir = ''
        self.proj_meta = ''
        self.cell_size = 12.5
        self.selected_raster = ''
        self.selected_raster_shape = ''
        self.proj_dict = {'enero': {}, 'febrero': {}, 'marzo': {}, 'abril': {}, 'mayo': {}, 'junio': {}, 'julio': {},
                          'agosto': {}, 'septiembre': {}, 'octubre': {}, 'noviembre': {}, 'diciembre': {}, 'promedio': {}
                          }
        for key in self.proj_dict:
            self.proj_dict[key] = {'c1': '', 'c2': '', 'cc': '', 'cfo': '', 'ci': '', 'esc': '','etp': '', 'etr': '',
                                   'hd': '', 'hsf': '', 'hsi': '', 'kfc': '', 'kp': '', 'kv': '', 'p': '', 'pi': '',
                                   'pm': '', 'ret': '', 'rp': '', 'pendientes': '', 't': ''}

    def update_proj_dict(self, month, var, is_global=False):
        if is_global:
            self.proj_dict[month][var] = os.path.join(self.proj_dir, var.title(), var.title() + '_.tif')
        else:
            self.proj_dict[month][var] = os.path.join(self.proj_dir, var.title(), var.title() + '_' + month.title()
                                                      + '.tif')


class FileManager:
    def __init__(self, metadata):
        self.metadata = metadata
        self.repo_dict = self.metadata.repo_dict
        self.basic_vars = self.metadata.basic_vars

    def extract_vars(self):
        keys_list = list(self.repo_dict.keys())
        paths_list = list(self.repo_dict.values())
        for i in range(len(keys_list)):
            name = re.split('[_. ]', keys_list[i].lower())
            if name[1] == 'tif':
                for var in self.metadata.basic_vars:
                    if var == name[0]:
                        for month in self.metadata.months:
                            self.metadata.proj_dict[month.lower()][var] = paths_list[i]
            for j in range(len(self.metadata.month_ids)):
                if self.metadata.month_ids[j] in name[1]:
                    for var in self.metadata.basic_vars:
                        if var == name[0]:
                            self.metadata.proj_dict[self.metadata.months[j].lower()][var] = paths_list[i]

    def check_vars(self, cfo_text, n_hrs_text):
        missing_vars = []
        check = True
        cfo = cfo_text.toPlainText()
        n_hrs = re.split('[, ]', n_hrs_text.toPlainText())
        global_vars = ["cc", "kfc", 'cfo', "kp", "kv", "pm", 'pendientes']

        if cfo == '':
            if self.metadata.proj_dict['enero']['cfo'] == '':
                missing_vars.append('Cfo')
                check = False

        if n_hrs == ['']:
            missing_vars.append('numero de horas de sol')
            check = False

        for var in global_vars:
            if var == 'cfo':
                pass
            elif var == 'kp' and self.metadata.proj_dict['enero']['kp'] == '':
                if self.metadata.proj_dict['enero']['pendientes'] == '':
                    missing_vars.append('Kp o Pendientes')
                    check = False
            elif self.metadata.proj_dict['enero'][var] == '':
                missing_vars.append(var)
                check = False

        for var in self.metadata.basic_vars:
            if var not in global_vars:
                for month in self.metadata.months:
                    if self.metadata.proj_dict[month.lower()][var] == '':
                        missing_vars.append(var + ' ' + month)
                        check = False

        return check, missing_vars


class ImgHandler:
    def __init__(self, metadata, visual_box, file_list, selected_label):
        self.metadata = metadata
        self.visual_box = visual_box
        self.file_list = file_list
        self.selected_label = selected_label

    def show_image(self):
        self.visual_box.clear()
        file = self.file_list.currentItem().text()
        self.metadata.selected_raster = self.metadata.repo_dict[file]
        self.selected_label.setText('Mapa de referencia: ' + file)
        file_array, self.metadata.proj_meta = gt.Raster(self.metadata.repo_dict[file],
                                                        self.metadata.cell_size).raster_array(True)
        self.metadata.selected_raster_shape = file_array.shape
        image = pg.ImageItem(file_array, axisOrder='row-major')
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0, 255, 255, 255], [255, 255, 0, 255], [0, 0, 0, 255], (0, 0, 255, 255), (255, 0, 0, 255)],
                         dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        image.setLevels([np.nanmin(file_array), np.nanmax(file_array)])
        image.setLookupTable(lut, update=True)
        self.visual_box.addItem(image)


class ComboHandler:
    def __init__(self, metadata, month_combo, var_combo, file_list, cell_combo):
        self.metadata = metadata
        self.month_combo = month_combo
        self.var_combo = var_combo
        self.cell_combo = cell_combo
        self.file_list = file_list

    def filter_by_month(self):
        self.file_list.clear()
        month = str(self.month_combo.currentText()).lower()
        keys = list(self.metadata.repo_dict.keys())
        id_ = ''

        for id_month in self.metadata.month_ids:
            if id_month in month:
                id_ = id_month
        if month == 'mes':
            for key in keys:
                self.file_list.addItem(key)
        else:
            for key in keys:
                name = re.split('[_. ]', key)
                if name[1].lower() == 'tif':
                    self.file_list.addItem(key)
                elif id_ in name[1].lower():
                    self.file_list.addItem(key)

    def filter_by_var(self):
        self.file_list.clear()
        var = str(self.var_combo.currentText()).lower()
        keys = list(self.metadata.repo_dict.keys())
        if var == 'variable':
            for key in keys:
                self.file_list.addItem(key)
        else:
            for key in keys:
                name = re.split('[_. ]', key)
                if var == name[0].lower():
                    self.file_list.addItem(key)

    def get_cell_size(self):
        value = self.cell_combo.currentText()
        if value != 'Tamaño de Celda (Por Defecto: 12.5)':
            self.metadata.cell_size = float(value)
        else:
            self.metadata.cell_size = 12.5


class StatsHandler:
    def __init__(self, metadata, list_box, text_box):
        self.metadata = metadata
        self.list_box = list_box
        self.text_box = text_box

    def write_stats(self):
        file = self.list_box.currentItem().text()
        path_file = self.metadata.repo_dict[file]
        raster = Raster(path_file, self.metadata.cell_size)
        data_array, data_meta = raster.raster_array(return_meta=True)
        stats_text = 'Estadisticas'
        array_shape = 'Dimensiones del Raster: ' + str(data_array.shape)
        arra_avg = 'Valor Promedio: ' + str(np.nanmean(data_array))
        array_std = 'Desviacion Estandar: ' + str(np.nanstd(data_array))
        array_max = 'Valor Maximo: ' + str(np.nanmax(data_array))
        array_min = 'Valor Minimo: ' + str(np.nanmin(data_array))
        self.text_box.clear()
        self.text_box.appendPlainText(stats_text)
        self.text_box.appendPlainText(array_shape)
        self.text_box.appendPlainText(arra_avg)
        self.text_box.appendPlainText(array_std)
        self.text_box.appendPlainText(array_max)
        self.text_box.appendPlainText(array_min)


class ProcessHandler:
    def __init__(self, metadata, cfo_text, n_hrs_text):
        self.metadata = metadata
        self.cfo_text = cfo_text
        self.n_hrs_text = n_hrs_text

    def compute(self, check, missing_vars):

        if check:

            base_raster = Raster(self.metadata.selected_raster, self.metadata.cell_size)
            base_shape = base_raster.raster_array(False).shape

            n_hrs_day = [x for x in re.split('[, ]', self.n_hrs_text.toPlainText())]

            cc_clip = base_raster.clip(self.metadata.proj_dict['enero']['cc'])
            gt.write_tif(cc_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Cc', '')

            pm_clip = base_raster.clip(self.metadata.proj_dict['enero']['pm'])
            gt.write_tif(pm_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Pm', '')

            if self.metadata.proj_dict['enero']['cfo'] == '':
                text = self.cfo_text.toPlainText()
                value = float(text)
                cfo_clip = np.full(base_shape, value, dtype=float)
            else:
                cfo_clip = base_raster.clip(self.metadata.proj_dict['enero']['cfo'])

            gt.write_tif(cfo_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Cfo', '')

            if self.metadata.proj_dict['enero']['kp'] == '':
                slope_clip = base_raster.clip(self.metadata.proj_dict['enero']['pendientes'])
                gt.write_tif(slope_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Pendientes', '')
                kp_clip = gt.kp(slope_clip)
                gt.write_tif(kp_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Kp', '')
            else:
                kp_clip = base_raster.clip(self.metadata.proj_dict['enero']['kp'])
                gt.write_tif(kp_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Kp', '')

            kv_clip = base_raster.clip(self.metadata.proj_dict['enero']['kv'])
            gt.write_tif(kv_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Kv', '')

            kfc_clip = base_raster.clip(self.metadata.proj_dict['enero']['kfc'])
            gt.write_tif(kfc_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Kfc', '')
            t_arrays = []
            pi_avgs = []
            etp_avgs = []

            for month in self.metadata.months:
                p_clip = base_raster.clip(self.metadata.proj_dict[month.lower()]['p'])
                gt.write_tif(p_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'P', month)
                t_clip = base_raster.clip(self.metadata.proj_dict[month.lower()]['t'])
                gt.write_tif(t_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'T', month)
                t_arrays.append(t_clip)
                ret_clip = gt.ret(p_clip, cfo_clip)
                gt.write_tif(ret_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Ret', month)
                ci_clip = gt.ci(kp_clip, kv_clip, kfc_clip)
                gt.write_tif(ci_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Ci', month)
                pi_clip = gt.pi(ci_clip, p_clip, ret_clip)
                pi_avgs.append(np.nanmean(pi_clip))
                gt.write_tif(pi_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Pi', month)
                esc_clip = gt.esc(p_clip, ret_clip, pi_clip)
                gt.write_tif(esc_clip, self.metadata.proj_meta, self.metadata.proj_dir, 'Esc', month)
                self.metadata.update_proj_dict(month.lower(), 'cfo', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'cc', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'pm', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'pendientes', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'kp', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'kv', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'kfc', is_global=True)
                self.metadata.update_proj_dict(month.lower(), 'p')
                self.metadata.update_proj_dict(month.lower(), 't')
                self.metadata.update_proj_dict(month.lower(), 'ret')
                self.metadata.update_proj_dict(month.lower(), 'ci')
                self.metadata.update_proj_dict(month.lower(), 'pi')
                self.metadata.update_proj_dict(month.lower(), 'esc')

            etp = gt.etp_thorn_escalar(t_arrays, float(n_hrs_day[0]), self.metadata.days_month)

            for i in range(len(self.metadata.months)):
                etp_avgs.append(np.nanmean(etp[i]))
                gt.write_tif(etp[i], self.metadata.proj_meta, self.metadata.proj_dir, 'Etp', self.metadata.months[i])
                self.metadata.update_proj_dict(self.metadata.months[i].lower(), 'etp')

            del p_clip, t_clip, t_arrays, ret_clip, ci_clip, pi_clip
            initial_index = 0

            for i in range(len(pi_avgs)):
                if pi_avgs[i] > etp_avgs[i]:
                    initial_index = (i + 1) % 12

            hsi = cc_clip
            gt.write_tif(hsi, self.metadata.proj_meta, self.metadata.proj_dir, 'Hsi',
                         self.metadata.months[initial_index])
            self.metadata.update_proj_dict(self.metadata.months[initial_index].lower(), 'hsi')

            rp_anual = []

            for i in range(12):
                pi = base_raster.clip(
                    self.metadata.proj_dict[self.metadata.months[(initial_index + i) % 12].lower()]['pi'])
                c1 = gt.c1(hsi, pm_clip, pi, cc_clip)
                gt.write_tif(c1, self.metadata.proj_meta, self.metadata.proj_dir, 'C1',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'c1')
                c2 = gt.c2(hsi, pm_clip, pi, c1, cc_clip, etp[(initial_index + i) % 12])
                gt.write_tif(c2, self.metadata.proj_meta, self.metadata.proj_dir, 'C2',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'c2')
                hd = gt.hd(pm_clip, pi, hsi)
                gt.write_tif(hd, self.metadata.proj_meta, self.metadata.proj_dir, 'Hd',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'hd')
                etr = gt.etr(c1, c2, hd, etp[(initial_index + i) % 12])
                gt.write_tif(etr, self.metadata.proj_meta, self.metadata.proj_dir, 'Etr',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'etr')
                hsf = gt.hsf(pm_clip, cc_clip, etr, hd)
                gt.write_tif(hsf, self.metadata.proj_meta, self.metadata.proj_dir, 'hsf',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'hsf')
                rp = gt.rp(pi, etr, hsi, hsf)
                gt.write_tif(rp, self.metadata.proj_meta, self.metadata.proj_dir, 'Rp',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'rp')
                hsi = hsf.copy()
                gt.write_tif(hsi, self.metadata.proj_meta, self.metadata.proj_dir, 'Hsi',
                             self.metadata.months[(initial_index + i) % 12])
                self.metadata.update_proj_dict(self.metadata.months[(initial_index + i) % 12].lower(), 'hsi')

                if i == 0:
                    rp_anual = rp
                else:
                    rp_anual += rp
            gt.write_tif(rp_anual, self.metadata.proj_meta, self.metadata.proj_dir, 'Rp', 'anual')
        else:
            error_message = 'Error: No se encuentran las siguientes variables: '
            for missing in missing_vars:
                error_message += missing + ', '
            ErrorWindow(error_message)


class ErrorWindow:
    def __init__(self, message):
        self.message = message
        error_dialog = qtw.QErrorMessage()
        error_dialog.showMessage(self.message)
        error_dialog.setMinimumSize(400, 160)
        error_dialog.setWindowTitle('Error')
        error_dialog.exec_()


class NewProjWindow(qtw.QDialog):
    def __init__(self, title, metadata):
        self.metadata = metadata

        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(600, 100)

        # Label
        self.main_layout = qtw.QHBoxLayout()

        # Widgets
        self.proj_label = qtw.QLabel('Seleccionar Carpeta del Proyecto: ')
        self.proj_name = qtw.QLineEdit()
        self.proj_btn = qtw.QPushButton('Crear Proyecto')

        self.proj_btn.clicked.connect(self.new_file_dialog)

        self.main_layout.addWidget(self.proj_label)
        self.main_layout.addWidget(self.proj_name)
        self.main_layout.addWidget(self.proj_btn)

        self.setLayout(self.main_layout)

    def new_file_dialog(self):
        close_window = True
        parent_path = qtw.QFileDialog.getExistingDirectory(self, 'Seleccione Carpeta', r'/')
        project_name = self.proj_name.text()

        if project_name.strip() and parent_path.strip():
            self.metadata.proj_dir = os.path.join(parent_path, project_name)

            for folder in self.metadata.variables:
                try:
                    os.makedirs(os.path.join(self.metadata.proj_dir, folder))
                except FileExistsError:
                    ErrorWindow('Error: Ya existe un proyecto con este nombre')
                    close_window = False
                    break

        if close_window:
            self.close()


class Application(qtw.QMainWindow):

    def __init__(self):

        self.metadata = Metadata()

        super().__init__()

        # Window configuration

        self.setWindowTitle('GeoTools Ver. 0.9')
        self.setMinimumSize(1200, 650)
        self.setWindowIcon(qtg.QIcon('terra_consultants.jpeg'))

        # Menu Widget
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Archivo')
        new_action = qtw.QAction('Nuevo Proyecto', self)
        open_action = qtw.QAction('Abrir Proyecto', self)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)

        # Widgets lvl1

        self.rep_name = qtw.QLabel('Ubicacion del Repositorio: ')
        self.rep_dir = qtw.QLabel('')
        self.set_rep = qtw.QPushButton('Seleccionar Repositorio')

        # Widgets of lvl 2 left part

        self.selected_label = qtw.QLabel('Mapa de referencia: ')
        self.file_list = qtw.QListWidget()

        # Widget lvl2 central part

        self.plotter = pg.GraphicsView()
        self.visual_box = pg.ViewBox()
        self.visual_box.invertY()
        self.plotter.setCentralItem(self.visual_box)
        self.plotter.setBackground("w")

        # Widgets right part of lvl2 layout

        self.generate_files = qtw.QPushButton('Generar Datos')

        self.cell_combo = qtw.QComboBox()
        self.cell_combo.addItems(['Tamaño de Celda (Por Defecto: 12.5)', '50', '25', '5', '3', '2', '1'])

        self.data_combo = qtw.QComboBox()
        self.data_combo.addItems(['Variable'] + self.metadata.variables)

        self.months_combo = qtw.QComboBox()
        self.months_combo.addItems(['Mes'] + self.metadata.months + ['Promedio'])

        self.cfo_layout = qtw.QHBoxLayout()

        self.cfo_label = qtw.QLabel('Cfo (constante): ')
        self.cfo_text = qtw.QPlainTextEdit()
        self.cfo_text.setMaximumHeight(25)

        self.cfo_layout.addWidget(self.cfo_label)
        self.cfo_layout.addWidget(self.cfo_text)

        self.day_hrs_layout = qtw.QHBoxLayout()

        self.day_hrs_label = qtw.QLabel('Horas de sol: ')
        self.day_hrs_text = qtw.QPlainTextEdit()
        self.day_hrs_text.setMaximumHeight(25)

        self.day_hrs_layout.addWidget(self.day_hrs_label)
        self.day_hrs_layout.addWidget(self.day_hrs_text)

        self.stats = qtw.QPlainTextEdit()
        self.stats.setReadOnly(True)

        # Create pertinent classes

        self.new_proj_dialog = NewProjWindow('Nuevo Proyecto', self.metadata)
        self.image_handler = ImgHandler(self.metadata, self.visual_box, self.file_list, self.selected_label)
        self.file_manager = FileManager(self.metadata)
        self.combo_handler = ComboHandler(self.metadata, self.months_combo, self.data_combo, self.file_list,
                                          self.cell_combo)
        self.stats_handler = StatsHandler(self.metadata, self.file_list, self.stats)
        self.process_handler = ProcessHandler(self.metadata, self.cfo_text, self.day_hrs_text)

        # Menu Functionality

        new_action.triggered.connect(self.new_proj_window)

        # Menu functionality
        open_action.triggered.connect(self.open_proj_window)

        # Functionality layer lvl1

        self.set_rep.clicked.connect(self.ask_repository)

        # Functionality layer lvl2

        self.file_list.clicked.connect(self.select_file_list)
        self.generate_files.clicked.connect(self.compute)
        self.months_combo.currentTextChanged.connect(self.select_month)
        self.data_combo.currentTextChanged.connect(self.select_var)
        self.cell_combo.currentTextChanged.connect(self.select_cell_size)
        # Main widget and layouts creation

        main_widget = qtw.QWidget()
        self.setCentralWidget(main_widget)

        self.main_layout = qtw.QFormLayout()
        self.layout_lvl1 = qtw.QHBoxLayout()
        self.layout_lvl2l = qtw.QVBoxLayout()
        self.layout_lvl2 = qtw.QHBoxLayout()
        self.layout_lvl2r = qtw.QVBoxLayout()

        # Pack layout lvl 1

        self.layout_lvl1.addWidget(self.rep_name)
        self.layout_lvl1.addWidget(self.rep_dir)
        self.layout_lvl1.addWidget(self.set_rep)

        # Pack layout lvl2 left part

        self.layout_lvl2l.addWidget(self.selected_label)
        self.layout_lvl2l.addWidget(self.file_list)

        # Pack layout lvl2 right part

        self.layout_lvl2r.addWidget(self.generate_files)
        self.layout_lvl2r.addWidget(self.cell_combo)
        self.layout_lvl2r.addWidget(self.data_combo)
        self.layout_lvl2r.addWidget(self.months_combo)
        self.layout_lvl2r.addLayout(self.cfo_layout)
        self.layout_lvl2r.addLayout(self.day_hrs_layout)
        self.layout_lvl2r.addWidget(self.stats)

        # Pack layers of layout lvl 2

        self.layout_lvl2.addLayout(self.layout_lvl2l)
        self.layout_lvl2.addWidget(self.plotter)
        self.layout_lvl2.addLayout(self.layout_lvl2r)

        # Pack layouts into main layout

        self.main_layout.addRow(self.layout_lvl1)
        self.main_layout.addRow(self.layout_lvl2)

        # Set layout of main widget

        main_widget.setLayout(self.main_layout)

    def new_proj_window(self):
        self.new_proj_dialog.show()

    def open_proj_window(self):
        dialog = qtw.QFileDialog.getExistingDirectory(self, 'Select Folder', r'/')
        self.metadata.proj_dir = dialog
        self.setWindowTitle('GeoTools Ver. 0.9.   ' + 'Proyecto en  ' + dialog)

    def ask_repository(self):
        self.file_list.clear()
        dialog = qtw.QFileDialog.getExistingDirectory(self, 'Select Folder', r'/')
        self.metadata.repo_dir = dialog
        self.rep_dir.setText(dialog)
        for root, dirs, files in os.walk(dialog):
            for file in files:
                if file.endswith(".tif"):
                    self.file_list.addItem(file)
                    self.metadata.repo_dict[file] = os.path.join(root, file)

    def select_file_list(self):
        self.image_handler.show_image()
        self.stats_handler.write_stats()

    def select_month(self):
        self.combo_handler.filter_by_month()

    def select_var(self):
        self.combo_handler.filter_by_var()

    def select_cell_size(self):
        self.combo_handler.get_cell_size()

    def compute(self):
        if self.metadata.proj_dir == '':
            ErrorWindow('Error: Debe crear o abrir un proyecto')
        else:
            self.file_manager.extract_vars()
            check, missing_vars = self.file_manager.check_vars(self.cfo_text, self.day_hrs_text)
            self.process_handler.compute(check, missing_vars)
        pass


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    main_window = Application()
    main_window.show()
    app.exec_()
