# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

from lsst.pex.logging import Log
import lsst.coadd.chisquared as coaddChiSq
import baseStage

class ChiSquaredStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to create a chi-squared coadd

    For now, the coadd has the same dimensions and WCS as the first exposure
    or the next exposure after processing an event with isLastExposure = True.
    
    The coadd is written to the clipboard when an event is processed with isLastExposure = True.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "chiSquaredStage_dict.paf"
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        self.coadd = None

    def process(self, clipboard):
        """Add exposure to chiSquared coadd"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key
#         print "self.coadd=", self.coadd, "at start of process"

        exposure = self.getFromClipboard(clipboard, "exposure")
        
        if not self.coadd:
            self.log.log(Log.INFO, "First exposure: create coadd")
            dimensions = exposure.getMaskedImage().getDimensions()
            wcs = exposure.getWcs()
            coaddPolicy = self.policy.get("coaddPolicy")
            self.coadd = coaddChiSq.Coadd(dimensions, wcs, coaddPolicy)

        self.log.log(Log.INFO, "Add exposure to coadd")
        self.coadd.addExposure(exposure)

        event = self.getFromClipboard(clipboard, "event")
#         print "event names"
#         for name in event.names():
#             print "*", name

        if event.get("isLastExposure"):
            self.log.log(Log.INFO, "Last exposure: write coadd to clipboard and reset to initial state")
            coaddExposure = self.coadd.getCoadd()
            weightMap = self.coadd.getWeightMap()
            self.addToClipboard(clipboard, "coadd", coaddExposure)
            self.addToClipboard(clipboard, "weightMap", weightMap)
            self.coadd = None
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class ChiSquaredStage(baseStage.Stage):
    parallelClass = ChiSquaredStageParallel

