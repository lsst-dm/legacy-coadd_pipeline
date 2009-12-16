import lsst.coadd.psfmatched as psfMatched
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
    policyDictionaryName = "psfMatchStage_dict.paf"
    
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        self.psfMatchPolicy = self.policy.get("psfMatchPolicy")

    def process(self, clipboard):
        """Psf-match exposure to referenceExposure"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        warpedExposure = self.getFromClipboard(clipboard, "warpedExposure")
        referenceExposure = self.getFromClipboard(clipboard, "referenceExposure")

        psfMatchedMaskedImage, psfMatchingKernel, psfMatchingKernelSum, backgroundModel = \
            psfMatched.psfMatchMaskedImage(referenceExposure.getMaskedImage(),
                warpedExposure.getMaskedImage(), self.psfMatchPolicy)
        psfMatchedExposure = afwImage.makeExposure(psfMatchedMaskedImage, referenceExposure.getWcs())

        self.addToClipboard(clipboard, "psfMatchedExposure", psfMatchedExposure)
        self.addToClipboard(clipboard, "psfMatchingKernel", psfMatchingKernel)
        self.addToClipboard(clipboard, "psfMatchingKernelSum", psfMatchingKernelSum)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class PsfMatchStage(baseStage.Stage):
    parallelClass = PsfMatchStageParallel
