import lsst.coadd.utils as coaddUtils
import lsst.coadd.psfmatched as psfMatched
import BaseStage

class PsfMatchStageParallel(BaseStage.ParallelStage):
    """
    Pipeline stage to psf-match one exposure to another.
    
    The input exposures must have the same WCS to get reasonable results. This is NOT checked.
    
    @todo: modify to psf-match one exposure to a psf model instead of another exposure.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "PsfMatchStage_dict.paf"
    
    def setup(self):
        BaseStage.ParallelStage.setup(self)
        
        self.warpingKernel = afwMath.makeWarpingKernel(self.policy.get("warpingKernelName"))
        self.psfMatchPolicy = self.policy.get("psfMatchPolicy")

    def process(self, clipboard):
        """Psf-match exposure to referenceExposure"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        exposure = self.getFromClipboard(clipboard, "exposure")
        referenceExposure = self.getFromClipboard(clipboard, "referenceExposure")
        
        warpedExposure, psfMatchedExposure, kernelSum, backgroundModel = psfMatched.warpAndPsfMatchExposure(
            referenceExposure, exposure, self._warpingKernel, self.psfMatchPolicy)

        self.addToClipboard(clipboard, "warpedExposure", psfMatchedExposure)
        self.addToClipboard(clipboard, "psfMatchedExposure", psfMatchedExposure)
        self.addToClipboard(clipboard, "kernelSum", kernelSum)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class PsfMatchStage(BaseStage.Stage):
    parallelClass = PsfMatchStageParallel
