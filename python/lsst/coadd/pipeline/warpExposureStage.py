import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.coadd.utils as coaddUtils
import baseStage

class WarpExposureStageParallel(baseStage.ParallelStage):
    """Pipeline stage to warp one exposure to match a reference exposure.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "warpExposureStage_dict.paf"
    
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        self.warpingKernel = afwMath.makeWarpingKernel(self.policy.get("warpingKernelName"))

    def process(self, clipboard):
        """Warp exposure to referenceExposure"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        exposure = self.getFromClipboard(clipboard, "exposure")
        referenceExposure = self.getFromClipboard(clipboard, "referenceExposure")

        warpedExposure = coaddUtils.makeBlankExposure(referenceExposure)
        afwMath.warpExposure(warpedExposure, exposure, self.warpingKernel)

        self.addToClipboard(clipboard, "warpedExposure", warpedExposure)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class WarpExposureStage(baseStage.Stage):
    parallelClass = WarpExposureStageParallel
