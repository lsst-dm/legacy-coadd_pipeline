import lsst.coadd.utils as coaddUtils
import lsst.coadd.psfmatched as psfMatched
import baseStage

class PsfMatchStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to psf-match one exposure to another.
    
    The input exposures must have the same WCS to get reasonable results. This is NOT checked.
    
    @todo: modify to psf-match one exposure to a psf model instead of another exposure.
    
    @todo: should the psf-matching kernel be output instead of the kernel sum? I think so!
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "psfMatchStage_dict.paf"
    
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
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
class PsfMatchStage(baseStage.Stage):
    parallelClass = PsfMatchStageParallel
