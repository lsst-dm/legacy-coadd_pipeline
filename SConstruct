# -*- python -*-
#
# Setup our environment
#
import os.path
import lsst.SConsUtils as scons

env = scons.makeEnv("coadd_pipeline",
                    r"$HeadURL: svn+ssh://svn.lsstcorp.org/DMS/coadd/pipeline/trunk/SConstruct $",
                    []
                    )
#
# Build/install things
#
for d in Split("doc tests python/lsst/coadd/pipeline"):
    SConscript(os.path.join(d, "SConscript"))

env['IgnoreFiles'] = r"(~$|\.pyc$|^\.svn$|\.o$)"

Alias("install", [
    env.InstallAs(os.path.join(env['prefix'], "doc", "htmlDir"), os.path.join("doc", "htmlDir")),
    env.Install(env['prefix'], "examples"),
    env.Install(env['prefix'], "policy"),
    env.Install(env['prefix'], "python"),
    env.Install(env['prefix'], "tests"),
    env.InstallEups(os.path.join(env['prefix'], "ups")),
])

scons.CleanTree(r"*~ core *.so *.os *.o *.pyc")
#
# Build TAGS files
#
files = scons.filesToTag()
if files:
    env.Command("TAGS", files, "etags -o $TARGET $SOURCES")

env.Declare()
env.Help("""
A base package for other coadd packages.
""")

