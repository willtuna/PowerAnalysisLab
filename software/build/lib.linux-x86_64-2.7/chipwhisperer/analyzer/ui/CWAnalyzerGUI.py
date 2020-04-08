#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2016, NewAE Technology Inc
# All rights reserved.
#
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
import logging
import sys
from chipwhisperer.common.ui.CWMainGUI import CWMainGUI, makeApplication
from PySide.QtGui import *  # DO NOT REMOVE PYSIDE IMPORTS - Required for pyqtgraph to select correct version on some platforms
from PySide.QtCore import Qt
from chipwhisperer.common.ui.KeyScheduleDialog import AesKeyScheduleDialog, DesKeyScheduleDialog
from chipwhisperer.common.api.CWCoreAPI import CWCoreAPI
from chipwhisperer.analyzer.utils.TraceExplorerDialog import TraceExplorerDialog
from chipwhisperer.common.results.base import ResultsBase
from chipwhisperer.common.utils import pluginmanager
from chipwhisperer.common.utils.parameter import Parameter, Parameterized, setupSetParam
from chipwhisperer.common.utils.tracesource import PassiveTraceObserver
from chipwhisperer.analyzer.attacks._base import AttackObserver
from chipwhisperer.analyzer.preprocessing.pass_through import PassThrough
from functools import partial
import inspect

class AttackSettings(Parameterized):
    def __init__(self):
        self._attack = None
        self.valid_attacks = pluginmanager.getPluginsInDictFromPackage("chipwhisperer.analyzer.attacks", True, True)

        self.params = Parameter(name="Attack Settings", type="group")
        self.params.addChildren([
            {'name': 'Attack', 'type':'list', 'values':self.valid_attacks, 'get':self.getAttack, 'set':self.setAttack}
        ])

    @setupSetParam("Attack")
    def setAttack(self, atk):
        self._attack = atk
        if self._attack is not None:
            self.params.append(self._attack.params)

    def getAttack(self):
        return self._attack

class PreprocessingSettings(Parameterized):
    _num_modules = 4
    def __init__(self, api):
        self._api = api
        self.valid_preprocessingModules = pluginmanager.getPluginsInDictFromPackage("chipwhisperer.analyzer.preprocessing", False, False)
        self.params = Parameter(name="Preprocessing Settings", type='group')

        self._moduleParams = [
            Parameter(name='self.ppmod[%d]' % (i), type='group') for i in range(self._num_modules)
        ]
        self._initModules()

        self.params.addChildren([
            {'name':'Selected Modules', 'type':'group', 'children':[
                {'name':'self.ppmod[%d]' % (step), 'type':'list', 'values':self.valid_preprocessingModules,
                 'get':partial(self.getModule, step), 'set':partial(self.setModule, step)} for step in range(0, len(self._modules))
            ]},
        ])
        for m in self._moduleParams:
            self.params.append(m)

    def _initModules(self):
        self._modules = [None]*self._num_modules
        for i in range(self._num_modules):
            mod = PassThrough(name="Preprocessing Module ppmod[%d]" % (i))
            self.setModule(i, mod)

    def getModule(self, num):
        return self._modules[num].__class__

    # TODO: calling this from the command line causes a cosmetic bug
    @setupSetParam("")
    def setModule(self, num, module):
        """Insert the preprocessing module selected from the GUI into the list of active modules.

        This ensures that the options for that module are then displayed in the GUI, along with
        writing the auto-generated script.
        """

        if module is None:
            raise ValueError("Received None as module in setModule()" % module)

        if num == 0:
            trace_source = self._api.project().traceManager()
        else:
            trace_source = self._modules[num-1]

        if self._modules[num] is not None:
            self._modules[num].deregister()
            self._moduleParams[num].clearChildren()

        if inspect.isclass(module):
            module = module(name="Preprocessing Module #%d" % (num+1))

        self._modules[num] = module
        self._modules[num].setTraceSource(trace_source)
        self._moduleParams[num].append(self._modules[num].getParams())

        if (num+1) < len(self._modules) and self._modules[num+1] is not None:
            self._modules[num+1].setTraceSource(module)

    def __getitem__(self, idx):
        return self._modules[idx]

    def __setitem__(self, idx, module):
        self.setModule(idx, module)
        logging.warning("Selected Modules parameter list didn't update during setModule call in PreprocessingSettings")

    def __str__(self):
        return str(self._modules)

    def __repr__(self):
        return str(self)


class CWAnalyzerGUI(CWMainGUI):
    """This is the main API for the ChipWhisperer Analyzer. From CWAnalyzer,
    the Python console has a "self" object that refers to one of these.
    """

    def __init__(self, api):
        self._attackSettings = AttackSettings()
        self._preprocessSettings = PreprocessingSettings(api)

        super(CWAnalyzerGUI, self).__init__(api, name="ChipWhisperer" + u"\u2122" + " Analyzer " + CWCoreAPI.__version__ + "[*]", icon="cwiconA")
        #self.addExampleScripts(pluginmanager.getPluginsInDictFromPackage("chipwhisperer.analyzer.scripts", False, False, self))
        CWAnalyzerGUI.instance = self

