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

def makeCoadd(exposurePathList, policy):
    """Make a coadd using ChiSquaredStage
    
    Inputs:
    - exposurePathList: a list of paths to calibrated science exposures
    - policy: policy to control the coaddition stage
    """
    if len(exposurePathList) == 0:
        print "No images specified; nothing to do"
        return

    # until PR 1069 is fixed one cannot actually use SimpleStageTester to process multiple files
    # meanwhile just call the process method directly
        
    # set up pipeline
    stage = coaddPipe.ChiSquaredStage(policy)
#     tester = pexHarness.simpleStageTester.SimpleStageTester(stage)
#     tester.setDebugVerbosity(Verbosity)
    tempLog = pexLog.Log()
    parallelStage = coaddPipe.ChiSquaredStageParallel(policy, tempLog)

    # process exposures
    coadd = None
    lastInd = len(exposurePathList) - 1
    for expInd, exposurePath in enumerate(exposurePathList):
        isFirst = (expInd == 0)
        isLast = (expInd == lastInd)

        print "Processing exposure %d of %d: %s" % (expInd+1, lastInd+1, exposurePath)
        try:
            exposure = afwImage.ExposureF(filePath)
        except Exception, e:
            print "Skipping %s: %s" % (filePath, e)
            continue

        # set up the clipboard
        clipboard = pexHarness.Clipboard.Clipboard()
        inPolicy = policy.get("inputKeys")
        clipboard.put(inPolicy.get("exposure"), exposure)
        event = dafBase.PropertySet()
        event.add("isLastExposure", isLast)
        clipboard.put(inPolicy.get("event"), event)

        # run the stage
#        outClipboard = tester.runWorker(clipboard)
        parallelStage.process(clipboard)
        outClipboard = clipboard
    
        if isLast:
            # one could put this code after the loop, but then it is less robust against
            # code changes (e.g. making multiple coadds), early exit, etc.
            outPolicy = policy.get("outputKeys")
            coadd = outClipboard.get(outPolicy.get("coadd"))
            weightMap = outClipboard.get(outPolicy.get("weightMap"))
            return (coadd, weightMap)

    raise RuntimeError("Unexpected error; last exposure never run")

if __name__ == "__main__":
    pexLog.Trace.setVerbosity('lsst.coadd', Verbosity)
    helpStr = """Usage: makeCoadd.py coaddPath exposureList [policyPath]

where:
- coaddPath is the desired name or path of the output coadd
- exposureList is a file containing a list of:
    pathToExposure
  where:
  - pathToExposure is the path to an Exposure (without the final _img.fits)
  - the first exposure listed is the reference exposure:
        its size and WCS are used for the coadd exposure
  - empty lines and lines that start with # are ignored.
- policyPath is the path to a policy file
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
        policy = pexPolicy.Policy(policyPath)
    else:
        policy = pexPolicy.Policy()
    # remove the following bit once the code uses simpleStageTester
    policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "ChiSquaredStageDictionary.paf", "policy")
    print "policyFile %s loaded" % (policyFile,)
    defPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath())
    policy.mergeDefaults(defPolicy)
    
    exposurePathList = []
    with file(exposureList, "rU") as infile:
        for lineNum, line in enumerate(infile):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            filePath = line
            exposurePathList.append(filePath)

    coadd, weightMap = makeCoadd(exposurePathList, policy)
    coadd.writeFits(outName)
    weightMap.writeFits(weightOutName)
