import lsst.pex.logging as pexLog
import lsst.pex.policy as pexPolicy
import lsst.pex.harness.stage as harnessStage

class ParallelStage(harnessStage.ParallelProcessing):
    """
    Base class for a pipeline parallel stage.
    
    The intent is to work around some limitations in the middleware, at least temporarily.
    
    Subclasses must set two variables:
    - packageName
    - policyDictionaryName

    The policy dictionary must be contained here:
    <packageName>/policy/policyDictionaryName
    """
    def setup(self):
        self.log = pexLog.Log(self.log, self.__class__.__name__)

        policyFile = pexPolicy.DefaultPolicyFile(self.packageName, self.policyDictionaryName, "policy")
        defPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath(), True)
        if self.policy is None:
            self.policy = pexPolicy.Policy()
        self.policy.mergeDefaults(defPolicy.getDictionary())
    
    def getFromClipboard(self, clipboard, key, doRaise=True):
        """Retrieve an item from the clipboard.
        
        Inputs:
        - clipbaord: the clipboard
        - key: the name of the item; the name of the item on the clipboard is given by:
            self.policy.get("inputKeys." + key)
        - doRaise: if True then raise KeyError if item is not found on clipboard
            else return None
        
        @return the item read from the clipboard
        @raise KeyError if doRaise True and item not found on clipboard
        @raise lsst.pex.exceptions.LsstCppException wrapping lsst::pex::policy::NameNotFound
            if full key is not found in policy; this indicates a bug: a mismatch with the stage dictionary.
        """
        policyKey = "inputKeys.%s" % (key,)
        clipboardKey = self.policy.getString(policyKey)
        clipboardItem = clipboard.get(clipboardKey)
        if clipboardItem == None and doRaise:
            raise KeyError("Could not find %s=%s on clipboard" % (policyKey, clipboardKey))
        return clipboardItem
    
    def addToClipboard(self, clipboard, key, item):
        """Put an item on the clipboard.
        
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

Stage = harnessStage.Stage # convenience
