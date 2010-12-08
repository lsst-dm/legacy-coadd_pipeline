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
import lsst.pex.harness as pexHarness
import lsst.pex.policy as pexPolicy
import lsst.afw.image as afwImage
import lsst.coadd.pipeline as coaddPipe
from lsst.pex.harness import Clipboard, simpleStageTester

Verbosity = 5

def warpExposures(exposurePathList, policy):
    """Warp a set of exposures to match a reference exposure
    
    Inputs:
    - exposurePathList: a list of paths to calibrated science exposures;
        the first one is taken to be the reference (and so is not processed).
    - policy: policy to control the coaddition stage
    """
    if len(exposurePathList) == 0:
        print "No images specified; nothing to do"
        return

    # set up pipeline
    stage = coaddPipe.WarpExposureStage(policy)
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

        # set up the clipboard
        clipboard = pexHarness.Clipboard.Clipboard()
        clipboard.put(policy.get("inputKeys.exposure"), exposure)
        clipboard.put(policy.get("inputKeys.referenceExposure"), referenceExposure)

        # run the stage
        tester.runWorker(clipboard)
        
        warpedExposure = clipboard.get(policy.get("outputKeys.warpedExposure"))
        warpedExposure.writeFits("warped_%s" % (exposureName,))

if __name__ == "__main__":
    helpStr = """Usage: warpExposures.py exposureList [policyPath]

where:
- exposureList is a file containing a list of:
    pathToExposure
  where:
  - pathToExposure is the path to an Exposure (without the final _img.fits)
  - the first exposure listed is the reference exposure: all other exposures are warped to match it.
  - empty lines and lines that start with # are ignored.
- policyPath is the path to a policy file; overrides for policy/WarpExposureStageDictionary.py
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
    # There doesn't seem to be a better way to get at the policy dict; it should come from the stage. Sigh.
    policyFile = pexPolicy.DefaultPolicyFile("coadd_pipeline", "WarpExposureStageDictionary.paf", "policy")
    defPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath())
    policy.mergeDefaults(defPolicy)
    
    exposurePathList = []
    with file(exposureList, "rU") as infile:
        for lineNum, line in enumerate(infile):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            filePath = line
            fileName = os.path.basename(filePath)
            exposurePathList.append(filePath)

    warpExposures(exposurePathList, policy)
