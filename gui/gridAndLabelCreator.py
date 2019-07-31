from builtins import str, range, abs, round
from math import floor, ceil, pow
from qgis.core import QgsProject, QgsVectorLayer, QgsCoordinateTransform, QgsCoordinateReferenceSystem, \
                      QgsFillSymbol,QgsLineSymbol, QgsSimpleFillSymbolLayer, QgsSingleSymbolRenderer, \
                      QgsInvertedPolygonRenderer, QgsRuleBasedRenderer, QgsPoint, QgsPointXY, QgsGeometry, \
                      QgsGeometryGeneratorSymbolLayer
from qgis.core import QgsRuleBasedLabeling, QgsPalLayerSettings, QgsTextFormat, QgsPropertyCollection, QgsLabelingResults, QgsLabelPosition
from qgis.utils import iface
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QObject


class GridAndLabelCreator(QObject):
	def __init__(self, parent=None):
		super(GridAndLabelCreator, self).__init__()

	def reset(self, layer):
		layer_rst = layer
		properties = {'color': 'black'}
		grid_symb = QgsFillSymbol.createSimple(properties)
		symb_out = QgsSimpleFillSymbolLayer()
		grid_symb.changeSymbolLayer(0, symb_out)
		render_base = QgsSingleSymbolRenderer(grid_symb)
		layer_rst.setRenderer(render_base)
		root_rule = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
		rules = QgsRuleBasedLabeling(root_rule)
		layer_rst.setLabeling(rules)
		layer_rst.setLabelsEnabled(False)
		layer_rst.triggerRepaint()
		return

	def geo_test(self, layer, index, id_attr, id_value, spacing, crossX, crossY, scale, color, fontSize, font, fontLL, llcolor):
		if layer.crs().isGeographic() == False:
			self.styleCreator(layer, index, id_attr, id_value, spacing, crossX, crossY, scale, color, fontSize, font, fontLL, llcolor, True)
		else:
			self.styleCreator(layer, index, id_attr, id_value, spacing, crossX, crossY, scale, color, fontSize, font, fontLL, llcolor, False)
		pass

	def utmLLtransform(self, utmcheck, p1, transf):
		if utmcheck:
			p1.transform(transf)
			return p1
		pass

	def crossLinegenerator(self, xmin_source, ymin_source, px, py, u, t, dx, dy, utmcheck, trLLUTM):
		p1 = QgsPoint(xmin_source+px*u, ymin_source+py*t)
		p2 = QgsPoint(xmin_source+px*u+dx, ymin_source+py*t+dy)
		self.utmLLtransform(utmcheck, p1, trLLUTM)
		self.utmLLtransform(utmcheck, p2, trLLUTM)
		properties = {'color': 'black'}
		line_temp = QgsLineSymbol.createSimple(properties)
		line_temp.setWidth(0.05)
		symb = QgsGeometryGeneratorSymbolLayer.create(properties)
		symb.setSymbolType(1)
		symb.setSubSymbol(line_temp)
		symb.setGeometryExpression('make_line(make_point('+str(p1.x())+',('+str(p1.y())+')),make_point('+str(p2.x())+',('+str(p2.y())+')))')
		return symb

	def gridLinesymbolMaker(self, x1, y1, x2, y2, xmax_source, xmin_source, ymax_source, ymin_source, trUTMLL, trLLUTM, utmcheck, isVertical):
		a1 = QgsPoint(x1, y1)
		a2 = QgsPoint(x2, y2)
		a1.transform(trUTMLL)
		a2.transform(trUTMLL)
		if isVertical:
			p1 = QgsPoint(a1.x(), ymin_source)
			p2 = QgsPoint(a2.x(), ymax_source)
			self.utmLLtransform(utmcheck, p1, trLLUTM)
			self.utmLLtransform(utmcheck, p2, trLLUTM)
		else:
			p1 = QgsPoint(xmin_source, a1.y())
			p2 = QgsPoint(xmax_source, a2.y())
			self.utmLLtransform(utmcheck, p1, trLLUTM)
			self.utmLLtransform(utmcheck, p2, trLLUTM)
		return [a1,a2,p1,p2]

	def utm_Symb_Generator(self, grid_spacing, trUTMLL, trLLUTM, grid_symb, properties, geo_number_x, geo_number_y, UTM_num_x, UTM_num_y, t, u, geo_bound_bb, bound_UTM_bb, utmcheck):
		xmin_source = float(geo_bound_bb.split()[1])
		ymin_source = float(geo_bound_bb.split()[2])
		xmax_source = float(geo_bound_bb.split()[3])
		ymax_source = float(geo_bound_bb.split()[4])
		xmin_UTM = float(bound_UTM_bb.split()[1])
		ymin_UTM = float(bound_UTM_bb.split()[2])
		xmax_UTM = float(bound_UTM_bb.split()[3])
		ymax_UTM = float(bound_UTM_bb.split()[4])
		test_line = [None]*2
		properties = {'color': 'black'}
		line_temp = QgsLineSymbol.createSimple(properties)
		line_temp.setWidth(0.05)
		symb = QgsGeometryGeneratorSymbolLayer.create(properties)
		symb.setSymbolType(1)
		symb.setSubSymbol(line_temp)

		#Test First And Last Grid Lines
		#Vertical
		if (t == 1 and u == 0) or (t == UTM_num_x and u == 0):
			#Symbol vertices
			auxPointlist = self.gridLinesymbolMaker(((floor(xmin_UTM/grid_spacing)+t)*grid_spacing), ymin_UTM, ((floor(xmin_UTM/grid_spacing)+t)*grid_spacing), ymax_UTM, xmax_source, xmin_source, ymax_source, ymin_source, trUTMLL, trLLUTM, utmcheck, True)
			#0: left bound; 1: right bound
			test_line[0] = QgsGeometry.fromWkt('LINESTRING ('+str(xmin_source)+' '+str(ymin_source)+','+str(xmin_source)+' '+str(ymax_source)+')')
			test_line[1] = QgsGeometry.fromWkt('LINESTRING ('+str(xmax_source)+' '+str(ymin_source)+','+str(xmax_source)+' '+str(ymax_source)+')')
			test_grid = QgsGeometry.fromPolyline([auxPointlist[0],auxPointlist[1]])
			if test_line[0].intersects(test_grid):
				mid_point = test_line[0].intersection(test_grid).vertexAt(0)
				self.utmLLtransform(utmcheck, mid_point, trLLUTM)
				if auxPointlist[0].x() > auxPointlist[1].x():
					symb.setGeometryExpression('make_line(make_point('+str(auxPointlist[2].x())+','+str(auxPointlist[2].y())+'), make_point('+str(mid_point.x())+','+str(mid_point.y())+'))')
				else:
					symb.setGeometryExpression('make_line(make_point('+str(mid_point.x())+','+str(mid_point.y())+'), make_point('+str(auxPointlist[3].x())+','+str(auxPointlist[3].y())+'))')
			elif test_line[1].intersects(test_grid):
				mid_point = test_line[1].intersection(test_grid).vertexAt(0)
				self.utmLLtransform(utmcheck, mid_point, trLLUTM)
				if auxPointlist[0].x() < auxPointlist[1].x():
					symb.setGeometryExpression('make_line(make_point('+str(auxPointlist[2].x())+','+str(auxPointlist[2].y())+'), make_point('+str(mid_point.x())+','+str(mid_point.y())+'))')
				else:
					symb.setGeometryExpression('make_line(make_point('+str(mid_point.x())+','+str(mid_point.y())+'), make_point('+str(auxPointlist[3].x())+','+str(auxPointlist[3].y())+'))')
			else:
				symb.setGeometryExpression('make_line(make_point('+str(auxPointlist[2].x())+','+str(auxPointlist[2].y())+'), make_point('+str(auxPointlist[3].x())+','+str(auxPointlist[3].y())+'))')

		#Horizontal
		elif (u == 1 and t == 0) or (u == UTM_num_y and t == 0):
			#Symbol vertices
			auxPointlist = self.gridLinesymbolMaker(xmin_UTM, ((floor(ymin_UTM/grid_spacing)+u)*grid_spacing), xmax_UTM, ((floor(ymin_UTM/grid_spacing)+u)*grid_spacing), xmax_source, xmin_source, ymax_source, ymin_source, trUTMLL, trLLUTM, utmcheck, False)
			#0: bottom bound; 1: upper bound
			test_line[0] = QgsGeometry.fromWkt('LINESTRING ('+str(xmin_source)+' '+str(ymin_source)+','+str(xmax_source)+' '+str(ymin_source)+')')
			test_line[1] = QgsGeometry.fromWkt('LINESTRING ('+str(xmin_source)+' '+str(ymax_source)+','+str(xmax_source)+' '+str(ymax_source)+')')
			test_grid = QgsGeometry.fromPolyline([auxPointlist[0],auxPointlist[1]])
			if test_line[0].intersects(test_grid):
				mid_point = test_line[0].intersection(test_grid).vertexAt(0)
				self.utmLLtransform(utmcheck, mid_point, trLLUTM)
				if auxPointlist[0].y() > auxPointlist[1].y():
					symb.setGeometryExpression('make_line(make_point('+str(auxPointlist[2].x())+','+str(auxPointlist[2].y())+'), make_point('+str(mid_point.x())+','+str(mid_point.y())+'))')
				else:
					symb.setGeometryExpression('make_line(make_point('+str(mid_point.x())+','+str(mid_point.y())+'), make_point('+str(auxPointlist[3].x())+','+str(auxPointlist[3].y())+'))')
			elif test_line[1].intersects(test_grid):
				mid_point = test_line[1].intersection(test_grid).vertexAt(0)
				self.utmLLtransform(utmcheck, mid_point, trLLUTM)
				if auxPointlist[0].y() < auxPointlist[1].y():
					symb.setGeometryExpression('make_line(make_point('+str(auxPointlist[2].x())+','+str(auxPointlist[2].y())+'), make_point('+str(mid_point.x())+','+str(mid_point.y())+'))')
				else:
					symb.setGeometryExpression('make_line(make_point('+str(mid_point.x())+','+str(mid_point.y())+'), make_point('+str(auxPointlist[3].x())+','+str(auxPointlist[3].y())+'))')
			else:
				symb.setGeometryExpression("make_line(make_point("+str(auxPointlist[2].x())+","+str(auxPointlist[2].y())+"), make_point("+str(auxPointlist[3].x())+","+str(auxPointlist[3].y())+"))")

		#Inner Grid Lines
		#Vertical
		elif (not(t == 1)) and (not(t == UTM_num_x)) and u == 0:
			auxPointlist = self.gridLinesymbolMaker(((floor(xmin_UTM/grid_spacing)+t)*grid_spacing), ymin_UTM, ((floor(xmin_UTM/grid_spacing)+t)*grid_spacing), ymax_UTM, xmax_source, xmin_source, ymax_source, ymin_source, trUTMLL, trLLUTM, utmcheck, True)
			symb.setGeometryExpression('make_line(make_point('+str(auxPointlist[2].x())+','+str(auxPointlist[2].y())+'), make_point('+str(auxPointlist[3].x())+','+str(auxPointlist[3].y())+'))')
		#Horizontal
		elif (not(u == 1)) and (not(u == UTM_num_y)) and t == 0:
			auxPointlist = self.gridLinesymbolMaker(xmin_UTM, ((floor(ymin_UTM/grid_spacing)+u)*grid_spacing), xmax_UTM, ((floor(ymin_UTM/grid_spacing)+u)*grid_spacing), xmax_source, xmin_source, ymax_source, ymin_source, trUTMLL, trLLUTM, utmcheck, False)
			symb.setGeometryExpression("make_line(make_point("+str(auxPointlist[2].x())+","+str(auxPointlist[2].y())+"), make_point("+str(auxPointlist[3].x())+","+str(auxPointlist[3].y())+"))")

		grid_symb.appendSymbolLayer(symb)
		return grid_symb

	def grid_labeler(self, coord_base_x, coord_base_y, px, py, u, t, dx, dy, vAlign, hAlign, desc, fSize, fontType, expression_str, trLLUTM, trUTMLL, llcolor, utmcheck, scale):
		if utmcheck:
			pgrid = QgsPoint(coord_base_x + px*u, coord_base_y + py*t)
			pgrid.transform(trLLUTM)
			pgrid = QgsPoint(pgrid.x()+ dx, pgrid.y()+ dy)
		else:
			pgrid = QgsPoint(coord_base_x + px*u + dx, coord_base_y + py*t + dy)
		#Label Format Settings
		settings = QgsPalLayerSettings()
		settings.Placement = QgsPalLayerSettings.Free
		settings.isExpression = True
		textprop = QgsTextFormat()
		textprop.setColor(llcolor)
		textprop.setSizeUnit(1)
		textprop.setSize(fSize*scale*1.324)
		textprop.setFont(QFont(fontType))
		textprop.setLineHeight(1)
		settings.setFormat(textprop)
		settings.fieldName = expression_str

		#Label Name and Position
		datadefined = QgsPropertyCollection()
		datadefined.setProperty(9, pgrid.x())
		datadefined.setProperty(10, pgrid.y())
		if not(hAlign == ''):
			datadefined.setProperty(11, hAlign)
		if not(vAlign == ''):
			datadefined.setProperty(12, vAlign)
		datadefined.setProperty(20, 1)

		#Creating and Activating Labeling Rule
		settings.setDataDefinedProperties(datadefined)
		rule = QgsRuleBasedLabeling.Rule(settings)
		rule.setDescription(desc)
		rule.setActive(True)

		return rule

	def utm_grid_labeler(self, x_UTM, y_UTM, x_geo, y_geo, px, py, trUTMLL, trLLUTM, u, isVertical, dx, dy, dyO, dy1, label_index, vAlign, hAlign, desc, fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangetest):
		# Check if is labeling grid's vertical lines
		x_min = float(geo_bound_bb.split()[1])
		y_min = float(geo_bound_bb.split()[2])
		x_max = float(geo_bound_bb.split()[3])
		y_max = float(geo_bound_bb.split()[4])
		if isVertical:
			# Displacing UTM Label that overlaps Geo Label
			if utmcheck:
				dx0 = 0
			else:
				dx0 = dx
				dx = 0
			test_plac = QgsPoint(((floor(x_UTM/grid_spacing)+u)*grid_spacing),y_UTM)
			test_plac.transform(trUTMLL)
			ancX = QgsPoint(((floor(x_UTM/grid_spacing)+u)*grid_spacing)+dx,y_UTM)
			ancX.transform(trUTMLL)
			ancY = QgsPoint(ancX.x(),y_geo)
			if utmcheck:
				ancY.transform(trLLUTM)
			test = QgsPoint(((floor(x_UTM/grid_spacing)+u)*grid_spacing),y_UTM)
			test.transform(trUTMLL)
			if u == 1:
				deltaDneg = 0.0014
				deltaDpos = 0.0016
			else:
				deltaDneg = 0.0010
				deltaDpos = 0.0015
			testif = abs(floor(abs(round(test.x(), 4) - (x_min % (px)) - (deltaDneg*(fSize/1.5) *scale/10))/px) - floor(abs(round(test.x(), 4) - (x_min % (px)) + (deltaDpos*(fSize/1.5) *scale/10))/px))
			if testif >= 1:
				ancY = QgsPoint(ancY.x(),ancY.y()+dyO)
			else:
				ancY = QgsPoint(ancY.x(),ancY.y()+dy)
			x = ancX.x() + dx0
			if utmcheck:
				ancY.transform(trUTMLL)
			y =ancY.y()
			full_label = str((floor(x_UTM/grid_spacing)+u)*grid_spacing)
			if test_plac.x() < (x_min + (0.0005 *scale/10)) or test_plac.x() > (x_max - (0.0005 *scale/10)):
				return self.grid_labeler(x, y, 0, 0, 0, 0, 0, 0, vAlign, hAlign, desc, fSize, fontType, '', trLLUTM, trUTMLL, QColor('black'), utmcheck, scale)

		# Labeling grid's horizontal lines
		else:
			test_plac = QgsPoint(x_UTM,(floor(y_UTM/grid_spacing)+u)*grid_spacing)
			test_plac.transform(trUTMLL)
			ancX = QgsPoint(x_UTM,(floor(y_UTM/grid_spacing)+u)*grid_spacing)
			ancX.transform(trUTMLL)
			ancX = QgsPoint(x_geo, ancX.y())
			ancY = QgsPoint(x_geo, ancX.y())
			if utmcheck:
				ancY.transform(trLLUTM)
			# Displacing UTM Label it overlaps with Geo Label
			test = QgsPoint(x_UTM,(floor(y_UTM/grid_spacing)+u)*grid_spacing)
			test.transform(trUTMLL)
			testif = abs(floor(abs(round(test.y(), 4) - (y_min % (py)) - (0.0004*(fSize/1.5) *scale/10))/py) - floor(abs(round(test.y(), 4) - (y_min % (py)))/py))
			if testif >= 1:
				ancY = QgsPoint(ancY.x(),ancY.y()+dy1)
			else:
				testif2 = abs(floor(abs(round(test.y(), 4) - (y_min % (py)))/py) - floor(abs(round(test.y(), 4) - (y_min % (py)) + (0.0004*(fSize/1.5) *scale/10))/py))
				if testif2 >= 1:
					ancY = QgsPoint(ancY.x(),ancY.y()+dyO)
				else:
					ancY = QgsPoint(ancY.x(),ancY.y()+dy)
			if utmcheck:
				dx0 = 0
				ancX.transform(trLLUTM)
				ancX = QgsPoint(ancX.x()+dx, ancX.y())
				ancX.transform(trUTMLL)
				ancY.transform(trUTMLL)
			else:
				dx0 = dx
			x = ancX.x() + dx0
			y = ancY.y()
			full_label = str((floor(y_UTM/grid_spacing)+u)*grid_spacing)
			if test_plac.y() < (y_min + (0.0002 *scale/10)) or test_plac.y() > (y_max- (0.0002 *scale/10)):
				return self.grid_labeler(x, y, 0, 0, 0, 0, 0, 0, vAlign, hAlign, desc, fSize, fontType, '', trLLUTM, trUTMLL, QColor('black'), utmcheck, scale)

		if label_index == 1:
			expression_str = full_label[ : -5]
			fontType.setWeight(50)
		elif label_index == 2:
			expression_str = str('\'')+full_label[-5 : -3]+str('\'')
			fSize = fSize*5/3
			fontType.setWeight(57)
			if len(expression_str) == 3:
				hAlign = 'Left'
		elif label_index == 3:
			expression_str = str('\'')+full_label[-3 : ]+str('\'')
			if u == min(rangetest) and (('Bot' in desc) or ('Left' in desc)):
				expression_str =str('\'')+full_label[-3 : ]+str('m\'')
			fontType.setWeight(50)
		elif label_index == 4:
			expression_str = ''
			if u == min(rangetest):
				expression_str = '\'N\''
				if isVertical:
					expression_str = '\'E\''
				fSize = fSize*5/3
				fontType.setWeight(57)

		ruleUTM = self.grid_labeler(x, y, 0, 0, 0, 0, 0, 0, vAlign, hAlign, desc, fSize, fontType, expression_str, trLLUTM, trUTMLL, QColor('black'), utmcheck, scale)
		return ruleUTM

