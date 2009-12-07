from lsst.pex.logging import Log
import lsst.pex.policy as pexPolicy
import lsst.pex.harness.stage as harnessStage
import lsst.coadd.chisquared as coaddChiSq

class ChiSquareStageParallel(harnessStage.ParallelProcessing):
    """
    Description:
        Pipeline stage to create a chi-squared coadd
        
    @todo get the following clipboard items from an event, rather than directly from the clipboard:
    isLastExposure, width, height and WCS

    Policy Dictionary:
    lsst/coadd/pipeline/policy/ChiSquareStageDictionary.paf
    """
    def setup(self):
#         print "***** setup"
        self.log = Log(self.log, "ChiSquareStage")

        policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "ChiSquareStageDictionary.paf", "policy")
        defPolicy = pexPolicy.Policy.createPolicy(policyFile, "policy", True)
        if self.policy is None:
            self.policy = pexPolicy.Policy()
        self.policy.mergeDefaults(defPolicy)
        
        self.coadd = None

    def process(self, clipboard):
        """Add exposure to chiSquared coadd"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key
#         print "self.coadd=", self.coadd, "at start of process"

        exposure = self.getFromClipboard(clipboard, "exposure")
        
        if not self.coadd:
            self.log.log(Log.INFO, "First exposure: create coadd")
            dimensions = exposure.getMaskedImage().getDimensions()
            wcs = exposure.getWcs()
            coaddPolicy = self.policy.get("coaddPolicy")
            self.coadd = coaddChiSq.Coadd(dimensions, wcs, coaddPolicy)

        self.log.log(Log.INFO, "Add exposure to coadd")
        self.coadd.addExposure(exposure)

        event = self.getFromClipboard(clipboard, "event")
#         print "event names"
#         for name in event.names():
#             print "*", name

        if event.get("isLastExposure"):
            self.log.log(Log.INFO, "Last exposure: write coadd to clipboard and reset to initial state")
            coaddExposure = self.coadd.getCoadd()
            weightMap = self.coadd.getWeightMap()
            self.addToClipboard(clipboard, "coadd", coaddExposure)
            self.addToClipboard(clipboard, "weightMap", weightMap)
            self.coadd = None
    
    def getFromClipboard(self, clipboard, key):
        """Retrieve an item from the clipboard.
        
        I hope to replace this with improvements in the middleware.
        
        Inputs:
        - clipbaord: the clipboard
        - key: the name of the item; the name of the item on the clipboard is given by:
            self.policy.get("inputKeys." + key)
        
        @return the item read from the clipboard
        @raise KeyError or ? if full key is not found in policy or item is not found on clipboard.
        """
        policyKey = "inputKeys.%s" % (key,)
        clipboardKey = self.policy.getString(policyKey)
        if clipboardKey == None:
            raise KeyError("Could not find %s in policy" % (policyKey,))
        clipboardItem = clipboard.get(clipboardKey)
        if clipboardItem == None:
            raise KeyError("Could not find %s=%s on clipboard" % (policyKey, clipboardKey))
        return clipboardItem
    
    def addToClipboard(self, clipboard, key, item):
        """Put an item on the clipboard.
        
        I hope to replace this with improvements in the middleware.
        
        Outputs:
        - clipbaord: the clipboard
        - key: the name of the item; the name of the item on the clipboard is given by:
            self.policy.get("outputKeys." + key)
        - item: the item to add to the clipboard

        @raise KeyError or ? if full key is not found in self.policy.
        """
        policyKey = "outputKeys.%s" % (key,)
        clipboardKey = self.policy.getString(policyKey)
        if clipboardKey == None:
            raise KeyError("Could not find %s in policy" % (policyKey,))
        clipboard.put(clipboardKey, item)
        
# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class ChiSquareStage(harnessStage.Stage):
    parallelClass = ChiSquareStageParallel

