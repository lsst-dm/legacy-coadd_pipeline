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
import lsst.coadd.utils as coaddUtils
import baseStage

class CoaddGenerationStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to add warped and psf-matched exposures to a coadd.
    
    @todo: modify to use HEALPix.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "CoaddGenerationStageDictionary.paf"
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        self.coadd = None
    
    def process(self, clipboard):
        """Add exposure to coadd"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        psfMatchedExposure = self.getFromClipboard(clipboard, "psfMatchedExposure")
        if not self.coadd:
            self.log.log(Log.INFO, "First exposure: create coadd")
            coaddDimensions = psfMatchedExposure.getMaskedImage().getDimensions()
            coaddWcs = psfMatchedExposure.getWcs()
            allowedMaskPlanes = self.policy.getPolicy("coaddPolicy").get("allowedMaskPlanes")
            self.coadd = coaddUtils.Coadd(coaddDimensions, coaddWcs, allowedMaskPlanes)

        weight = self.coadd.addExposure(psfMatchedExposure)
        self.addToClipboard(clipboard, "coaddedWeight", weight)
        self.log.log(Log.INFO, "Added exposure to coadd; weight=%0.2f" % (weight,))

        event = self.getFromClipboard(clipboard, "event")
        if event.get("isLastExposure"):
            self.log.log(Log.INFO, "Last exposure: write coadd to clipboard and reset to initial state")
            coaddExposure = self.coadd.getCoadd()
            weightMap = self.coadd.getWeightMap()
            self.addToClipboard(clipboard, "coadd", coaddExposure)
            self.addToClipboard(clipboard, "weightMap", weightMap)
            self.coadd = None

# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class CoaddGenerationStage(baseStage.Stage):
    parallelClass = CoaddGenerationStageParallel
