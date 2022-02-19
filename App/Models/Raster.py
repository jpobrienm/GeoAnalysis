import rasterio
from rasterio.enums import Resampling
import numpy as np
import os


class Raster():
    def __init__(self, path, cell):
        self.path = path
        self.cell = cell

    def getMeta(self):
        with rasterio.open(self.path) as src:
            meta = src.profile
            xupscale = abs(meta["transform"][0] / self.cell)
            yupscale = abs(meta["transform"][4] / self.cell)
            affine = meta['transform']

        return meta, xupscale, yupscale, affine

    def rasterArray(self):
        meta, xupscale, yupscale, affine = self.getMeta()
        with rasterio.open(self.path) as src:
            meta.update(
                width=meta['width'] * xupscale,
                height=meta['height'] * yupscale,
                transform=rasterio.Affine(self.cell * abs(affine[0]) / affine[0], affine[1], affine[2],
                                          affine[3], self.cell * abs(affine[4]) / affine[4], affine[5])
            )

            thumbnail = src.read(1, out_shape=(1, int(src.height * yupscale), int(src.width * xupscale)),
                                 resampling=Resampling.nearest).astype('float64')

            thumbnail[thumbnail < -1e-5] = np.nan

        return thumbnail
