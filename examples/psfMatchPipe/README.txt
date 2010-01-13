This example will run a version of the PSFMatch pipeline.  To run,
type:

   python testPsfMatchPipe.py

When called this way, it will look for input data in the optional data
package, coadd_pipeline_data.  If this is not available, one must
provide the directory containing the data (listed in
testSelectImages.paf) as an extra argument.  

This test script is implemented as a unit test (using Python's
unittest module) wrapped around SimpleStageTester.  The stages that
are included are listed in testPSFMatch.paf, but because
SimpleStageTester is used to run the stages, the testPSFMatch.paf is
not used.  

Editor's Note: other scripts for running this script (in particular,
to run the pipeline over a list of exposures) are still in the works.



   