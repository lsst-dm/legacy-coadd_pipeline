#!/usr/bin/env python

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

from __future__ import with_statement

import os
import sys
import time

import eups
import lsst.daf.base as dafBase
import lsst.pex.harness as pexHarness
import lsst.pex.logging as pexLog
import lsst.pex.policy as pexPolicy
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.coadd.pipeline as coaddPipe
from lsst.pex.harness import Clipboard, simpleStageTester

SaveDebugImages = False
Verbosity = 1

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

def makeCoadd(exposurePathList, warpExposurePolicy, psfMatchPolicy, coaddGenPolicy):
    """Make a coadd using psf-matching and coaddGenerationStage
    
    Inputs:
    - exposurePathList: a list of paths to calibrated science exposures
    - warpExposurePolicy: policy to control warping
    - psfMatchPolicy: policy to control psf-matching
    """
    if len(exposurePathList) == 0:
        print "No images specified; nothing to do"
        return

    # until PR 1069 is fixed one cannot actually use SimpleStageTester to process multiple files
    # meanwhile just call the process method directly
        
    # set up pipeline stages
    # note: CoaddGenerationStage cannot be run with SimpleStageTester until PR 1069 is fixed.
    warpExposureStage = coaddPipe.WarpExposureStage(warpExposurePolicy)
    warpExposureTester = pexHarness.simpleStageTester.SimpleStageTester(warpExposureStage)
    warpExposureTester.setDebugVerbosity(Verbosity)
    psfMatchStage = coaddPipe.PsfMatchStage(psfMatchPolicy)
    psfMatchTester = pexHarness.simpleStageTester.SimpleStageTester(psfMatchStage)
    psfMatchTester.setDebugVerbosity(Verbosity)
#     stage = coaddPipe.CoaddGenerationStage(coaddGenPolicy)
#     tester = pexHarness.simpleStageTester.SimpleStageTester(stage)
#     tester.setDebugVerbosity(Verbosity)
    tempLog = pexLog.Log()
    coaddGenerationStage = coaddPipe.CoaddGenerationStageParallel(coaddGenPolicy, tempLog)
    
    # process exposures
    referenceExposure = None
    lastInd = len(exposurePathList) - 1
    for expInd, exposurePath in enumerate(exposurePathList):
        isFirst = (expInd == 0)
        isLast = (expInd == lastInd)

        print "Processing exposure %d of %d: %s" % (expInd+1, lastInd+1, exposurePath)
        exposure = afwImage.ExposureF(exposurePath)

        print "Subtract background"
        subtractBackground(exposure.getMaskedImage())

        clipboard = pexHarness.Clipboard.Clipboard()
        event = dafBase.PropertySet()
        event.add("isLastExposure", isLast)
        clipboard.put(coaddGenPolicy.get("inputKeys.event"), event)

        # psf-match, if necessary
        if not referenceExposure:
            print "First exposure; simply add to coadd"
            referenceExposure = exposure
            clipboard.put(coaddGenPolicy.get("inputKeys.psfMatchedExposure"), exposure)
        else:
            clipboard.put(warpExposurePolicy.get("inputKeys.exposure"), exposure)
            clipboard.put(warpExposurePolicy.get("inputKeys.referenceExposure"), referenceExposure)
            warpExposureTester.runWorker(clipboard)
            psfMatchTester.runWorker(clipboard)
            
            if SaveDebugImages:
                exposureName = os.path.basename(exposurePath)
                warpedExposure = clipboard.get(warpExposurePolicy.get("outputKeys.warpedExposure"))
                warpedExposure.writeFits("warped_%s" % (exposureName,))
                psfMatchedExposure = clipboard.get(psfMatchPolicy.get("outputKeys.psfMatchedExposure"))
                psfMatchedExposure.writeFits("psfMatched_%s" % (exposureName,))

#        tester.runWorker(clipboard)
        coaddGenerationStage.process(clipboard)
    
        if isLast:
            # one could put this code after the loop, but then it is less robust against
            # code changes (e.g. making multiple coadds), early exit, etc.
            coadd = clipboard.get(coaddGenPolicy.get("outputKeys.coadd"))
            weightMap = clipboard.get(coaddGenPolicy.get("outputKeys.weightMap"))
            return (coadd, weightMap)

    raise RuntimeError("Unexpected error; last exposure never run")

if __name__ == "__main__":
    pexLog.Trace.setVerbosity('lsst.coadd', Verbosity)
    helpStr = """Usage: makeCoadd.py coaddPath exposureList  [psfMatchPolicyPath [coaddGenerationPolicyPath]]

where:
- coaddPath is the desired name or path of the output coadd
- exposureList is a file containing a list of:
    pathToExposure
  where:
  - pathToExposure is the path to an Exposure (without the final _img.fits)
  - the first exposure listed is the reference exposure:
        its size and WCS are used for the coadd exposure
  - empty lines and lines that start with # are ignored.
- psfMatchPolicyPath is the path to a policy file; overrides for policy/psfMatchStage_dict.paf
- coaddGenerationPolicyPath is the path to a policy file; overrides for policy/coaddGenerationStage.paf
"""
    if len(sys.argv) not in (3, 4):
        print helpStr
        sys.exit(0)
    
    outName = sys.argv[1]
    if os.path.exists(outName + "_img.fits"):
        print "Coadd file %s already exists" % (outName,)
        sys.exit(1)
    weightOutName = outName + "_weight.fits"
    
    exposureList = sys.argv[2]

    if len(sys.argv) > 3:
        policyPath = sys.argv[3]
        psfMatchPolicy = pexPolicy.Policy(policyPath)
    else:
        psfMatchPolicy = pexPolicy.Policy()
    # There doesn't seem to be a better way to get at the policy dict; it should come from the stage. Sigh.
    warpExposurePolFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "warpExposureStage_dict.paf",
        "policy")
    warpExposurePolicy = pexPolicy.Policy.createPolicy(warpExposurePolFile,
        warpExposurePolFile.getRepositoryPath())

    psfMatchPolFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "psfMatchStage_dict.paf", "policy")
    defPsfMatchPolicy = pexPolicy.Policy.createPolicy(psfMatchPolFile, psfMatchPolFile.getRepositoryPath())
    psfMatchPolicy.mergeDefaults(defPsfMatchPolicy)

    if len(sys.argv) > 4:
        policyPath = sys.argv[4]
        coaddGenPolicy = pexPolicy.Policy(coaddGenerationPolicyPath)
    else:
        coaddGenPolicy = pexPolicy.Policy()
    coaddGenPolFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "coaddGenerationStage_dict.paf", "policy")
    defCoaddGenPolicy = pexPolicy.Policy.createPolicy(coaddGenPolFile, coaddGenPolFile.getRepositoryPath())
    coaddGenPolicy.mergeDefaults(defCoaddGenPolicy)
    
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

    if len(exposurePathList) == 0:
        print "No exposures; nothing to do"
        sys.exit(0)

    startTime = time.time()

    coadd, weightMap = makeCoadd(exposurePathList, warpExposurePolicy, psfMatchPolicy, coaddGenPolicy)
    coadd.writeFits(outName)
    weightMap.writeFits(weightOutName)

    deltaTime = time.time() - startTime
    print "Processed %d exposures in %0.1f seconds; %0.1f seconds/exposure" % \
        (len(exposurePathList), deltaTime, deltaTime/float(len(exposurePathList)))
