import rasterio
from rasterio.enums import Resampling
import numpy as np
import os
import matplotlib.pyplot as plt


class Raster:
    def __init__(self, path, cellsize):
        self.path = path
        self.cellSize = cellsize

    def raster_array(self, return_meta):
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
                                 resampling=Resampling.average).astype('float64')
            thumbnail[thumbnail < -1e-5] = np.nan
        if return_meta:
            return thumbnail, meta
        else:
            return thumbnail

    def clip(self, path_to_clip):
        with rasterio.open(self.path) as src, rasterio.open(path_to_clip) as srctoclip:
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
            top_left_thumbnail = src.xy(0, 0)
            index = srctoclip.index(top_left_thumbnail[0], top_left_thumbnail[1])
            clipped_thumbnail = thumbnailtoclip[index[0]: index[0] + len(thumbnail), index[1]:index[1] + len(thumbnail[0])]
            clipped_thumbnail[np.isnan(thumbnail)] = np.nan
        return clipped_thumbnail
