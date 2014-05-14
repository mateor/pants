# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os

from twitter.common.dirutil import safe_mkdtemp, safe_rmtree
from pants_test.pants_run_integration_test import PantsRunIntegrationTest

from mock import MagicMock, patch


@patch('sys.stdin')
class JarPublishIntegrationTest(PantsRunIntegrationTest):

  def test_scala_publish(self, MagicMock):
    self.package_namespace = 'com/pants/example/jvm-example-lib/0.0.1-SNAPSHOT'
    self.publish_test('src/scala/com/pants/example/BUILD:jvm-run-example-lib',
                      ['ivy-0.0.1-SNAPSHOT.xml',
                       'jvm-example-lib-0.0.1-SNAPSHOT.jar',
                       'jvm-example-lib-0.0.1-SNAPSHOT.pom',
                       'jvm-example-lib-0.0.1-SNAPSHOT-javadoc.jar',
                       'jvm-example-lib-0.0.1-SNAPSHOT-sources.jar'])


  def test_scala_publish1(self, MagicMock):
    self.package_namespace = 'com/pants/example/hello-greet/0.0.1-SNAPSHOT/'
    self.publish_test('src/java/com/pants/examples/hello/greet',
                      ['ivy-0.0.1-SNAPSHOT.xml',
                       'hello-greet-0.0.1-SNAPSHOT.jar',
                       'hello-greet-0.0.1-SNAPSHOT.pom',
                       'hello-greet-0.0.1-SNAPSHOT-javadoc.jar',
                       'hello-greet-0.0.1-SNAPSHOT-sources.jar'])

  def publish_test(self, target, artifacts=[]):
    dir = safe_mkdtemp()
    with patch('__builtin__.raw_input', return_value='Y'):
      with self.run_pants(['publish', target,
                           '--publish-local=%s' % dir,
                           '--no-publish-dryrun',
                           '--no-publish-commit',
                           '--publish-force',
                           '--publish-jar_create_publish-sources']) as pants_run:
        for file in artifacts:
          self.assertTrue(os.path.exists(os.path.join(dir,
                                                      self.package_namespace,
                                                      file)))
    self.assertEquals(pants_run, self.PANTS_SUCCESS_CODE)
    safe_rmtree(dir)

