from lsst.pex.logging import Log
import lsst.coadd.utils as coaddUtils
import baseStage

class TemplateGenerationStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to combine a list of exposures computing an outlier-rejected mean.
    
    @todo: skeleton only!
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "templateGenerationStage_dict.paf"
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

        self.addToClipboard(clipboard, "coadd", coadd[0])

# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class TemplateGenerationStage(baseStage.Stage):
    parallelClass = TemplateGenerationStageParallel
