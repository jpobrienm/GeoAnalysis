import rasterio
from rasterio.enums import Resampling
import numpy as np
import os

from rasterio.warp import calculate_default_transform, reproject
from rasterio.windows import Window


class RasterGroup:
    def __init__(self, folder_path, cell):
        self.folder_path = folder_path
        self.cell = cell
        self.minSize = []
        self.file_list = {}
        self.crs_list = []
        self.group_crs = None
        self.inner_rectangle = []

    def gatherRasterPaths(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".tif"):
                    self.file_list[file] = os.path.join(root, file)

    def gatherMetadata(self):
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                self.crs_list.append(src.crs)

    def setGroupMetadata(self, index=0):
        self.group_crs = self.crs_list[index]

    def getMinSize(self):
        width, height = np.inf, np.inf
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                if src.width < width:
                    width = src.width
                if src.height < height:
                    height = src.height
        self.minSize = [width, height]

    def resizeGroup(self, out_path):
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                meta = src.profile
                xupscale = abs(meta["transform"][0] / self.cell)
                yupscale = abs(meta["transform"][4] / self.cell)
                affine = meta['transform']

                meta.update(
                    width=meta['width'] * xupscale,
                    height=meta['height'] * yupscale,
                    transform=rasterio.Affine(self.cell * abs(affine[0]) / affine[0], affine[1], affine[2],
                                              affine[3], self.cell * abs(affine[4]) / affine[4], affine[5])
                )

                thumbnail = src.read(1, out_shape=(1, int(src.height * yupscale), int(src.width * xupscale)),
                                     resampling=Resampling.nearest).astype('float64')

                with rasterio.open(os.path.join(out_path, file), 'w',
                                   **meta) as dst:
                    dst.write(thumbnail.astype(rasterio.float64), 1)


    def fixGroupMeta(self, out_path):
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                src_crs = src.crs
                transform, width, height = calculate_default_transform(src_crs, self.group_crs,
                                                                       src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()

                kwargs.update({
                    'crs': self.group_crs,
                    'transform': transform,
                    'width': width,
                    'height': height})

                with rasterio.open(os.path.join(out_path, file), 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=self.group_crs,
                            resampling=Resampling.nearest)

    def getInnerRectangle(self):
        left = -np.inf
        right = np.inf
        top = np.inf
        bottom = -np.inf
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                src_left, src_bottom, src_right, src_top = src.bounds
                if left < src_left:
                    left = src_left
                if right > src_right:
                    right = src_right
                if top > src_top:
                    top = src_top
                if bottom < src_bottom:
                    bottom = src_bottom
        self.inner_rectangle = [left, right, top, bottom]

    def show_indexes(self):
        left, right, top, bottom = self.inner_rectangle
        print(self.inner_rectangle)
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                top_left = src.index(left, top)
                right_bottom = src.index(right, bottom)


    def cropGroup(self, out_path):
        left, right, top, bottom = self.inner_rectangle
        for file in self.file_list:
            with rasterio.open(self.file_list[file]) as src:
                top_left = src.index(left, top)
                size = [min(src.width - top_left[0], self.minSize[0]), min(src.height - top_left[1], self.minSize[1])]
                window = Window(top_left[0], top_left[1], size[0], size[1])
                transform = src.window_transform(window)
                profile = src.profile
                profile.update({
                    'height': size[1],
                    'width': size[0],
                    'transform': transform})
                with rasterio.open(os.path.join(out_path, file), 'w',
                                   **profile) as dst:
                    dst.write(src.read(window=window))




#path = r"C:\Users\jpobr\Desktop\Repositorio"
#out_path = r"C:\Users\jpobr\Desktop\AAA"
#fixed_path = r"C:\Users\jpobr\Desktop\AAA\fixed"
#cropped_path = r"C:\Users\jpobr\Desktop\AAA\cropped"
#group = RasterGroup(path, 10)
#group.gatherRasterPaths()
#group.resizeGroup(out_path)
#group = RasterGroup(out_path, 10)
#group.gatherRasterPaths()
#group.gatherMetadata()
#group.setGroupMetadata()
#group.fixGroupMeta(fixed_path)
#group.getInnerRectangle()
#group.getMinSize()
#group.cropGroup(cropped_path)
