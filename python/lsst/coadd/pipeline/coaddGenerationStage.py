from lsst.pex.logging import Log
import lsst.coadd.utils as coaddUtils
import lsst.coadd.psfmatched as coaddPsf
import baseStage

class CoaddGenerationStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to add warped and psf-matched exposures to a coadd.
    
    @todo: modify to use HEALPix.
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "coaddGenerationStage_dict.paf"
    def setup(self):
        baseStage.ParallelStage.setup(self)
        
        self.coadd = None
    
    def process(self, clipboard):
        """Add exposure to coadd"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        # simplify this code once coadd_psfmatched supports creating coadds
        # without psf-matching each input image;
        # meanwhile do not bother with proper weighting.
        psfMatchedExposure = self.getFromClipboard(clipboard, "psfMatchedExposure")
        if not self.coadd:
            self.log.log(Log.INFO, "First exposure: create coadd")
            allowedMaskPlanes = self.policy.get("allowedMaskPlanes")
            self.coadd = coaddPsf.BasicCoadd(psfMatchedExposure, allowedMaskPlanes)
        else:
            weight = self.coadd.addExposure(psfMatchedExposure)
            self.log.log(Log.INFO, "Added exposure to coadd; weight=%0.2f" % (weight,))

        event = self.getFromClipboard(clipboard, "event")
        if event.get("isLastExposure"):
            self.log.log(Log.INFO, "Last exposure: write coadd to clipboard and reset to initial state")
            coaddExposure = self.coadd.getCoadd()
            weightMap = self.coadd.getWeightMap()
            self.addToClipboard(clipboard, "coadd", coaddExposure)
            self.addToClipboard(clipboard, "weightMap", weightMap)
            self.addToClipboard(clipboard, "weight", weight)
            self.coadd = None

# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class CoaddGenerationStage(baseStage.Stage):
    parallelClass = CoaddGenerationStageParallel
