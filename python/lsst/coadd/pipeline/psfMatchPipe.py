import lsst.pex.logging as pexLog
import lsst.pex.policy as pexPolicy
import lsst.pex.harness.stage as harnessStage
import lsst.pex.harness as pexHarness
import lsst.pex.harness.IOStage
import lsst.ip.diffim.diffimTools as diffimTools

class SelectImages(harnessStage.ParallelProcessing):
    """
    a parallel stage implementation that provides to a PSFMatch pipeline
    the names of the exposures to operate on.  
    """
    def setup(self):
        policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", 
                                                 "selectImages_dict.paf",
                                                 "policy")
        defPolicy = pexPolicy.Policy.createPolicy(policyFile,
                                                  policyFile.getRepositoryPath(),
                                                  True)
        if self.policy is None:
            self.policy = pexPolicy.Policy()
        self.policy.mergeDefaults(defPolicy.getDictionary())

        self.nextExposureIdx = 0;
        self.referenceExpName = self.policy.get("referenceExpName")
        self.exposureList = self.policy.getArray("exposureName")
        self.exposureDir = self.policy.get("exposureDir")
        self.matchedExpDir = self.policy.get("matchedExpDir")

    
    def process(self, clipboard):
        """
        place the name of the next exposure to operate on onto the 
        clipboard
        """
        clipboard.put("exposureDir", self.exposureDir)
        clipboard.put("referenceExpName", self.referenceExpName)
        clipboard.put("exposureName",self.exposureList[self.nextExposureIdx])

        # output name
        outname = self.exposureList[self.nextExposureIdx]
        if outname.endswith(".sci"):
            outname = outname[:-3] + "matched"
        clipboard.put("matchedExpName", outname)
        self.nextExposureIdx += 1

class SelectImagesStage(harnessStage.Stage):
    parallelClass = SelectImages


        
class InputRefExp(pexHarness.IOStage.InputStageParallel):
    """
    a parallel stage implementation that loads in a reference exposure for 
    a psfMatch pipeline.  This implementation allows the same reference 
    exposure to be used by multiple iterations of the stage.  It does this 
    by not only posting the exposure to the clipboard, but also keeping a
    reference as an attribute of this class call referenceExposure.  The 
    process function will check to see if this attribute is None; if 
    it is, the image will be loaded from disk; otherwise the exposure will 
    post to the clipboard.  
    """

    def setup(self):
        self.referenceExposure = None
        try:
            self.refExposureKey = self.policy.get("InputItems").names()[0]
        except IndexError:
            raise RuntimeError("Empty 'InputItems' parameter in policy")
    
    def process(self, clipboard):
        if self.referenceExposure is None:
            pexHarness.IOStage.InputStageParallel.process(self, clipboard)
            self.referenceExposure = clipboard.get(self.refExposureKey)
        else:
            clipboard.put(self.refExposureKey, self.referenceExposure)

class InputRefExpStage(harnessStage.Stage):
    parallelClass = InputRefExp


class SelfBkgdSubtract(harnessStage.ParallelProcessing):
    """
    a ParallelProcessing stage component that will estimate the background in 
    an Exposure and then subtract it.  
    """
    def setup(self):
        policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", 
                                                 "selfBkgdSubtract_dict.paf",
                                                 "policy")
        defPolicy = pexPolicy.Policy.createPolicy(policyFile,
                                                  policyFile.getRepositoryPath(),
                                                  True)
        if self.policy is None:
            self.policy = pexPolicy.Policy()
        self.policy.mergeDefaults(defPolicy.getDictionary())

        self.expkey = self.policy.get("inputKeys.exposure")

    def process(self, clipboard):
        diffimTools.backgroundSubtract(self.policy,
                               [clipboard.get(self.expkey).getMaskedImage()])

class SelfBkgdSubtractStage(harnessStage.Stage):
    parallelClass = SelfBkgdSubtract

class RefSelfBkgdSubtract(SelfBkgdSubtract):
    def setup(self):
        self.bgsubtracted = False

    def process(self, clipboard):
        if not self.bgsubtracted:
            SelfBkgdSubtract.process(self, clipboard)
            self.bgsubtracted = True

class RefSelfBkgdSubtractStage(harnessStage.Stage):
    parallelClass = SelfBkgdSubtract


