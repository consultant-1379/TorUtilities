#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.services import custom_queue
from testslib import unit_test_utils


class CustomContainsQueueUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.queue = custom_queue.CustomContainsQueue()
        self.item = "TEST_00"
        self.item_two = "TEST_01"

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_queue__contains__item(self):
        self.queue.empty()
        self.queue.put_unique(self.item)
        self.assertIn(self.item, self.queue)
        self.assertNotIn(self.item_two, self.queue)

    def test_get_item__removes_item(self):
        self.queue.empty()
        self.queue.put_unique(self.item)
        self.assertIn(self.item, self.queue)
        self.queue.get_item(self.item)
        self.assertNotIn(self.item, self.queue)

    def test_put_item__only_adds_unique(self):
        self.queue.empty()
        self.queue.put_unique(self.item)
        self.assertIn(self.item, self.queue)
        self.assertEqual(self.queue.qsize(), 1)
        self.queue.put_unique(self.item_two)
        self.assertEqual(self.queue.qsize(), 2)
        self.queue.put_unique(self.item)
        self.assertEqual(self.queue.qsize(), 2)

    @patch('enmutils_int.lib.services.custom_queue.time.sleep', return_value=0)
    def test_block_until_item_removed__no_sleep_if_item_not_found(self, _):
        logger = Mock()
        self.queue.empty()
        self.queue.block_until_item_removed(self.item, logger)
        self.assertEqual(0, logger.debug.call_count)

    @patch('enmutils_int.lib.services.custom_queue.time.sleep', return_value=0)
    def test_block_until_item_removed__block_until_item_removed(self, _):
        logger = Mock()
        self.queue.empty()
        self.queue.put_unique(self.item)
        self.queue.block_until_item_removed(self.item, logger, max_time_to_wait=6)
        self.assertEqual(2, logger.debug.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
