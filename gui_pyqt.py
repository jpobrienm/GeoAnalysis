import os
import shutil
import re
import sys
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
from PyQt5 import QtCore
import geoTools as gt
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt


class FileManager:
    def __init__(self, project_path, project_name):

        self.project_path = project_path
        self.project_name = project_name
        self.forlders = ['C1', 'C2', 'Cc', 'Cfo', 'Ci', 'Etp', 'Etpr', 'Etr', 'Hd', 'Hsf', 'Kfc', 'Kp', 'Kv', 'Pm',
                         'Pendiente', 'Pi', 'Ret', 'Rp', 'T']

    def make_project_folder(self):

        parent_dir = os.path.join(self.project_path, self.project_name)
        print(parent_dir)
        if os.path.exists(parent_dir):
            shutil.rmtree(parent_dir)
        os.makedirs(parent_dir)
        for folder in self.forlders:
            os.makedirs(os.path.join(parent_dir, folder))



class Application(qtw.QWidget):
    def __init__(self):
        self.project_folder = ''
        self.repo_folder = ''
        self.repo_dict = {}
        self.chosen_path = ''
        self.chosen_meta = ''
        self.identifiers = ["cc", "cfo", "kfc", "kp", "kv", "pm", "slope", "p", "pendiente", "t"]
        self.month_identifiers = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        self.days_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        super().__init__()
        self.setWindowTitle('GeoTools Ver. 0.4')
        self.setMinimumSize(1200, 600)
        self.setWindowIcon(qtg.QIcon('terra_consultants.jpeg'))

        # Principal Layout

        self.main_layout = qtw.QFormLayout()
        self.layout_lvl1 = qtw.QHBoxLayout()
        self.layout_lvl2 = qtw.QHBoxLayout()
        self.layout_lvl3 = qtw.QHBoxLayout()
        self.layout_lvl3r = qtw.QVBoxLayout()
        self.layout_lvl4 = qtw.QHBoxLayout()
        self.layout_lvl5 = qtw.QHBoxLayout()

        # Widget lvl1

        self.prj_name = qtw.QLabel('Nombre del proyecto: ')
        self.edit_prj_name = qtw.QLineEdit()
        self.prj_set_dir = qtw.QPushButton('Seleccionar Destino')
        self.prj_set_dir.clicked.connect(self.askdirectory)

        self.layout_lvl1.addWidget(self.prj_name)
        self.layout_lvl1.addWidget(self.edit_prj_name)
        self.layout_lvl1.addWidget(self.prj_set_dir)

        # Widget lvl2

        self.rep_name = qtw.QLabel('Ubicacion del Repositorio: ')
        self.rep_dir = qtw.QLabel('')
        self.set_rep = qtw.QPushButton('Seleccionar Repositorio')
        self.set_rep.clicked.connect(self.askrepository)

        self.layout_lvl2.addWidget(self.rep_name)
        self.layout_lvl2.addWidget(self.rep_dir)
        self.layout_lvl2.addWidget(self.set_rep)

        # Widget lvl3

        self.file_list = qtw.QListWidget()
        self.file_list.clicked.connect(self.select_file_list)

        self.plotter = pg.GraphicsView()
        self.visual_box = pg.ViewBox()
        self.visual_box.invertY()
        self.plotter.setCentralItem(self.visual_box)
        self.plotter.setBackground("w")

        self.layout_lvl3.addWidget(self.file_list)
        self.layout_lvl3.addWidget(self.plotter)

        # Right part of lvl3 layout

        self.generate_files = qtw.QPushButton('Generar Datos')
        self.generate_files.clicked.connect(self.compute)

        self.folder_combo = qtw.QComboBox()
        self.folder_combo.addItems(['Carpeta', 'Repositorio', 'Proyecto'])

        self.data_combo = qtw.QComboBox()
        self.data_combo.addItems(['C1', 'C2', 'Cc', 'Ci', 'Etp', 'Etr', 'Hd', 'Hsf', 'Hsi', 'Kfc', 'Kp', 'Kv', 'P',
                                  'Pi', 'Pm', 'Ret', 'Rp', 'Pendiente', 'T'])

        self.months_combo = qtw.QComboBox()
        self.months_combo.addItems(["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                                    "Septiembre", "Octubre", "Noviembre", "Diciembre"])

        self.cfo_layout = qtw.QHBoxLayout()

        self.cfo_label = qtw.QLabel('Cfo (constante): ')
        self.cfo_text = qtw.QPlainTextEdit()
        self.cfo_text.setMaximumHeight(25)

        self.cfo_layout.addWidget(self.cfo_label)
        self.cfo_layout.addWidget(self.cfo_text)

        self.stats = qtw.QPlainTextEdit()
        self.stats.setReadOnly(True)

        self.layout_lvl3r.addWidget(self.generate_files)
        self.layout_lvl3r.addWidget(self.data_combo)
        self.layout_lvl3r.addWidget(self.months_combo)
        self.layout_lvl3r.addLayout(self.cfo_layout)
        self.layout_lvl3r.addWidget(self.stats)

        # layout lvl 4

        self.chosen_map = qtw.QLineEdit()
        self.chosen_map.setReadOnly(True)

        self.set_map = qtw.QPushButton('Seleccionar mapa de referencia')

        self.layout_lvl4.addWidget(self.chosen_map)
        self.layout_lvl4.addWidget(self.set_map)

        # layout lvl 5

        self.sun_lbl = qtw.QLabel('Numero de horas de sol promedio mensual: ')
        self.sun_hrs = qtw.QLineEdit()

        self.layout_lvl5.addWidget(self.sun_lbl)
        self.layout_lvl5.addWidget(self.sun_hrs)


        # Pack the right part on lvl 3

        self.layout_lvl3.addLayout(self.layout_lvl3r)

        # Pack widwets in main layout

        self.main_layout.addRow(self.layout_lvl1)
        self.main_layout.addRow(self.layout_lvl2)
        self.main_layout.addRow(self.layout_lvl3)
        self.main_layout.addRow(self.layout_lvl4)
        self.main_layout.addRow(self.layout_lvl5)

        self.setLayout(self.main_layout)
        self.show()

    def askdirectory(self):
        dialog_parent_dir = qtw.QFileDialog.getExistingDirectory(self, 'Select Folder', r'/')
        parent_folder = self.edit_prj_name.text()

        if parent_folder.strip():
            filemanager = FileManager(dialog_parent_dir, parent_folder)
            filemanager.make_project_folder()
            self.setWindowTitle('GeoTools Ver. 0.4  ' + '  Directorio del proyecto:  ' + self.project_folder)
        else:
            print("error")

    def askrepository(self):
        self.file_list.clear()
        dialog = qtw.QFileDialog.getExistingDirectory(self, 'Select Folder', r'/')
        self.repo_folder = dialog
        self.rep_dir.setText(dialog)
        for root, dirs, files in os.walk(dialog):
            for file in files:
                if file.endswith(".tif"):
                    self.file_list.addItem(file)
                    self.repo_dict[file] = os.path.join(root, file)

    def select_file_list(self):
        self.visual_box.clear()
        file = self.file_list.currentItem().text()
        file_array, self.chosen_meta = gt.Raster(self.repo_dict[file], 12.5).raster_array(True)
        image = pg.ImageItem(file_array, axisOrder='row-major')
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0, 255, 255, 255], [255, 255, 0, 255], [0, 0, 0, 255], (0, 0, 255, 255), (255, 0, 0, 255)],
                           dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        image.setLookupTable(lut)
        image.setLevels([np.nanmin(file_array), np.nanmax(file_array)])
        image.setLookupTable(lut, update=True)
        self.visual_box.addItem(image)
        self.chosen_map.setText(file)

    def compute(self):

        # handling files

        self.chosen_path = self.repo_dict[self.chosen_map.text()]

        keys_list = list(self.repo_dict.keys())
        paths_list = list(self.repo_dict.values())
        names_list = []
        month_list = []

        for key in keys_list:
            name = re.split("[._ ]", key)
            names_list.append((str(name[0].lower())))
            month_list.append(str(name[1].lower()))

        # opening required rasters

        base_raster = gt.Raster(self.chosen_path, 12.5)

        cc = base_raster.clip(paths_list[names_list.index('cc')])
        gt.ArrayTools(cc).write_tif(self.chosen_meta, self.project_folder, 'Cc', '')

        cfo = base_raster.clip(paths_list[names_list.index('cfo')])
        gt.ArrayTools(cfo).write_tif(self.chosen_meta, self.project_folder, 'Cfo', '')

        kfc = base_raster.clip(paths_list[names_list.index('kfc')])
        gt.ArrayTools(kfc).write_tif(self.chosen_meta, self.project_folder, 'Kfc', '')

        kv = base_raster.clip(paths_list[names_list.index('kv')])
        gt.ArrayTools(kv).write_tif(self.chosen_meta, self.project_folder, 'Kv', '')

        pm = base_raster.clip(paths_list[names_list.index('pm')])
        gt.ArrayTools(pm).write_tif(self.chosen_meta, self.project_folder, 'Pm', '')

        if 'kp' in names_list:
            kp = base_raster.clip(paths_list[names_list.index('kp')])
            gt.ArrayTools(kp).write_tif(self.chosen_meta, self.project_folder, 'Kp', '')

        elif 'pendiente' in names_list:
            slope = base_raster.clip(paths_list[names_list.index('pendiente')])
            gt.ArrayTools(slope).write_tif(self.chosen_meta, self.project_folder, 'Pendiente', '')

        elif 'slope' in names_list:
            slope = base_raster.clip(paths_list[names_list.index('slope')])
            gt.ArrayTools(slope).write_tif(self.chosen_meta, self.project_folder, 'Slope', '')

        p_indexes = [i for i in range(len(names_list)) if names_list[i] == 'p']
        t_indexes = [i for i in range(len(names_list)) if names_list[i] == 't']

        p_months = []
        t_months = []

        os.makedirs(os.path.join(self.project_folder, 'P'))
        os.makedirs(os.path.join(self.project_folder, 'T'))

        for id_ in self.month_identifiers:
            for index in p_indexes:
                if id_ in month_list[index]:
                    p = gt.Raster(self.chosen_path, 12.5).clip(paths_list[index])
                    gt.ArrayTools(p).write_tif(self.chosen_meta, self.project_folder, 'P', month_list[index])
                    p_months.append(p)
                    break
            for index in t_indexes:
                if id_ in month_list[index]:
                    t = gt.Raster(self.chosen_path, 12.5).clip(paths_list[index])
                    t_months.append(t)
                    gt.ArrayTools(t).write_tif(self.chosen_meta, self.project_folder, 'T', month_list[index])
                    break

        n_hours = float(self.sun_hrs.text())
        etp_array = gt.etp_thorn(t_months, n_hours, self.days_month)
        for i in range(len(etp_array)):
            gt.ArrayTools(etp_array[i]).write_tif(self.chosen_meta, self.project_folder, 'Etp', month_list[i])


app = qtw.QApplication(sys.argv)
main_window = Application()
app.exec()
