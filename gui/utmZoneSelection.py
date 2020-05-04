import os
from qgis.PyQt import QtGui, QtWidgets, uic 
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import pyqtSignal
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox, QgsSpinBox, QgsDoubleSpinBox, QgsColorButton
from qgis.core import QgsVectorLayer, QgsMapLayerProxyModel, QgsCoordinateTransform, \
                      QgsCoordinateReferenceSystem, QgsProject, QgsGeometry, QgsPointXY, QgsRectangle
from .gridAndLabelCreator import *



FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'utm_zone_selection_window.ui'))


class UTMZoneSelection(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, iface, layer, id_attr, id_value, spacing, crossX, crossY, scale, color, fontSize, font, fontLL, llcolor, linwidth_geo, linwidth_utm):
        """Constructor."""
        super(UTMZoneSelection, self).__init__()
        self.layer = layer
        self.id_attr = id_attr
        self.id_value = id_value
        self.spacing = spacing
        self.crossX = crossX
        self.crossY = crossY
        self.scale = scale
        self.color = color
        self.fontSize = fontSize
        self.font = font
        self.fontLL = fontLL
        self.llcolor = llcolor
        self.linwidth_geo = linwidth_geo
        self.linwidth_utm = linwidth_utm
        self.gridAndLabelCreator = GridAndLabelCreator()
        self.setupUi(self)
        self.iface = iface
        self.setDialog()
        self.okButton.pressed.connect(self.generate_grid)
        self.cancelButton.pressed.connect(self.cancel)

    def setDialog(self):
        #Unchecking boxes
        self.checkList1 = []
        self.checkList2 = []
        self.checkList3 = []

        for c in self.zoneFrame1.children():
            self.checkList1.append(c) if type(c) == QtWidgets.QCheckBox else ''
        for c in self.zoneFrame2.children():
            self.checkList2.append(c) if type(c) == QtWidgets.QCheckBox else ''
        for c in self.zoneFrame3.children():
            self.checkList3.append(c) if type(c) == QtWidgets.QCheckBox else ''

        for c in self.checkList1:
            c.setChecked(False)
        for c in self.checkList2:
            c.setChecked(False)
        for c in self.checkList3:
            c.setChecked(False)

        self.workCrs = self.layer.crs()
        query = '"'+str(self.id_attr)+'"='+str(self.id_value)
        self.layer.selectByExpression(query, QgsVectorLayer.SelectBehavior(0))
        self.workFeature = self.layer.selectedFeatures()[0]
        self.layer.removeSelection()

        utm = self.UTMcheck(self.workFeature, self.workCrs)
        #Displaying found zones and checking according boxes
        for c in self.checkList1:
            c.setChecked(True) if c.text() in utm else ''
            c.setEnabled(True) if c.text() in utm else ''
        for c in self.checkList2:
            c.setChecked(True) if c.text() in utm else ''
            c.setEnabled(True) if c.text() in utm else ''
        for c in self.checkList3:
            c.setChecked(True) if c.text() in utm else ''
            c.setEnabled(True) if c.text() in utm else ''

        self.generate_grid()
        self.cancel()

    def UTMcheck(self, workFeature, workCrs):
        #Opening UTM Zones layer and finding intersections
        filePathZones = self.pathGpkg()
        zonesLayer = filePathZones + "|layername=Brasil_Fusos"
        zonesMap = QgsVectorLayer(zonesLayer, "zones", "ogr")

        zonesList = zonesMap.getFeatures()
        zones = []

        transformer = QgsCoordinateTransform(workCrs, QgsCoordinateReferenceSystem(4674, QgsCoordinateReferenceSystem.EpsgCrsId), QgsProject.instance())

        geoFeature = workFeature.geometry()
        geoFeature.transform(transformer)

        featureBbox = geoFeature.boundingBox()
        bboxStr = str(featureBbox).replace(',','').replace('>','').split()
        if bboxStr[3] == bboxStr[1] and bboxStr[4] == bboxStr[2]:
            roundedBbox = QgsGeometry.fromPointXY(QgsPointXY(round(float(bboxStr[3]),5), round(float(bboxStr[4]),5)))
        else:
            extentMax = QgsPointXY(round(float(bboxStr[3]),5), round(float(bboxStr[4]),5))
            extentMin = QgsPointXY(round(float(bboxStr[1]),5), round(float(bboxStr[2]),5))
            roundedBbox = QgsGeometry.fromRect(QgsRectangle(extentMin, extentMax))
        
        for i in zonesList:
            if roundedBbox.intersects(i.geometry()):
                zones.append(i[3])

        return zones

    def pathGpkg(self):
        filePath = os.path.dirname(os.path.dirname(__file__))
        filePathGpkg = os.path.join(filePath, "auxiliar", "Brasil_Fusos.gpkg")
        return filePathGpkg

    def generate_grid(self):
        zoneDict = { \
            '18 S':31978,\
            '19 S':31979,\
            '20 S':31980,\
            '21 S':31981,\
            '22 S':31982,\
            '23 S':31983,\
            '24 S':31984,\
            '25 S':31985,\
            '26 S':5396,\
            '19 N':31973,\
            '20 N':31974,\
            '21 N':31975,\
            '22 N':31976,\
            '23 N':6210 \
        }

        zoneChecked = []
        for c in self.checkList1:
            zoneChecked.append(c.text()) if c.isChecked() else ''
        for c in self.checkList2:
            zoneChecked.append(c.text()) if c.isChecked() else ''
        for c in self.checkList3:
            zoneChecked.append(c.text()) if c.isChecked() else ''

        if len(zoneChecked) != 1:
            QMessageBox.critical(self, u"Erro", u"Selecione apenas um fuso UTM.")
            return
        else:
            crstr = QgsCoordinateTransform(self.workCrs, QgsCoordinateReferenceSystem(zoneDict[zoneChecked[0]], QgsCoordinateReferenceSystem.EpsgCrsId), QgsProject.instance())
            workFeature_geometry = self.workFeature.geometry()
            workFeature_geometry.transform(crstr)
            self.gridAndLabelCreator.styleCreator(workFeature_geometry, self.layer, zoneDict[zoneChecked[0]], self.id_attr, self.id_value, self.spacing, self.crossX, self.crossY, self.scale, self.color, self.fontSize, self.font, self.fontLL, self.llcolor, self.linwidth_geo, self.linwidth_utm)
            self.close()

    def cancel(self):
        self.close()