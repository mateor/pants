# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from twitter.common.dirutil import safe_mkdir

from pants.tasks.task import Task
from pants.tasks.task import TaskError
from pants.tasks.code_gen import CodeGen



class AaptGen(CodeGen):
    """
    CodeGen for Android app building with the Android Asset Packaging Tool.
    There may be an aapt superclass, as it has future packaging functions besides codegen.

    aapt supports 6 major commands: {dump, list, add, remove, crunch, package}
    For right now, pants is only supporting 'package'. More to come as we see use cases.

    Commands and flags for aapt can be seen here:
    https://android.googlesource.com/platform/frameworks/base/+/master/tools/aapt/Command.cpp
    """

    def __init__(self):
        #define the params needed in the BUILD file {name, sources, dependencies, etc.}
        pass

    def is_gentarget(self, target):
        """Nust return True if it handles generating for the target."""
        # TODO: this should be "isInstance(target, AndroidBinary)" when that target is written
        return True

    def genlangs(self, lang, targets):
        # this returns the language the generated code will be in
        return dict(java=lambda t: t.is_jvm)

    def genlang(self, lang, targets):

        """aapt must override and generate code in :lang for the given targets.

        May return a list of pairs (target, files) where files is a list of files
        to be cached against the target.
        """
        # Here is action.
        for target in targets:
            if lang != 'java':
                raise TaskError('Unrecognized android gen lang: %s' % lang)
            output_dir = safe_mkdir(self._aapt_out(target))


        # if aapt returns NULL -- file does not exist or no permission to read.

    def createtarget(self, lang, gentarget, dependees):
        """from: CodeGen: aapt class must override and create a synthetic target.
         The target must contain the sources generated for the given gentarget.
        """
        #This method creates the new target to replace the acted upon resources in the target graph




    # The CodeGen superclass implements some caching in execute() Investigate more.

    # somewhere in here we need to setup output directories. antler_gen makes the java_out
    #    so lets make output dirs in the classes to which they belong. That means we need:
    #    safe_mkdir(bin) --- antlr does it in genlang()

    def _aapt_out(self, target):
        return os.path.join(target.address.safe_spec_path, 'bin')