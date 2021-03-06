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

"""Exercise outlierRejectionStage

To avoid filling up the disk or memory, it simply runs over small bit of a set of exposures
"""
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

SaveDebugImages = False
Verbosity = 1

BBox = afwImage.BBox(afwImage.PointI(0, 0), 100, 100)

BackgroundCellSize = 512

def subtractBackground(maskedImage):
    """Subtract the background from a MaskedImage
    
    Note: at present the mask and variance are ignored, but they might used be someday.
    
    Returns the background object returned by afwMath.makeBackground.
    """
    bkgControl = afwMath.BackgroundControl(afwMath.Interpolate.NATURAL_SPLINE)
    bkgControl.setNxSample(int(maskedImage.getWidth() // BackgroundCellSize) + 1)
    bkgControl.setNySample(int(maskedImage.getHeight() // BackgroundCellSize) + 1)
    bkgControl.getStatisticsControl().setNumSigmaClip(3)
    bkgControl.getStatisticsControl().setNumIter(3)

    image = maskedImage.getImage()
    bkgObj = afwMath.makeBackground(image, bkgControl)
    image -= bkgObj.getImageF()
    return bkgObj

def makeCoadd(exposurePathList, warpExposurePolicy, psfMatchPolicy, outlierRejectionPolicy):
    """Make a coadd using psf-matching and outlierRejectionStage
    
    Inputs:
    - exposurePathList: a list of paths to calibrated science exposures
    - psfMatchPolicy: policy to control psf-matching
    """
    if len(exposurePathList) == 0:
        print "No images specified; nothing to do"
        return

    # until PR 1069 is fixed one cannot actually use SimpleStageTester to process multiple files
    # meanwhile just call the process method directly
        
    # set up pipeline stages
    # note: OutlierRejectionStage cannot be run with SimpleStageTester until PR 1069 is fixed.
    warpExposureStage = coaddPipe.WarpExposureStage(warpExposurePolicy)
    warpExposureTester = pexHarness.simpleStageTester.SimpleStageTester(warpExposureStage)
    warpExposureTester.setDebugVerbosity(Verbosity)
    psfMatchStage = coaddPipe.PsfMatchStage(psfMatchPolicy)
    psfMatchTester = pexHarness.simpleStageTester.SimpleStageTester(psfMatchStage)
    psfMatchTester.setDebugVerbosity(Verbosity)
    outlierRejectionStage = coaddPipe.OutlierRejectionStage(outlierRejectionPolicy)
    outlierRejectionTester = pexHarness.simpleStageTester.SimpleStageTester(outlierRejectionStage)
    outlierRejectionTester.setDebugVerbosity(Verbosity)
    
    # process exposures
    referenceExposure = None
    lastInd = len(exposurePathList) - 1
    psfMatchedExposureList = []
    for expInd, exposurePath in enumerate(exposurePathList):
        isLast = (expInd == lastInd)

        print "Processing exposure %d of %d: %s" % (expInd+1, lastInd+1, exposurePath)
        exposure = afwImage.ExposureF(exposurePath)

        print "Subtract background"
        subtractBackground(exposure.getMaskedImage())

        clipboard = pexHarness.Clipboard.Clipboard()

        # psf-match, if necessary
        if not referenceExposure:
            print "First exposure; simply add to coadd"
            referenceExposure = exposure
            psfMatchedExposureList.append(afwImage.ExposureF(exposure, BBox))
        else:
            clipboard.put(warpExposurePolicy.get("inputKeys.exposure"), exposure)
            clipboard.put(warpExposurePolicy.get("inputKeys.referenceExposure"), referenceExposure)
            warpExposureTester.runWorker(clipboard)
            psfMatchTester.runWorker(clipboard)
            
            psfMatchedExposure = clipboard.get(psfMatchPolicy.get("outputKeys.psfMatchedExposure"))
            psfMatchedExposureList.append(afwImage.ExposureF(psfMatchedExposure, BBox))
            if SaveDebugImages:
                exposureName = os.path.basename(exposurePath)
                warpedExposure = clipboard.get(warpExposurePolicy.get("outputKeys.warpedExposure"))
                warpedExposure.writeFits("warped_%s" % (exposureName,))
                psfMatchedExposure.writeFits("psfMatched_%s" % (exposureName,))

    clipboard = pexHarness.Clipboard.Clipboard()
    psfMatchedMaskedImageList = afwImage.vectorMaskedImageF(
        [e.getMaskedImage() for e in psfMatchedExposureList])
    clipboard.put(outlierRejectionPolicy.get("inputKeys.maskedImageList"), psfMatchedMaskedImageList)
    outlierRejectionTester.runWorker(clipboard)
    coaddMaskedImage = clipboard.get(outlierRejectionPolicy.get("outputKeys.coadd"))
    coaddExposure = afwImage.makeExposure(coaddMaskedImage, referenceExposure.getWcs())
    weightMap = clipboard.get(outlierRejectionPolicy.get("outputKeys.weightMap"))
    return (coaddExposure, weightMap)

if __name__ == "__main__":
    pexLog.Trace.setVerbosity('lsst.coadd', Verbosity)
    helpStr = """Usage: makePsfCoaddWithOutlierRejection.py coaddPath psfMatchedExposureList  [psfMatchPolicyPath [outlierRejectionPolicyPath]]

where:
- coaddPath is the desired name or path of the output coadd
- psfMatchedExposureList is a file containing a list of:
    pathToExposure
  where:
  - pathToExposure is the path to an Exposure (without the final _img.fits)
  - the first exposure listed is the reference exposure:
        its size and WCS are used for the coadd exposure
  - empty lines and lines that start with # are ignored.
- psfMatchPolicyPath is the path to a policy file; overrides for policy/PsfMatchToImageStageDictionary.paf
- outlierRejectionPolicyPath is the path to a policy file; overrides for
    policy/OutlierRejectionStageDictionary.paf
"""
    if len(sys.argv) not in (3, 4):
        print helpStr
        sys.exit(0)
    
    outName = sys.argv[1]
    if os.path.exists(outName + "_img.fits"):
        print "Coadd file %s already exists" % (outName,)
        sys.exit(1)
    weightOutName = outName + "_weight.fits"
    
    psfMatchedExposureList = sys.argv[2]

    if len(sys.argv) > 3:
        policyPath = sys.argv[3]
        psfMatchPolicy = pexPolicy.Policy(policyPath)
    else:
        psfMatchPolicy = pexPolicy.Policy()
    # There doesn't seem to be a better way to get at the policy dict; it should come from the stage. Sigh.
    warpExposurePolFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "WarpExposureStageDictionary.paf",
        "policy")
    warpExposurePolicy = pexPolicy.Policy.createPolicy(warpExposurePolFile,
        warpExposurePolFile.getRepositoryPath())
    psfMatchPolFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "PsfMatchToImageStageDictionary.paf", "policy")
    defPsfMatchPolicy = pexPolicy.Policy.createPolicy(psfMatchPolFile, psfMatchPolFile.getRepositoryPath())
    psfMatchPolicy.mergeDefaults(defPsfMatchPolicy)

    if len(sys.argv) > 4:
        policyPath = sys.argv[4]
        outlierRejectionPolicy = pexPolicy.Policy(outlierRejectionPolicyPath)
    else:
        outlierRejectionPolicy = pexPolicy.Policy()
    outlierRejectionPolFile = pexPolicy.DefaultPolicyFile("coadd_pipeline",
        "OutlierRejectionStageDictionary.paf", "policy")
    defOutlierRejectionPolicy = pexPolicy.Policy.createPolicy(outlierRejectionPolFile,
        outlierRejectionPolFile.getRepositoryPath())
    outlierRejectionPolicy.mergeDefaults(defOutlierRejectionPolicy)
    
    exposurePathList = []
    with file(psfMatchedExposureList, "rU") as infile:
        for lineNum, line in enumerate(infile):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            filePath = line
            exposurePathList.append(filePath)

    coadd, weightMap = makeCoadd(exposurePathList, warpExposurePolicy, psfMatchPolicy, outlierRejectionPolicy)
    coadd.writeFits(outName)
    weightMap.writeFits(weightOutName)
