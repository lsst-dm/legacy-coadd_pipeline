#!/usr/bin/env python
"""
Tests for components of the PSFMatch pipeline
"""

import os
import sys
import unittest

from lsst.coadd.pipeline import psfMatchPipe, WarpExposureStage, PsfMatchStage
from lsst.pex.policy import Policy, DefaultPolicyFile
from lsst.pex.harness.simpleStageTester import SimpleStageTester
from lsst.pex.harness import IOStage
import lsst.pex.harness.stage as phstage
import lsst.afw.image

datadir = None

class InputStage(phstage.Stage):
    parallelClass = IOStage.InputStageParallel

class PipeTestCase(unittest.TestCase):

    def setUp(self):
        selectPolicyFile = "testSelectImages.paf"
        self.selectPolFile = DefaultPolicyFile("coadd_pipeline", 
                                               selectPolicyFile,
                                               "examples/psfMatchPipe")

    def tearDown(self):
        pass

    def testSelectImages(self):
        selectPolicy = Policy.createPolicy(self.selectPolFile)

        tester = self._makeSelectTester(selectPolicy)
        clipboard = {}
        out = tester.runWorker(clipboard)

        rexp = selectPolicy.get("referenceExpName")
        exp1 = selectPolicy.getArray("exposureName")[0]
        expd = selectPolicy.get("exposureDir")

        keys = out.keys()
        self.assert_("referenceExpName" in keys,
                     "referenceExpName not set on clipboard")
        self.assertEquals(out["referenceExpName"], rexp)
        self.assert_("exposureName" in keys,
                     "exposureName not set on clipboard")
        self.assertEquals(out["exposureName"], exp1)
        self.assert_("exposureDir" in keys,
                     "exposureDir not set on clipboard")
        self.assertEquals(out["exposureDir"], expd)

    def _makeSelectTester(self, selectpol):
        if not selectpol.exists("exposureDir"):
            global datadir
            if not datadir:
                try:
                    datadir=os.path.join(os.environ['COADD_PIPELINE_DATA_DIR'],
                                         "PSFMatch")
                except KeyError:
                    print >> sys.stderr, \
                          "Product COADD_PIPELINE_DATA_DIR not setup;",\
                          "provide data directory as argument."
                    raise RuntimeError, "No exposure dir specified"
            selectpol.set("exposureDir", datadir)
    
        tester = SimpleStageTester( psfMatchPipe.SelectImagesStage(selectpol) )
        tester.setDebugVerbosity(5)
        return tester

    def _makeRefLoadTester(self, selectpol):
        inppol = DefaultPolicyFile("coadd_pipeline", 
                                   "refImageInput.paf",
                                   "examples/psfMatchPipe")
        inppol = Policy.createPolicy(inppol)
        
        tester = self._makeSelectTester(selectpol)
        tester.addStage( psfMatchPipe.InputRefExpStage(inppol) )
        return tester

    def _makeExpLoadTester(self, selectpol):
        inppol = DefaultPolicyFile("coadd_pipeline", 
                                   "expImageInput.paf",
                                   "examples/psfMatchPipe")
        inppol = Policy.createPolicy(inppol)
        
        tester = self._makeRefLoadTester(selectpol)
# bug in pex_harness causes this to fail:
#        tester.addStage(phstage.makeStage(inppol,
#                    paraClsName="lsst.pex.harness.IOStage.InputStageParallel"))
        tester.addStage( InputStage(inppol) )

        return tester

    def _makePsfMatchTester(self, selectpol):
        tester = self._makeExpLoadTester(selectpol)
        tester.addStage( WarpExposureStage(None) )
        tester.addStage( PsfMatchStage(None) )
        return tester

    def testRefLoad(self):
        selectPolicy = Policy.createPolicy(self.selectPolFile)
        tester = self._makeRefLoadTester(selectPolicy)
        clipboard = {}
        out = tester.runWorker(clipboard)

        self.assert_(out.has_key("referenceExposure"),
                     "referenceExposure not set on clipboard")
        self.assert_(isinstance(out["referenceExposure"],
                                lsst.afw.image.ExposureF),
                     "referenceExposure is not an Exposure")

    def testExpLoad(self):
        selectPolicy = Policy.createPolicy(self.selectPolFile)
        tester = self._makeExpLoadTester(selectPolicy)
        clipboard = {}
        out = tester.runWorker(clipboard)

        self.assert_(out.has_key("exposure"),
                     "exposure not set on clipboard")
        self.assert_(isinstance(out["exposure"],
                                lsst.afw.image.ExposureF),
                     "exposure is not an Exposure")
        self.assert_(isinstance(out["referenceExposure"],
                                lsst.afw.image.ExposureF),
                     "referenceExposure is not an Exposure")

    def testPsfMatch(self):
        """
        run one iteration of the PSFMatch pipeline
        """
        selectPolicy = Policy.createPolicy(self.selectPolFile)
        tester = self._makePsfMatchTester(selectPolicy)
        clipboard = {}
        out = tester.runWorker(clipboard)

        self.assert_(isinstance(out["exposure"],
                                lsst.afw.image.ExposureF),
                     "exposure is not an Exposure")
        self.assert_(isinstance(out["referenceExposure"],
                                lsst.afw.image.ExposureF),
                     "referenceExposure is not an Exposure")

        print "Clipboard keys:", out.keys()

def testPsfMatch():
    suite=unittest.TestLoader().loadTestsFromName(globals()['__name__'] +
                                                  ".PipeTestCase.testPsfMatch")
    unittest.TextTestRunner(verbosity=2).run(suite)

def testSelect():
    suite=unittest.TestLoader().loadTestsFromName(globals()['__name__'] +
                                              ".PipeTestCase.testSelectImages")
    unittest.TextTestRunner(verbosity=2).run(suite)

def dbmain():
    suite = unittest.TestLoader().loadTestsFromTestCase(PipeTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        datadir = sys.argv[1]
#    unittest.main()
#    dbmain()
    testPsfMatch()
#    testSelect()


    