#        self.api.setAttack(self.api.valid_attacks.get("CPA", None))


    def projectChanged(self):
        CWMainGUI.projectChanged(self)

    def loadExtraModules(self):
        self.aesKeyScheduleDialog = AesKeyScheduleDialog(self)
        self.desKeyScheduleDialog = DesKeyScheduleDialog(self)

        self.traceExplorerDialog = TraceExplorerDialog(self)

    def addToolbarItems(self, toolbar):
        toolbar.addAction(QAction(QIcon(':/images/attack.png'), 'Start Attack', self, triggered=self.doAnalysis))

    def addToolMenuItems(self):
        self.toolMenu.addAction(QAction('AES Key Schedule', self, statusTip='Show AES Key Schedule calculator',
                                      triggered=self.aesKeyScheduleDialog.show))
        self.toolMenu.addAction(QAction('DES Key Schedule', self, statusTip='Show DES Key Schedule calculator',
                                      triggered=self.desKeyScheduleDialog.show))

    def doAnalysis(self):
        # TODO: remove
        """Called when the 'Do Analysis' button is pressed"""
        self.clearFocus()
        if self.api.project().traceManager().numTraces() == 0:
            ret = QMessageBox.question(self, "Attack Error", "No traces enabled in project.\nOpen Trace Manager?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.traceManagerDialog.show()
            return

        logging.info("Executing analysis...")
        logging.info("Analysis completed")

        helpExampleScriptsDialog = QMessageBox()
        helpExampleScriptsDialog.setWindowTitle('What happened to the "Attack Button"?')
        helpExampleScriptsDialog.setText('ChipWhisperer v4 uses scripting instead of the attack button. '+
                                         'The attack button may be added back in a later release, for now it does not function. ' +
                                         'See <a href="http://wiki.newae.com/cw3to4">http://wiki.newae.com/cw3to4</a> for details.')
        helpExampleScriptsDialog.setTextFormat(Qt.RichText);
        helpExampleScriptsDialog.exec_()

    def addSettingsDocks(self):
        self.settingsAttackDock = self.addSettings(self._attackSettings.params)
        self.settingsPreprocessingDock = self.addSettings(self._preprocessSettings.params)
        self.settingsTraceExplorer = self.addSettings(self.traceExplorerDialog.params)
        self.settingsResultsDock = self.addSettings(ResultsBase.getClassParameter())

        # Load all ActiveTraceObservers
        self.windowMenu.addSeparator()
        for k, v in ResultsBase.getClasses().iteritems():
            if issubclass(v, PassiveTraceObserver) or issubclass(v, AttackObserver):
                ResultsBase.createNew(k)
        self.tabifyDocks(self.resultDocks)

        self.tabifyDocks([self.settingsPreprocessingDock, self.settingsAttackDock,
                          self.settingsTraceExplorer, self.settingsResultsDock])

    @staticmethod
    def getInstance():
        return CWAnalyzerGUI.instance

    @property
    def project(self):
        """The current project loaded in the analyzer."""
        return self.api.project()

    @project.setter
    def project(self, new_project):
        self.api.setProject(new_project)

    @property
    def attack(self):
        """The attack module in use. This should be a subclass of the base class
        AttackBaseClass.
        """
        return self._attackSettings.getAttack()

    @attack.setter
    def attack(self, new_attack):
        self._attackSettings.setAttack(new_attack)

    @property
    def ppmod(self):
        """The preprocessing modules in use. Access like
        >>> self.ppmod[0]
        """
        return self._preprocessSettings

    @property
    def correlation_plot(self):
        """The "Correlations vs Traces in Attack" tab. Shows the output
        statistic for each subkey as traces are added to the attack. Useful for
        checking the progress or success rate of an attack. Read-only.
        """
        return self.api.getResults("Correlation vs Traces in Attack")

    @property
    def output_plot(self):
        """The "Output vs Point Plot" tab. Shows the output statistics at each
        point in the traces. Useful for checking which points provided the
        attackable leakage. Read-only."""
        return self.api.getResults("Output vs Point Plot")

    @property
    def pge_plot(self):
        """The "PGE vs Trace Plot" tab. Shows the PGE (the rank of the correct
        guess) versus the number of traces used in the attack. Useful for
        showing the success rate of an attack. Read-only.
        """
        return self.api.getResults("PGE vs Trace Plot")

    @property
    def trace_plot(self):
        """The "Trace Output Plot" tab. Useful for checking the output of the
        preprocessing modules. Read-only.
        """
        return self.api.getResults("Trace Output Plot")

    @property
    def results_table(self):
        """The "Results Table" tab. Shows ranked correlations (or any statistic)
        for each subkey. Read-only.
        """
        return self.api.getResults("Results Table")



def main():
    # Create the Qt Application
    app = makeApplication("Analyzer")

    # Create and show the GUI
    Parameter.usePyQtGraph = True
    window = CWAnalyzerGUI(CWCoreAPI())
    window.show()

    # Run the main Qt loop
    app.exec_()


if __name__ == '__main__':
    main()
