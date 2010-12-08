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

import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.coadd.utils as coaddUtils
import baseStage

class WarpExposureStageParallel(baseStage.ParallelStage):
    """Pipeline stage to warp one exposure to match a reference exposure.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "WarpExposureStageDictionary.paf"
    
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        warpPolicy = self.policy.getPolicy("warpPolicy")
        self.warper = coaddUtils.Warp.fromPolicy(warpPolicy)

    def process(self, clipboard):
        """Warp exposure to referenceExposure"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        exposure = self.getFromClipboard(clipboard, "exposure")
        referenceExposure = self.getFromClipboard(clipboard, "referenceExposure")
        warpedExposure = self.warper.warpExposure(
            bbox = coaddUtils.bboxFromImage(referenceExposure),
            wcs = referenceExposure.getWcs(),
            exposure = exposure)

        self.addToClipboard(clipboard, "warpedExposure", warpedExposure)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class WarpExposureStage(baseStage.Stage):
    parallelClass = WarpExposureStageParallel
