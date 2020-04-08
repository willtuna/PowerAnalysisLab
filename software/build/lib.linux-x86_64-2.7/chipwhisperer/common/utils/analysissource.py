#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2014, NewAE Technology Inc
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

from chipwhisperer.common.utils import util


class AnalysisSource(object):
    """ It produces an analysis report as output """

    def __init__(self):
        self.sigAnalysisStarted = util.Signal()
        self.sigAnalysisUpdated = util.Signal()
        self.sigAnalysisDone = util.Signal()


class AnalysisObserver(object):
    """ It processes the data from an AnalysisSource when requested """
    
    def __init__(self, analysisSource=None):
        self._analysisSource = None
        self.setAnalysisSource(analysisSource)

    def getAnalysisSource(self):
        return self._analysisSource

    def setAnalysisSource(self, analysisSource):
        if analysisSource:
            analysisSource.sigAnalysisStarted.connect(self.analysisStarted)
            analysisSource.sigAnalysisUpdated.connect(self.analysisUpdated)
            analysisSource.sigAnalysisDone.connect(self.processAnalysis)
        self._analysisSource = analysisSource

    def analysisStarted(self):
        """Setup the environment (i.e. GUI)"""
        pass

    def analysisUpdated(self):
        """Do partial reports"""
        pass

    def processAnalysis(self):
        """Do final report"""
        pass