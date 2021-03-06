#!/usr/bin/env python2.7

import os
import sys
import unittest

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from tests.test_notification_pusher import NotificationPusherTestCase
from tests.test_redirect_checker import RedirectCheckerTestCase
from tests.test_utils import UtilsTestCase
from tests.test_worker import WorkerTestCase
from tests.test_lib_init import InitLibTestCase


if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(NotificationPusherTestCase),
        unittest.makeSuite(RedirectCheckerTestCase),
        unittest.makeSuite(UtilsTestCase),
        unittest.makeSuite(WorkerTestCase),
        unittest.makeSuite(InitLibTestCase),
    ))
    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
