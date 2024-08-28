import Queue
import time


class CustomContainsQueue(Queue.Queue):

    def __contains__(self, item):
        """
        Function to check if Queue contains a specific item

        :param item: Item to be checked against the Queue
        :type item: object

        :return: Boolean indicating if item is currently in the Queue
        :rtype: bool
        """
        with self.mutex:
            return item in self.queue

    def get_item(self, item):
        """
        Function to get a specific item from the Queue

        :param item: Item to be returned from the Queue
        :type item: object
        """
        if self.__contains__(item):
            self.queue.remove(item)

    def put_unique(self, item):
        """
        Function to add a specific item from the Queue

        :param item: Item to be added to the Queue
        :type item: object
        """
        if not self.__contains__(item):
            self.put_nowait(item)

    def block_until_item_removed(self, item, logger, max_time_to_wait=300):
        """
        Function to block until item is removed or timeout is reached.

        :param item: Item to be poll the Queue for, until removed or timeout reached
        :type item: object
        :param logger: Logger instance supplied to the function
        :type logger: `log.logger`
        :param max_time_to_wait: Maximum time in seconds to wait until removing the blocking item
        :type max_time_to_wait: int
        """
        elapsed_time = 0
        while self.__contains__(item) and elapsed_time <= max_time_to_wait:
            elapsed_time += 5
            sleep_time = max_time_to_wait if 1 <= max_time_to_wait <= 5 else 5
            logger.debug("Blocking operation in progress for {0}, waiting for {1} seconds before rechecking.".format(
                item, sleep_time))
            time.sleep(sleep_time)
        self.get_item(item)
