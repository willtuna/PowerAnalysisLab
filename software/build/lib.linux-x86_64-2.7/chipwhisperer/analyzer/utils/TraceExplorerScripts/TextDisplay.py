#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014, NewAE Technology Inc
# All rights reserved.
#
# Author: Colin O'Flynn
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================

from PySide.QtCore import *
from PySide.QtGui import *
from chipwhisperer.common.api.autoscript import AutoScript
from chipwhisperer.common.utils import util
from chipwhisperer.common.utils.parameter import Parameterized, Parameter, setupSetParam
from chipwhisperer.common.ui.CWMainGUI import CWMainGUI


class TextDisplay(Parameterized, AutoScript):
    _name = 'Text Display'

    def __init__(self, parent):
        AutoScript.__init__(self)
        self.parent = parent
        self.getParams().addChildren([
             {'name':'Update/Display Table', 'type':'action', 'action':lambda _:self.updateTable()},
        ])


        self.tablewid = QTableWidget()
        self.tablewid.setRowCount(0)
        self.tablewid.setColumnCount(4)
        self.tablewid.setHorizontalHeaderLabels(["Text In", "Text Out", "Key", "Trace Data"])
        #self.tablewid.verticalHeader().hide()
        #self.tablewid.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.dock = CWMainGUI.getInstance().addDock(self.tablewid, "Text Display Table", area=Qt.TopDockWidgetArea)
        self.dock.hide()

    def updateTable(self):
        self.dock.show()
        tm = CWMainGUI.getInstance().api.getInstance().project().traceManager()
        tend = tm.numTraces()
        self.tablewid.setRowCount(tend)
        for tnum in range(0,tend):
            tin = tm.getTextin(tnum)
            tout = tm.getTextout(tnum)
            k = tm.getKnownKey(tnum)

            self.tablewid.setItem(tnum, 0, QTableWidgetItem(util.list2hexstr(tin)))
            self.tablewid.setItem(tnum, 1, QTableWidgetItem(util.list2hexstr(tout)))
            self.tablewid.setItem(tnum, 2, QTableWidgetItem(util.list2hexstr(k)))
