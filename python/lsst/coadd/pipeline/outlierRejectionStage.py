from lsst.pex.logging import Log
import lsst.afw.image as afwImage
import baseStage

class OutlierRejectionStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to combine a list of exposures computing an outlier-rejected mean.
    
    @todo: skeleton only!
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "outlierRejectionStage_dict.paf"
    def process(self, clipboard):
        """Reject outliers"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        exposureList = self.getFromClipboard(clipboard, "exposureList")
        outlierRejectionPolicy = self.policy.get("outlierRejectionPolicy")

        # skeleton!; should call an outlier rejection function in coadd_utils
        coadd = exposureList[0]
        weightMap = afwImage.ImageF(coadd.getMaskedImage().getDimensions(), 1.0)

        self.addToClipboard(clipboard, "coadd", coadd)
        self.addToClipboard(clipboard, "weightMap", weightMap)

# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class OutlierRejectionStage(baseStage.Stage):
    parallelClass = OutlierRejectionStageParallel
