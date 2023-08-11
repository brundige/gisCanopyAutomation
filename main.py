import os
import os
from qgis._core import QgsApplication
import threading
import sys
from osgeo import gdal, ogr, osr
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *
from qgis.core import (
    QgsApplication,
    QgsProcessingFeedback,
    QgsVectorLayer
)

src_path = 'res_files'
res_path= 'src_files'


def fail_with_grace(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)

    return wrapper


@fail_with_grace
def rename(folder_path, new_name):
    file_num = 0
    for f in os.listdir(folder_path):
        # rename all files in folder
        os.rename(os.path.join(folder_path, f), os.path.join(folder_path, f'{new_name}_{file_num}.tif'))
        file_num += 1


def polygonize(in_path, out_path):
    gdal.UseExceptions()
    gdal.AllRegister()

    # get raster datasource
    src_ds = gdal.Open(in_path)
    if src_ds is None:
        print('Unable to open %s' % in_path)
        sys.exit(1)

    #
    src_band = src_ds.GetRasterBand(1)
    dst_layername = "POLYGONIZED_STUFF"
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(out_path)

    sp_ref = osr.SpatialReference()
    sp_ref.SetFromUserInput("EPSG:4326")

    dst_layer = dst_ds.CreateLayer(dst_layername, srs=sp_ref)
    fd = ogr.FieldDefn("canopy", ogr.OFTInteger)
    dst_layer.CreateField(fd)
    dst_field = dst_layer.GetLayerDefn().GetFieldIndex("canopy")

    gdal.Polygonize(src_band, None, dst_layer, dst_field, [], callback=None)


# START HEADLESS QGIS
QgsApplication.setPrefixPath('/Applications/QGIS.app/Contents', True)
qgs = QgsApplication([], False)
qgs.initQgis()
print("QGIS initialized")

rename(src_path, 'canopy_quad')

# merge all tif files in folder
gdal.BuildVRT(os.path.join(src_path, 'canopy_2022.vrt'),
              [os.path.join(src_path, f) for f in os.listdir(src_path) if f.endswith('.tif')])
# load virtual raster into qgis
layer = QgsRasterLayer(os.path.join(src_path, 'canopy_2022.vrt'), 'canopy_2022.vrt')

# polygonize raster
polygonize(os.path.join(src_path, 'canopy_2022.vrt'), os.path.join(res_path, 'canopy_2022.shp'))

# ****************************************************** for gdal processsing ******************************************************
sys.path.append('/Applications/QGIS.app/Contents/Resources/python/plugins')
import processing
from processing.core.Processing import Processing

Processing.initialize()

# ****************************************************** for gdal processsing ******************************************************


qgs.exitQgis()

# END HEADLESS QGIS

