# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GridGeneratorDockWidget
                                 A QGIS plugin
 Creates UTM and geopgraphic symbology and labels for given bounding feature.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-04-21
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Joao Felipe Aguiar Guimaraes
        email                : joao.felipe@eb.mil.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import QtGui, QtWidgets, uic 
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import pyqtSignal
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox, QgsSpinBox, QgsDoubleSpinBox, QgsColorButton
from qgis.core import QgsVectorLayer
from .Gui.GridLabel import *



FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gridGenerator_dockwidget_base.ui'))


class GridGeneratorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(GridGeneratorDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.mapLayerSelection.layerChanged.connect(self.attributeSelection.setLayer)

        self.okButton.pressed.connect(self.send_inputs)


    def send_inputs(self):

        if (not self.mapLayerSelection.currentLayer()) and (self.attributeSelection.currentField()) and (self.utmSpacing.value()) and (self.crossesX.value()) and (self.crossesY.value()) and (self.mapScale.value()) and (self.gridColor.color()) and (self.labelFontSize.value()) and (self.fontType.currentFont()):
            return

        layer = self.mapLayerSelection.currentLayer()
        attribute = self.attributeSelection.currentField()
        spacing = self.utmSpacing.value()
        crossX = self.crossesX.value()
        crossY = self.crossesY.value()
        scale = self.mapScale.value()
        color = self.gridColor.color()
        fontSize = self.labelFontSize.value()
        font = self.fontType.currentFont()
        GridAndLabelCreator.styleCreator(layer, attribute, spacing, crossX, crossY, scale, color, fontSize, font)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()