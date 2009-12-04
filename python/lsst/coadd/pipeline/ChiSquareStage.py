from lsst.pex.logging import Log
import lsst.pex.policy as pexPolicy
import lsst.pex.harness.stage as harnessStage
import lsst.coadd.chisquared as coaddChiSq

class ChiSquareStageParallel(harnessStage.ParallelProcessing):
    """
    Description:
        Pipeline stage to create a chi-squared coadd     

    Policy Dictionary:
    lsst/coadd/pipeline/policy/ChiSquareStageDictionary.paf

    Clipboard Input:
    - policy.inputKeys.coaddDimensions: desired dimensions of coadd (std::pair<int, int>)
    - policy.inputKeys.coaddWcs: desired WCS of coadd (afwImage.Wcs)
    - policy.inputKeys.exposure: calibrated science exposure with the background subtracted
    - policy.inputKeys.isLastExposure: a boolean that is True if this is the last exposure
    
    Clipboard Output (but ONLY if this is the last exposure!):
    - policy.outputKeys.coadd: the chi-squared coadd (afwImage.Exposure)
    - policy.outputKeys.weightMap: the weight map for the chi-squared coadd (afwImage.Image)
    """
    def setup(self):
        self.log = Log(self.log, "ChiSquareStage")

        policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "ChiSquareStageDictionary.paf", "policy")
        defPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath(), True)

        if self.policy is None:
            self.policy = pexPolicy.Policy()
        self.policy.mergeDefaults(defPolicy)
        
        self.coadd = None

    def process(self, clipboard):
        """Add exposure to chiSquared coadd"""
        if not self.coadd:
            self.log.log(Log.INFO, "First exposure: create coadd")
            dimensions = clipboard.get(self.policy.getString("inputKeys.coaddDimensions"))
            wcs = clipboard.get(self.policy.getString("inputKeys.wcsKey"))

            coaddPolicyFile = pexPolicy.DefaultPolicyFile(
                "coadd_chisquared", "ChiSquaredCoaddDictionary.paf", "policy")
            coaddDefPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath(), True)
            coaddPolicy = self.policy.get("coaddPolicy") or pexPolicy.Policy()
            coaddPolicy.mergeDefaults(coaddDefPolicy)

            self.coadd = coaddChiSq.Coadd(dimensions, wcs, coaddPolicy)

        exposure = clipboard.get(self.policy.getString("inputKeys.exposure"))
        isLastExposure = clipboard.get(self.policy.getString("inputKeys.isLastExposure"))
            
        self.log.log(Log.INFO, "Add exposure to coadd")
        self.coadd.addExposure(exposure)

        if isLastExposure:
            self.log.log(Log.INFO, "Last exposure: write coadd to clipboard and reset to initial state")
            coaddExposure = self.coadd.getCoadd()
            weightMap = self.coadd.getWeightMap()
            clipboard.put(self.policy.get("outputKeys.coadd"), coaddExposure)
            clipboard.put(self.policy.get("outputKeys.weightMap"), weightMap)
            self.coadd = None
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class ChiSquareStage(harnessStage.Stage):
    parallelClass = ChiSquareStageParallel

