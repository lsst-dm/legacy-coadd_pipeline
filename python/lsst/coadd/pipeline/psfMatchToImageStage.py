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

import lsst.coadd.psfmatched as coaddPsfMatch
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import baseStage

class PsfMatchStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to psf-match one exposure to another.
    
    The input exposures must have the same WCS to get reasonable results. This is NOT checked.
    
    @todo: modify to psf-match one exposure to a psf model instead of another exposure.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "PsfMatchToImageStageDictionary.paf"
    
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        psfMatchToImagePolicy = self.policy.getPolicy("psfMatchToImagePolicy")
        self.matcher = coaddPsfMatch.PsfMatchToImage(psfMatchToImagePolicy)

    def process(self, clipboard):
        """Psf-match exposure to referenceExposure"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        warpedExposure = self.getFromClipboard(clipboard, "warpedExposure")
        referenceExposure = self.getFromClipboard(clipboard, "referenceExposure")
        
        psfMatchedExposure, psfMatchingKernel, psfMatchingKernelSum = self.matcher.matchExposure(
            warpedExposure, referenceExposure.getMaskedImage())

        self.addToClipboard(clipboard, "psfMatchedExposure", psfMatchedExposure)
        self.addToClipboard(clipboard, "psfMatchingKernel", psfMatchingKernel)
        self.addToClipboard(clipboard, "psfMatchingKernelSum", psfMatchingKernelSum)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class PsfMatchStage(baseStage.Stage):
    parallelClass = PsfMatchStageParallel