#	def labelOverlapFix(rules, j):
#		rlList = rules.children()
#		for u in range(2,j+1):
#			lblSettings = rlList[-u].settings()
#			pos = QgsPointXY(lblSettings.Property(9), lblSettings1.Property(10))
#			lolPos = QgsLabelingResults().labelsAtPosition(pos)
#			dx = lblPos[0].width()
#			lblSettingsBase = rlList[-u+1].settings()
#			x = lblSettingsBase.Property(9)
#			if 'Right' in rlList[-u].description:
#				dx = -dx 
#			datadefined = QgsPropertyCollection()
#			datadefined.setProperty(9, x - dx)
#			lblSettings.setDataDefinedProperties(datadefined)
#		return rlList

	def conv_dec_gms(self, base_coord, coord_spacing, u, neg_character, pos_character):
		xbase = base_coord + coord_spacing*u
		x = abs(xbase)
		xdeg = floor(round(x,4))
		xmin = floor(round(((x - xdeg)*60),4))
		xseg = floor(round(((x - xdeg - xmin/60)*60),4))
		if xbase < 0:
			xhem = neg_character
		else:
			xhem = pos_character
		conv_exp_str = '\'' + str(xdeg).rjust(2,'0') + 'º ' + str(xmin).rjust(2,'0') + str('\\') + str('\' ') + str(xseg).rjust(2,'0') + '"\'' + '+\' ' + str(xhem) + '\''
		
		return conv_exp_str

	def geoGridcreator(self, grid_symb, geo_bound_bb, geo_number_x, geo_number_y, scale, utmcheck, trLLUTM):
		xmin_source = float(geo_bound_bb.split()[1])
		ymin_source = float(geo_bound_bb.split()[2])
		xmax_source = float(geo_bound_bb.split()[3])
		ymax_source = float(geo_bound_bb.split()[4])
		
		px = (xmax_source-xmin_source)/(geo_number_x+1)
		py = (ymax_source-ymin_source)/(geo_number_y+1)
		
		for u in range(1, (geo_number_x+2)):
			for t in range(0, (geo_number_y+2)):
				symb_cross = self.crossLinegenerator(xmin_source, ymin_source, px, py, u, t, -0.00002145*scale, 0, utmcheck, trLLUTM)
				grid_symb.appendSymbolLayer(symb_cross)
		for u in range(0, (geo_number_x+2)):
			for t in range(1, (geo_number_y+2)):
				symb_cross = self.crossLinegenerator(xmin_source, ymin_source, px, py, u, t, 0, -0.00002145*scale, utmcheck, trLLUTM)
				grid_symb.appendSymbolLayer(symb_cross)
		for u in range(0, (geo_number_x+1)):
			for t in range(0, (geo_number_y+2)):
				symb_cross = self.crossLinegenerator(xmin_source, ymin_source, px, py, u, t, 0.00002145*scale, 0, utmcheck, trLLUTM)
				grid_symb.appendSymbolLayer(symb_cross)
		for u in range(0, (geo_number_x+2)):
			for t in range(0, (geo_number_y+1)):
				symb_cross = self.crossLinegenerator(xmin_source, ymin_source, px, py, u, t, 0, 0.00002145*scale, utmcheck, trLLUTM)
				grid_symb.appendSymbolLayer(symb_cross)
		
		return grid_symb

	def geoGridlabelPlacer(self, geo_bound_bb, geo_number_x, geo_number_y, dx, dy, fSize, LLfontType, trLLUTM, trUTMLL, llcolor, utmcheck, scale):
		xmin_source = float(geo_bound_bb.split()[1])
		ymin_source = float(geo_bound_bb.split()[2])
		xmax_source = float(geo_bound_bb.split()[3])
		ymax_source = float(geo_bound_bb.split()[4])
	
		px = (xmax_source-xmin_source)/(geo_number_x+1)
		py = (ymax_source-ymin_source)/(geo_number_y+1)
	
		root_rule = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
	
		#Upper
		for u in range(0, geo_number_x+2):
			if u ==0:
				ruletemp = self.grid_labeler (xmin_source, ymax_source, px, py, u, 0, 0, dy[0], '', 'Center', 'Up '+str(u+1), fSize, LLfontType, str(self.conv_dec_gms(xmin_source, px, u, 'W', 'E'))+'+\'. GREENWICH\'', trLLUTM, trUTMLL, llcolor, utmcheck, scale)
				root_rule.appendChild(ruletemp)
			else:
				ruletemp = self.grid_labeler (xmin_source, ymax_source, px, py, u, 0, 0, dy[0], '', 'Center', 'Up '+str(u+1), fSize, LLfontType, self.conv_dec_gms(xmin_source, px, u, 'W', 'E'), trLLUTM, trUTMLL, llcolor, utmcheck, scale)
				root_rule.appendChild(ruletemp)
		#Bottom
		for b in range(0, geo_number_x+2):
			ruletemp = self.grid_labeler (xmin_source, ymin_source, px, py, b, 0, 0, dy[1], '', 'Center', 'Bot '+str(b+1), fSize, LLfontType, self.conv_dec_gms(xmin_source, px, b, 'W', 'E'), trLLUTM, trUTMLL, llcolor,  utmcheck, scale)
			root_rule.appendChild(ruletemp)
		#Right
		for r in range(0, geo_number_y+2):
			ruletemp = self.grid_labeler (xmax_source, ymin_source, px, py, 0, r, dx[0], 0, 'Half', '', 'Right '+str(r+1), fSize, LLfontType, self.conv_dec_gms(ymin_source, py, r, 'S', 'N'), trLLUTM, trUTMLL, llcolor, utmcheck, scale)
			root_rule.appendChild(ruletemp)
		#Left
		for l in range(0, geo_number_y+2):
			ruletemp = self.grid_labeler (xmin_source, ymin_source, px, py, 0, l, dx[1], 0, 'Half', '', 'Left '+str(l+1), fSize, LLfontType, self.conv_dec_gms(ymin_source, py, l, 'S', 'N'), trLLUTM, trUTMLL, llcolor, utmcheck, scale)
			root_rule.appendChild(ruletemp)
	
		return root_rule

	def utmGridlabelPlacer(self, root_rule, grid_spacing, geo_bound_bb, bound_UTM_bb, geo_number_x, geo_number_y, UTM_num_x, UTM_num_y, trUTMLL, trLLUTM, dx, dy, dy0, dy1, fSize, fontType, scale, utmcheck):
		xmin_source = float(geo_bound_bb.split()[1])
		ymin_source = float(geo_bound_bb.split()[2])
		xmax_source = float(geo_bound_bb.split()[3])
		ymax_source = float(geo_bound_bb.split()[4])
		xmin_UTM = float(bound_UTM_bb.split()[1])
		ymin_UTM = float(bound_UTM_bb.split()[2])
		xmax_UTM = float(bound_UTM_bb.split()[3])
		ymax_UTM = float(bound_UTM_bb.split()[4])
		px = (xmax_source-xmin_source)/(geo_number_x+1)
		py = (ymax_source-ymin_source)/(geo_number_y+1)

		if grid_spacing > 0:
			ruletest = self.utm_grid_labeler (xmin_UTM, ymin_UTM, 0, ymin_source, px, py, trUTMLL, trLLUTM, 1, True,dx[0], dy[1], dy0[1], 0, 1, '', '', 'UTMBot'+'Test', fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
			if ruletest.settings().fieldName == '':
				rangeUD = range(2, UTM_num_x+1)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymax_UTM, 0, ymax_source, px, py, trUTMLL, trLLUTM, 1, True, dx[0], dy[0], dy0[0], 0, 1, 'Bottom', '', 'UTMUp'+str(1), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymax_UTM, 0, ymax_source, px, py, trUTMLL, trLLUTM, 1, True, 0, dy[0]-1.3*(scale)*fSize/1.5, dy0[0]-1.3*(scale)*fSize/1.5, 0, 2, 'Bottom', 'Center', 'UTMUp'+str(1), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymax_UTM, 0, ymax_source, px, py, trUTMLL, trLLUTM, 1, True, dx[1], dy[0], dy0[0], 0, 3, 'Bottom', '', 'UTMUp'+str(1), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
				root_rule.appendChild(ruletemp)
			else:
				rangeUD = range(1, UTM_num_x+1)
			for u in rangeUD:
				# Upper
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymax_UTM, 0, ymax_source, px, py, trUTMLL, trLLUTM, u, True, dx[0], dy[0], dy0[0], 0, 1, 'Bottom', '', 'UTMUp'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymax_UTM, 0, ymax_source, px, py, trUTMLL, trLLUTM, u, True, 0, dy[0]-1.3*(scale)*fSize/1.5, dy0[0]-1.3*(scale)*fSize/1.5, 0, 2, 'Bottom', 'Center', 'UTMUp'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymax_UTM, 0, ymax_source, px, py, trUTMLL, trLLUTM, u, True, dx[1], dy[0], dy0[0], 0, 3, 'Bottom', '', 'UTMUp'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)
				# Bottom
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, 0, ymin_source, px, py, trUTMLL, trLLUTM, u, True,dx[0], dy[1], dy0[1], 0, 1, 'Top', '', 'UTMBot'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, 0, ymin_source, px, py, trUTMLL, trLLUTM, u, True, 0, dy[1]+0.4*(scale)*fSize/1.5, dy0[1]+0.4*(scale)*fSize/1.5, 0, 2, 'Top', 'Center', 'UTMBot'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, 0, ymin_source, px, py, trUTMLL, trLLUTM, u, True, dx[1], dy[1], dy0[1], 0, 3, 'Top', '', 'UTMBot'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, 0, ymin_source, px, py, trUTMLL, trLLUTM, u, True, dx[8], dy[1]+0.4*(scale)*fSize/1.5, dy0[1]+0.4*(scale)*fSize/1.5, 0, 4, 'Top', '', 'UTMBot'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeUD)
				root_rule.appendChild(ruletemp)

			ruletest = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, 1, False, dx[2]-3.0*scale*fSize/1.5, dy[2], dy0[2], dy1[0], 1, '', '', 'UTMLeft'+'Test', fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
			if ruletest.settings().fieldName == '':
				rangeLat = range(2, UTM_num_y+1)
				ruletemp = self.utm_grid_labeler (xmax_UTM, ymin_UTM, xmax_source, 0, px, py, trUTMLL, trLLUTM, 1, False, dx[5], dy[2], dy0[2], dy1[0], 1, '', '', 'UTMRight'+str(1), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmax_UTM, ymin_UTM, xmax_source, 0, px, py, trUTMLL, trLLUTM, 1, False, dx[6], dy[3], dy0[3], dy1[1], 2, '', 'Center', 'UTMRight'+str(1), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmax_UTM, ymin_UTM, xmax_source, 0, px, py, trUTMLL, trLLUTM, 1, False, dx[7], dy[2], dy0[2], dy1[0], 3, '', '', 'UTMRight'+str(1), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, range(1))
				root_rule.appendChild(ruletemp)
			else:
				rangeLat = range(1, UTM_num_y+1)
			for u in rangeLat:
				# Left
				if u == min(rangeLat):
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[2]-3.1*scale*fSize/1.5, dy[2], dy0[2], dy1[0], 1, 'Bottom', '', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[3]-3.1*scale*fSize/1.5, dy[3], dy0[3], dy1[1], 2, 'Bottom', 'Center', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[4]-3.1*scale*fSize/1.5, dy[2], dy0[2], dy1[0], 3, 'Bottom', '', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[9], dy[3], dy0[3], dy1[1], 4, 'Bottom', '', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
				else:
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[2], dy[2], dy0[2], dy1[0], 1, 'Bottom', '', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[3], dy[3], dy0[3], dy1[1], 2, 'Bottom', 'Center', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
					ruletemp = self.utm_grid_labeler (xmin_UTM, ymin_UTM, xmin_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[4], dy[2], dy0[2], dy1[0], 3, 'Bottom', '', 'UTMLeft'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
					root_rule.appendChild(ruletemp)
				# Right
				ruletemp = self.utm_grid_labeler (xmax_UTM, ymin_UTM, xmax_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[5], dy[2], dy0[2], dy1[0], 1, 'Bottom', '', 'UTMRight'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmax_UTM, ymin_UTM, xmax_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[6], dy[3], dy0[3], dy1[1], 2, 'Bottom', 'Center', 'UTMRight'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
				root_rule.appendChild(ruletemp)
				ruletemp = self.utm_grid_labeler (xmax_UTM, ymin_UTM, xmax_source, 0, px, py, trUTMLL, trLLUTM, u, False, dx[7], dy[2], dy0[2], dy1[0], 3, 'Bottom', '', 'UTMRight'+str(u), fSize, fontType, grid_spacing, scale, utmcheck, geo_bound_bb, rangeLat)
				root_rule.appendChild(ruletemp)
		
		return root_rule

	def styleCreator(self, layer, index, id_attr, id_value, spacing, crossX, crossY, scale, color, fontSize, font, fontLL, llcolor, utmcheck):
		"""Getting Input Data For Grid Generation"""
		grid_spacing = spacing
		geo_number_x = crossX
		geo_number_y = crossY
		fSize = fontSize
		fontType = font
		LLfontType = fontLL

		#Loading feature
		layer_bound = layer
		query = '"'+str(id_attr)+'"='+str(id_value)
		layer_bound.selectByExpression(query, QgsVectorLayer.SelectBehavior(0))
		feature_bound = layer_bound.selectedFeatures()[0]
		layer_bound.removeSelection()

		#Getting Feature Source CRS and Geometry
		if utmcheck:
			feature_geometry = feature_bound.geometry()
			bound_UTM = layer_bound.crs().authid()
			feature_bbox = feature_geometry.boundingBox()
			bound_UTM_bb = str(feature_bbox).replace(',','').replace('>','')
			# Transforming to Geographic
			transform_feature = QgsCoordinateTransform(QgsCoordinateReferenceSystem(bound_UTM), QgsCoordinateReferenceSystem('EPSG:4674'), QgsProject.instance())
			feature_geometry.transform(transform_feature)
			bound_sourcecrs = 'EPSG:4674'
			feature_bbox = feature_geometry.boundingBox()
		else:
			feature_geometry = feature_bound.geometry()
			bound_sourcecrs = layer_bound.crs().authid()
			feature_bbox = feature_geometry.boundingBox()
		geo_bound_bb = str(feature_bbox).replace(',','').replace('>','')

		#Defining CRSs Transformations
		inom = feature_bound[index]
		if inom[0]=='N': 
			bound_UTM = 'EPSG:319' + str(72 + int(inom[3:5])-18)
		elif inom[0]=='S': 
			bound_UTM = 'EPSG:319' + str(78 + int(inom[3:5])-18) 
		else:
			iface.messageBar().pushMessage("Error", "Invalid index attribute", level=Qgis.Critical)
			return
		trLLUTM = QgsCoordinateTransform(QgsCoordinateReferenceSystem(bound_sourcecrs), QgsCoordinateReferenceSystem(bound_UTM), QgsProject.instance())
		trUTMLL = QgsCoordinateTransform(QgsCoordinateReferenceSystem(bound_UTM), QgsCoordinateReferenceSystem(bound_sourcecrs), QgsProject.instance())

		#Defining UTM Grid Symbology Type
		renderer = layer.renderer()
		properties = {'color': 'black'}
		grid_symb = QgsFillSymbol.createSimple(properties)
		symb_out = QgsSimpleFillSymbolLayer()
		symb_out.setStrokeColor(QColor('black'))
		symb_out.setFillColor(QColor('white'))
		symb_out.setStrokeWidth(0.05)

		""" Creating UTM Grid """
		if not utmcheck:
			geo_UTM = feature_bound.geometry()
			geo_UTM.transform(trLLUTM)
			bound_UTM_bb = str(geo_UTM.boundingBox()).replace(',','').replace('>','')
		xmin_UTM = float(bound_UTM_bb.split()[1])
		ymin_UTM = float(bound_UTM_bb.split()[2])
		xmax_UTM = float(bound_UTM_bb.split()[3])
		ymax_UTM = float(bound_UTM_bb.split()[4])

		if grid_spacing > 0:
			UTM_num_x = floor(xmax_UTM/grid_spacing) - floor(xmin_UTM/grid_spacing)
			UTM_num_y = floor(ymax_UTM/grid_spacing) - floor(ymin_UTM/grid_spacing)
			#Generating Vertical Lines
			for x in range(1, UTM_num_x+1):
				grid_symb= self.utm_Symb_Generator (grid_spacing, trUTMLL, trLLUTM, grid_symb, properties, geo_number_x, geo_number_y, UTM_num_x, UTM_num_y, x, 0, geo_bound_bb, bound_UTM_bb, utmcheck)
			#Generating Horizontal Lines
			for y in range(1, UTM_num_y+1):
				grid_symb = self.utm_Symb_Generator (grid_spacing, trUTMLL, trLLUTM, grid_symb, properties, geo_number_x, geo_number_y, UTM_num_x, UTM_num_y, 0, y, geo_bound_bb, bound_UTM_bb, utmcheck)

		""" Creating Geo Grid """
		grid_symb = self.geoGridcreator(grid_symb, geo_bound_bb, geo_number_x, geo_number_y, scale, utmcheck, trLLUTM)

		""" Rendering UTM and Geographic Grid """
		#Changing UTM Grid Color
		grid_symb.setColor(color)
		grid_symb.changeSymbolLayer(0, symb_out)
		#Creating Rule Based Renderer (Rule For The Other Features)
		properties = {'color': 'white'}
		ext_grid_symb = QgsFillSymbol.createSimple(properties)
		symb_ot = QgsRuleBasedRenderer.Rule(ext_grid_symb)
		symb_ot.setFilterExpression('\"'+str(id_attr)+'\" <> '+str(id_value))
		symb_ot.setLabel('other')
		#Creating Rule Based Renderer (Rule For The Selected Feature, Root Rule)
		symb_new = QgsRuleBasedRenderer.Rule(grid_symb)
		symb_new.setFilterExpression('\"'+str(id_attr)+'\" = '+str(id_value))
		symb_new.setLabel('layer')
		symb_new.appendChild(symb_ot)
		#Applying New Renderer
		render_base = QgsRuleBasedRenderer(symb_new)
		new_renderer = QgsInvertedPolygonRenderer.convertFromRenderer(render_base)
		layer_bound.setRenderer(new_renderer)

		""" Labeling Geo Grid """
		if utmcheck:
			dx = [2*scale*fSize/1.5, -13.6*scale*fSize/1.5]
			dy = [1.7*scale*fSize/1.5, -3.8*scale*fSize/1.5]
		else:
			dx = [0.000018*scale, -0.000120*scale]
			dy = [0.000015*scale, -0.000040*scale]

		root_rule = self.geoGridlabelPlacer(geo_bound_bb, geo_number_x, geo_number_y, dx, dy, fSize, LLfontType, trLLUTM, trUTMLL, llcolor, utmcheck, scale)

		""" Labeling UTM Grid"""
		if utmcheck:
			dx = [-2.7, 1.8, -9.7, -6.2, -4.6, 2, 5.4, 7.0, 6.1, -3.5]
			dx = [i*scale*fSize/1.5 for i in dx]
			dy = [2.5, -1.7, -0.5, -1.5]
			dy = [i*scale*fSize/1.5 for i in dy]
			dy0 = [5.45, -4.8, -3.2, -4.2]
			dy0 = [i*scale*fSize/1.5 for i in dy0]
			dy1 = [2.15, 1.2]
			dy1 = [i*scale*fSize/1.5 for i in dy1]
		else:
			dx = [-0.00003, 0.000018, -0.000107, -0.000070, -0.000053, 0.000023, 0.000060, 0.000079]
			dx = [i*scale*fSize/1.5 for i in dx]
			dy = [0.000027, 0.000016, -0.000041, -0.000052, -0.000003, -0.000015]
			dy = [i*scale*fSize/1.5 for i in dy]
			dy0 = [0.0000644, 0.000053, -0.000076, -0.000087, 0.000064, 0.000052]
			dy0 = [i*scale*fSize/1.5 for i in dy0]
			dy1 = [0.000032, 0.000020]
			dy1 = [i*scale*fSize/1.5 for i in dy1]

		root_rule = self.utmGridlabelPlacer(root_rule, grid_spacing, geo_bound_bb, bound_UTM_bb, geo_number_x, geo_number_y, UTM_num_x, UTM_num_y, trUTMLL, trLLUTM, dx, dy, dy0, dy1, fSize, fontType, scale, utmcheck)

		""" Activating Labels """
		rules = QgsRuleBasedLabeling(root_rule)
		layer.setLabeling(rules)
		layer.setLabelsEnabled(True)
		layer.triggerRepaint()
		return
