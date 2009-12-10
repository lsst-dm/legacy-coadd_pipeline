#!/usr/bin/env python
from __future__ import with_statement

import sys, os, math

import pdb
import unittest

import eups
import lsst.daf.base as dafBase
import lsst.pex.harness as pexHarness
import lsst.pex.logging as pexLog
import lsst.pex.policy as pexPolicy
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.coadd.pipeline as coaddPipe
from lsst.pex.harness import Clipboard, simpleStageTester

Verbosity = 5

BackgroundCells = 256

def subtractBackground(maskedImage):
    """Subtract the background from a MaskedImage
    
    Note: at present the mask and variance are ignored, but they might used be someday.
    
    Returns the background object returned by afwMath.makeBackground.
    """
    bkgControl = afwMath.BackgroundControl(afwMath.Interpolate.NATURAL_SPLINE)
    bkgControl.setNxSample(int(maskedImage.getWidth() // BackgroundCells) + 1)
    bkgControl.setNySample(int(maskedImage.getHeight() // BackgroundCells) + 1)
    bkgControl.sctrl.setNumSigmaClip(3)
    bkgControl.sctrl.setNumIter(3)

    image = maskedImage.getImage()
    bkgObj = afwMath.makeBackground(image, bkgControl)
    image -= bkgObj.getImageF()
    return bkgObj

def psfMatchExposures(exposurePathList, policy):
    """Warp and psf-match a set of exposures to match a reference exposure
    
    Inputs:
    - exposurePathList: a list of paths to calibrated science exposures;
        the first one is taken to be the reference (and so is not processed).
    - policy: policy to control the coaddition stage
    """
    if len(exposurePathList) == 0:
        print "No images specified; nothing to do"
        return

    # set up pipeline
    stage = coaddPipe.PsfMatchStage(policy)
    tester = pexHarness.simpleStageTester.SimpleStageTester(stage)
    tester.setDebugVerbosity(Verbosity)

    # process exposures
    referenceExposurePath = exposurePathList[0]
    print "Reference exposure is: %s" % (referenceExposurePath,)
    referenceExposure = afwImage.ExposureF(referenceExposurePath)
    for exposurePath in exposurePathList[1:]:
        print "Processing exposure: %s" % (exposurePath,)
        exposure = afwImage.ExposureF(exposurePath)
        exposureName = os.path.basename(exposurePath)

        print "Subtract background"
        subtractBackground(exposure.getMaskedImage())

        # set up the clipboard
        clipboard = pexHarness.Clipboard.Clipboard()
        inPolicy = policy.get("inputKeys")
        clipboard.put(inPolicy.get("exposure"), exposure)
        clipboard.put(inPolicy.get("referenceExposure"), referenceExposure)

        # run the stage
        outClipboard = tester.runWorker(clipboard)
        
        outPolicy = policy.get("outputKeys")
        warpedExposure = outClipboard.get(outPolicy.get("warpedExposure"))
        psfMatchedExposure = outClipboard.get(outPolicy.get("psfMatchedExposure"))
        
        warpedExposure.writeFits("warped_%s" % (exposureName,))
        psfMatchedExposure.writeFits("psfMatched_%s" % (exposureName,))

if __name__ == "__main__":
    pexLog.Trace.setVerbosity('lsst.coadd', Verbosity)
    helpStr = """Usage: psfMatchExposure.py exposureList [policyPath]

where:
- exposureList is a file containing a list of:
    pathToExposure
  where:
  - pathToExposure is the path to an Exposure (without the final _img.fits)
  - the first exposure listed is the reference exposure:
        all other exposures are warped and PSF-matched to it.
        Thus the reference exposure should have the worst PSF of the set.
  - empty lines and lines that start with # are ignored.
- policyPath is the path to a policy file
"""
    if len(sys.argv) not in (2, 3):
        print helpStr
        sys.exit(0)
    
    exposureList = sys.argv[1]

    if len(sys.argv) > 2:
        policyPath = sys.argv[2]
        policy = pexPolicy.Policy(policyPath)
    else:
        policy = pexPolicy.Policy()

    policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "psfMatchStage_dict.paf", "policy")
    defPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath(), True)
    policy.mergeDefaults(defPolicy.getDictionary())
    
    exposurePathList = []
    ImageSuffix = "_img.fits"
    with file(exposureList, "rU") as infile:
        for lineNum, line in enumerate(infile):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            filePath = line
            fileName = os.path.basename(filePath)
            if not os.path.isfile(filePath + ImageSuffix):
                print "Skipping exposure %s; image file %s not found" % (fileName, filePath + ImageSuffix,)
                continue
            exposurePathList.append(filePath)

    psfMatchExposures(exposurePathList, policy)
