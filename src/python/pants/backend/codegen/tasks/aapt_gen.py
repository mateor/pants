# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from twitter.common.dirutil import safe_mkdir

from pants.backend.android.targets.android_target import AndroidTarget
from pants.base.exceptions import TaskError
from pants.backend.android.tasks.android_task import AndroidTask
from pants.backend.codegen.tasks.code_gen import CodeGen



class AaptGen(AndroidTask, CodeGen):
    """
    CodeGen for Android app building with the Android Asset Packaging Tool.
    There may be an aapt superclass, as it has future packaging functions besides codegen.

    aapt supports 6 major commands: {dump, list, add, remove, crunch, package}
    For right now, pants is only supporting 'package'. More to come as we support Release builds (crunch, at minimum).

    Commands and flags for aapt can be seen here:
    https://android.googlesource.com/platform/frameworks/base/+/master/tools/aapt/Command.cpp
    """

    def __init__(self, context, workdir):
        #define the params needed in the BUILD file {name, sources, dependencies, etc.}
        super(AaptGen, self).__init__(self, context, workdir)
        self.aapt = self._dist.aapt_tool()

    def is_gentarget(self, target):
        """Must return True if it handles generating for the target."""
        # TODO: this should be "isInstance(target, AndroidBinary)" when that target is written
        return isinstance(target, AndroidTarget)

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
            manifest_location = self.manifest(target)
            # TODO: in process- resolve the proper android.jar tool and pass it as final arg
            args = ["package", "-m -J", output_dir, "-M". manifest_location, "-S", target.resources, "-I", ]

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

    def manifest(self, target):
        #TODO This probably needs to go in android_binary target.

        # Android builds proscribe the AndroidManifest.xml location, but
        #  perhaps there is a better way to handle this
        return os.path.join(target.address.safe_spec_path, 'AndroidManifest.xml')
