# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from twitter.common.dirutil import safe_mkdir

from pants.backend.android.targets.android_binary import AndroidBinary
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

    def is_gentarget(self, target):
        """Must return True if it handles generating for the target."""
        return isinstance(target, AndroidBinary)

    def genlangs(self, lang, targets):
        # this returns the language the generated code will be in
        return dict(java=lambda t: t.is_jvm)

    def genlang(self, lang, targets):

        """aapt must override and generate code in :lang for the given targets.

        May return a list of pairs (target, files) where files is a list of files
        to be cached against the target.
        """


        # Here is action.

            # somewhere here we will need to handle "crunch" command for release builds.

        for target in targets:
            if lang != 'java':
                raise TaskError('Unrecognized android gen lang: %s' % lang)
            aapt_output = safe_mkdir(self._aapt_out(target))
            args = ["package", "-m -J", aapt_output, "-M", target.manifest, "-S", target.resources, "-I", self.android_jar_tool(target)]
        # if aapt returns NULL -- file does not exist or no permission to read.

    def createtarget(self, lang, gentarget, dependees):
        """from: CodeGen: aapt class must override and create a synthetic target.
         The target must contain the sources generated for the given gentarget.
        """
        #This method creates the new target to replace the acted upon resources in the target graph




    # The CodeGen superclass implements some caching in execute() Investigate more.

    def _aapt_out(self, target):
        return os.path.join(target.address.safe_spec_path, 'bin')

    def manifest(self, target):
        #TODO This probably needs to go in android_binary target.

        # Android builds proscribe the AndroidManifest.xml location, but
        #  perhaps there is a better way to handle this
        #   N.B. Buck allows any name for Manifest and just aliases the file when passed to tooling. Value?
        return os.path.join(target.address.safe_spec_path, 'AndroidManifest.xml')


    # resolve the tools on a per-target basis
    def aapt_tool(self, target):
        return (os.path.join(self._sdk_path, ('build-tools/' + target.build_tools_version), 'aapt'))

    def android_jar_tool(self, target):
        return (os.path.join(self._sdk_path, 'platforms', ('android-' + target.target_sdk_version), 'android.jar'))
