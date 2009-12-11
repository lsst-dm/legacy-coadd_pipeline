import lsst.coadd.psfmatched as psfMatched
import lsst.afw.math as afwMath
import baseStage

class PsfMatchStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to psf-match one exposure to another.
    
    The input exposures must have the same WCS to get reasonable results. This is NOT checked.
    
    @todo: modify to psf-match one exposure to a psf model instead of another exposure.
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
        
        warpedExposure, psfMatchedExposure, psfMatchingKernel, psfMatchingKernelSum, backgroundModel = \
            psfMatched.warpAndPsfMatchExposure(
                referenceExposure, exposure, self.warpingKernel, self.psfMatchPolicy)

        self.addToClipboard(clipboard, "warpedExposure", psfMatchedExposure)
        self.addToClipboard(clipboard, "psfMatchedExposure", psfMatchedExposure)
        self.addToClipboard(clipboard, "psfMatchingKernel", psfMatchingKernel)
        self.addToClipboard(clipboard, "psfMatchingKernelSum", psfMatchingKernelSum)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class PsfMatchStage(baseStage.Stage):
    parallelClass = PsfMatchStageParallel
