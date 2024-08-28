import datetime
import inspect
import time
from random import randint, sample, choice

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironWarning, EnmApplicationError
from enmutils.lib.timestamp import get_int_time_in_secs_since_epoch
from enmutils_int.lib.pm_subscriptions import CelltraceSubscription, StatisticalSubscription, Subscription
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class PM_06(GenericFlow):
    """
    Use Case id:    PM_06
    Slogan:         Average number of PMIC GUI users
    """
    NAME = "PM_06"
    NUM_NODES = {}
    THREAD_QUEUE_TIMEOUT = 60 * 60 * 24  # 24 hours
    JOIN_QUEUE_TIMEOUT = 30
    THREADING_TEARDOWN_TIMER = 10  # Time the teardown method will wait before tearing down
    thread_list = list()
    NUM_USERS = 0
    subscriptions = []
    PERCENT_USERS = {}
    USER_ROLES = None
    STATS_UNSUPPORTED_NODE_TYPES = []
    CELLTRACE_SUPPORTED_NODE_TYPES = []
    ADD_NODES_TO_SUBSCRIPTION = ""
    MAX_NODES_TO_ADD = 0
    NUM_COUNTERS = 0
    NODES_PER_SUBSCRIPTION = 0
    NUM_EVENTS = 0

    def run(self):
        self.state = "RUNNING"

        node_attributes = ["node_id", "netsim", "simulation", "primary_type", "node_name", "profiles"]
        profile_nodes_list = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        self.deallocate_stats_unsupported_nodes(profile_nodes_list)
        task_sets = self.create_tasksets()
        self._next_run = datetime.datetime.now()

        while self.keep_running():
            self.subscriptions = []
            log.logger.debug("Iteration start")

            # Add the threads to a single thread to execute all: 64 threads needed for simultaneous run
            self.create_and_execute_threads(task_sets, self.NUM_USERS,
                                            func_ref=task_executor, args=[profile_nodes_list, self],
                                            wait=self.THREAD_QUEUE_TIMEOUT, last_error_only=True)

            try:
                log.logger.debug("Main thread: Cleaning up subscriptions")
                Subscription.clean_subscriptions(name=self.NAME[:5], fast=True)
            except Exception as e:
                self.add_error_as_exception(e)

            log.logger.debug("Teardown List: {0}".format(self.teardown_list))
            log.logger.debug("Iteration end")
            self.sleep()

    def create_users_based_on_percentage(self, percentage_of_users):
        """
        Create a list of Users based on the percentage of users of the overall NUM_USERS for the profile

        :param percentage_of_users: Percentage of Users
        :type percentage_of_users: int
        :return: List of Users
        :rtype: list
        """
        num_users = int(float(self.NUM_USERS) / 100 * percentage_of_users)
        if num_users:
            return self.create_profile_users(num_users, self.USER_ROLES, safe_request=True)
        else:
            return []

    def create_tasksets(self):
        """
        Create a list of tasksets, which themselves are a list of tuples

        :return: list of tuples
        :rtype: list
        """
        baseline_polling_taskset = [([user], polling_task_set) for user in
                                    self.create_users_based_on_percentage(self.PERCENT_USERS['baseline_polling'])]

        burst_polling_taskset = [([user], burst_polling_task_set) for user in
                                 self.create_users_based_on_percentage(self.PERCENT_USERS['burst_polling'])]

        create_delete_subscriptions_taskset = [
            (self.create_users_based_on_percentage(self.PERCENT_USERS['create_delete_sub']),
             create_delete_subscriptions_task_set)]

        change_counters_taskset = [(self.create_users_based_on_percentage(self.PERCENT_USERS['change_counters']),
                                    change_counters_task_set)]

        activate_deactivate_subs_taskset = [(
            self.create_users_based_on_percentage(self.PERCENT_USERS['activate_deactivate']),
            activate_deactivate_subscriptions)]

        add_delete_nodes_taskset = [(self.create_users_based_on_percentage(self.PERCENT_USERS['add_delete_nodes']),
                                     add_delete_nodes_task_set)]

        task_sets = (baseline_polling_taskset + burst_polling_taskset + create_delete_subscriptions_taskset +
                     change_counters_taskset + activate_deactivate_subs_taskset + add_delete_nodes_taskset)

        return task_sets

    def deallocate_stats_unsupported_nodes(self, allocated_nodes):
        """
        Deallocate the stats unsupported node types from pm_06 profile

        :param allocated_nodes: Nodes assigned to profile
        :type allocated_nodes: list
        """
        unsupported_nodes = []
        for node in allocated_nodes:
            if node.primary_type in self.STATS_UNSUPPORTED_NODE_TYPES:
                unsupported_nodes.append(node)
        self.update_profile_persistence_nodes_list(unsupported_nodes)


def task_executor(user_task_set, profile_nodes_list, profile):
    """
    Execute the individual functions for each user/taskset combination

    :param user_task_set: Tuple for each user/taskset
    :type user_task_set: tuple
    :param profile_nodes_list: Nodes assigned to profile
    :type profile_nodes_list: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    user, taskset = user_task_set
    taskset(user, profile_nodes_list, profile)


def polling_task_set(users, _, profile):
    """
    Poll PM Rest Interface for 24 Hours every minute

    :param users: List of users performing task
    :type users: list
    :param _: Nodes assigned to profile (not required in this task set)
    :type _: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    task_name = "Task 1 {0}:".format(inspect.stack()[0][3])
    log.logger.debug("{0} Start - Executing continuous polling task set with 1 minute interval for 24 hrs"
                     .format(task_name))

    expected_thread_execution_time_secs = 24 * 60 * 60
    grace_time_secs = 60

    random_start_offset_time_secs = randint(0, 60)
    log.logger.debug("{0} Sleeping for random {1}s offset from start of thread"
                     .format(task_name, random_start_offset_time_secs))
    time.sleep(random_start_offset_time_secs)

    polling_period_duration_secs = (expected_thread_execution_time_secs - random_start_offset_time_secs -
                                    grace_time_secs)
    performing_continuous_polling(task_name, users[0], polling_period_duration_secs, profile)

    log.logger.debug("{0} has completed".format(task_name))


def burst_polling_task_set(users, _, profile):
    """
    Poll PM Rest Interface every minute for 1 Hour

    :param users: List of users performing task
    :type users: list
    :param _: Nodes assigned to profile (not required in this task set)
    :type _: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    task_name = "Task 2 {0}:".format(inspect.stack()[0][3])
    log.logger.debug("{0} Start - Execute burst polling task set after 8 hours for 1 hour with 1 minute interval"
                     .format(task_name))

    polling_period_duration_secs = 60 * 60

    random_start_offset_time_secs = randint(0, 60)
    log.logger.debug("{0} Sleeping for random {1}s offset from start of thread"
                     .format(task_name, random_start_offset_time_secs))

    time.sleep(random_start_offset_time_secs)

    log.logger.debug("{0} Sleeping for 8 hours before starting burst".format(task_name))
    time.sleep(60 * 60 * 8)

    log.logger.debug("{0} Start Burst Polling of PM for 1 hour".format(task_name))
    performing_continuous_polling(task_name, users[0], polling_period_duration_secs, profile)
    log.logger.debug("{0} has completed".format(task_name))


def performing_continuous_polling(task_name, user, polling_time_secs, profile):
    """
    Perform continuous polling

    :param task_name: Name of task
    :type task_name: str
    :param polling_time_secs: Time to spend polling ENM
    :type polling_time_secs: int
    :param user: User performing ENM queries
    :type user: enm_user_2.User
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    iteration = 1
    while polling_time_secs > 60:
        time_start = int(get_int_time_in_secs_since_epoch())
        log.logger.debug("{0} Performing iteration {1}".format(task_name, iteration))
        if poll_pm(user, profile):
            profile.add_error_as_exception(EnmApplicationError("Errors occurred while performing GET requests"))

        time_end = int(get_int_time_in_secs_since_epoch())
        time_taken_secs = time_end - time_start
        polling_time_secs -= time_taken_secs

        if time_taken_secs < 60:
            time_to_sleep = 60 - time_taken_secs
            log.logger.debug("{0} Sleeping for {1} sec until next poll operation".format(task_name, time_to_sleep))
            time.sleep(time_to_sleep)
            polling_time_secs -= time_to_sleep

        iteration += 1


def create_delete_subscriptions_task_set(users, profile_nodes_list, profile):
    """
    Sets up and tears down 5 subscriptions where the workload will be applied on.

    :param users: user list assigned for this task set
    :type users: list
    :param profile_nodes_list: Nodes assigned to profile
    :type profile_nodes_list: list
    :param profile: pm_06 profile instance
    :type profile: PM_06

    :raises EnvironWarning: if required node count not met on deployment.
    """

    task_name = "Task 3 {0}:".format(inspect.stack()[0][3])
    log.logger.debug("{0} Start - Sets up and tears down 5 subscriptions".format(task_name))

    stats_supported_node_list = [node for node in profile_nodes_list if
                                 node.primary_type not in profile.STATS_UNSUPPORTED_NODE_TYPES]

    celltrace_supported_node_list = [node for node in profile_nodes_list if
                                     node.primary_type in profile.CELLTRACE_SUPPORTED_NODE_TYPES]

    if len(stats_supported_node_list) < profile.NODES_PER_SUBSCRIPTION:
        raise (
            EnvironWarning("Number of nodes available to the profile is not enough to perform the create/delete "
                           "subscription task (minimum {0} nodes for stats and celltrace required). "
                           "{1}/{0} stats supported nodes; {2}/{0} celltrace supported nodes. "
                           .format(profile.NODES_PER_SUBSCRIPTION,
                                   len(stats_supported_node_list),
                                   len(celltrace_supported_node_list))))

    create_and_activate_stats_subscriptions(users, profile, stats_supported_node_list)
    create_and_delete_cell_and_stats_alternatively(users, profile, stats_supported_node_list,
                                                   celltrace_supported_node_list)
    delete_stats_subscriptions(users, profile)

    log.logger.debug("{0} has completed".format(task_name))


def create_and_activate_stats_subscriptions(users, profile, stats_supported_node_list):
    """
    Create some stats subscriptions

    :param users: list of user objects
    :type users: list
    :param profile: Profile Object
    :type profile: PM_06
    :param stats_supported_node_list: list of supported Node objects for Stats Subscriptions
    :type stats_supported_node_list: list
    """
    task_name = "Subtask 1 {0}:".format(inspect.stack()[0][3])
    interval_secs = 15 * 60
    log.logger.debug("{0} Start - Create & Activate 5 Statistical subscriptions with {1} mins interval "
                     .format(task_name, interval_secs / 60))

    iteration_count = 5
    for iteration in xrange(iteration_count):
        time_at_start_of_iteration = get_int_time_in_secs_since_epoch()
        log.logger.debug("{0} Performing iteration {1}/{2}".format(task_name, iteration + 1, iteration_count))
        sub_nodes = sample(stats_supported_node_list, profile.NODES_PER_SUBSCRIPTION)
        sub_user = choice(users)
        get_pm_home(sub_user, profile)

        subscription_name = "{0}-WORKER-{1}".format(profile.identifier, iteration)
        subscription = StatisticalSubscription(user=sub_user, name=subscription_name,
                                               nodes=sub_nodes, num_counters=profile.NUM_COUNTERS,
                                               description=profile.NAME + '_load_profile')
        teardown_subscription = StatisticalSubscription(user=sub_user, name=subscription_name)

        try:
            log.logger.debug("{0} Create subscription {1}: {2} with nodes: {3}"
                             .format(task_name, iteration, subscription_name, sub_nodes))
            subscription.create()
            teardown_subscription.id = subscription.id
            profile.subscriptions.append(subscription)
            profile.teardown_list.append(teardown_subscription)
        except Exception as e:
            profile.add_error_as_exception(e)
        if iteration != (iteration_count - 1):
            time_taken = get_int_time_in_secs_since_epoch() - time_at_start_of_iteration
            sleep_time = interval_secs - time_taken
            log.logger.debug("{0} Time taken: {1}. Sleeping for {2}s".format(task_name, time_taken, sleep_time))
            time.sleep(sleep_time)
        else:
            try:
                subscription.activate()
            except Exception as e:
                profile.add_error_as_exception(e)

    log.logger.debug("{0} Complete".format(task_name))


def create_and_delete_cell_and_stats_alternatively(users, profile, stats_supported_node_list,
                                                   celltrace_supported_node_list):
    """
    Creating and deleting 5 cell and stats subscriptions each alternatively with 1 hr interval

    :param users: list of user objects
    :type users: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    :param stats_supported_node_list: list of supported Node objects for Stats Subscriptions
    :type stats_supported_node_list: list
    :param celltrace_supported_node_list: list of supported Node Objects for Cell Trace Subscriptions
    :type celltrace_supported_node_list: list
    """
    task_name = "Subtask 2 {0}:".format(inspect.stack()[0][3])
    log.logger.debug("{0} Start - Create and delete 5 cell and stats subscriptions alternatively, with 1 hr "
                     "interval between creation and deletion".format(task_name))

    interval_secs = 60 * 60
    time_taken_to_delete_sub = 0
    iteration_count = 10

    for iteration in xrange(iteration_count):
        log.logger.debug("{0} Performing iteration {1}/{2}".format(task_name, iteration + 1, iteration_count))

        time_to_sleep_until_create = interval_secs - time_taken_to_delete_sub
        log.logger.debug("{0} Sleeping for {1} before Subscription creation"
                         .format(task_name, time_to_sleep_until_create))
        time.sleep(time_to_sleep_until_create)

        sub_user = choice(users)
        get_pm_home(sub_user, profile)
        if iteration % 2 == 0:
            if len(celltrace_supported_node_list) < profile.NODES_PER_SUBSCRIPTION:
                log.logger.debug(
                    "Skipping create/delete Cell trace Subscription task as nodes allocated are less than {0};"
                    " {1}/{0} celltrace supported nodes.".format(profile.NODES_PER_SUBSCRIPTION,
                                                                 len(celltrace_supported_node_list)))
                log.logger.debug("{0} Sleeping for 1 hour as normally sleep occurs after subscription deletion"
                                 .format(task_name))
                time.sleep(interval_secs)
                continue
            subscription_name = "{0}_CELL".format(profile.identifier)
            sub_nodes = sample(celltrace_supported_node_list, profile.NODES_PER_SUBSCRIPTION)
            sub = CelltraceSubscription(user=sub_user, name=subscription_name, nodes=sub_nodes,
                                        num_events=profile.NUM_EVENTS,
                                        description=profile.NAME + '_load_profile')
            teardown_subscription = CelltraceSubscription(user=sub_user, name=subscription_name)

        else:
            subscription_name = "{0}_STATS".format(profile.identifier)
            sub_nodes = sample(stats_supported_node_list, profile.NODES_PER_SUBSCRIPTION)
            sub = StatisticalSubscription(user=sub_user, name=subscription_name,
                                          nodes=sub_nodes, num_counters=profile.NUM_COUNTERS,
                                          description=profile.NAME + '_load_profile')
            teardown_subscription = StatisticalSubscription(user=sub_user, name=subscription_name)

        log.logger.debug("{0} Create Subscription {1}: {2}".format(task_name, iteration, subscription_name))

        sub_created_at_time = get_int_time_in_secs_since_epoch()
        try:
            sub.create()
        except Exception as e:
            profile.add_error_as_exception(e)

        teardown_subscription.id = sub.id
        profile.teardown_list.append(teardown_subscription)
        time_taken_to_create_sub = get_int_time_in_secs_since_epoch() - sub_created_at_time
        sleep_time_until_delete = interval_secs - time_taken_to_create_sub
        log.logger.debug("{0} Time taken to complete create subscription operation: {1}. Sleeping for {2}s before Subscription removal"
                         .format(task_name, time_taken_to_create_sub, sleep_time_until_delete))
        time.sleep(sleep_time_until_delete)

        log.logger.debug("{0} Delete Subscription {1}: {2}".format(task_name, iteration, subscription_name))
        sub_deleted_at_time = get_int_time_in_secs_since_epoch()
        try:
            sub.delete()
        except Exception as e:
            profile.add_error_as_exception(e)

        time_taken_to_delete_sub = get_int_time_in_secs_since_epoch() - sub_deleted_at_time
        log.logger.debug("{0} Time taken to complete delete subscription operation: {1}s".format(task_name, time_taken_to_delete_sub))
        profile.teardown_list.remove(teardown_subscription)

    log.logger.debug("{0} has completed".format(task_name))


def delete_stats_subscriptions(users, profile):
    """
    Delete the remaining subscriptions

    :param profile: Profile object
    :type profile: PM_06
    :param users: list of user objects
    :type users: list
    """
    task_name = "Subtask 3 {0}:".format(inspect.stack()[0][3])
    interval_secs = 15 * 60
    log.logger.debug("{0} Start - Delete 5 Statistical subscriptions with {1} mins interval between each deletion"
                     .format(task_name, interval_secs / 60))

    log.logger.debug("{0} Sleeping for 1 hour".format(task_name))
    time.sleep(60 * 60)

    deleted_subscriptions = []
    for subscription in profile.subscriptions:
        time_at_start_of_iteration = get_int_time_in_secs_since_epoch()
        log.logger.debug("{0} Removing subscription {1}".format(task_name, subscription.name))
        sub_user = choice(users)
        get_pm_home(sub_user, profile)
        try:
            log.logger.debug("{0} Check state of subscription {1}".format(task_name, subscription.name))
            if subscription.state == 'ACTIVE':
                log.logger.debug("{0} Need to deactivate subscription {1}".format(task_name, subscription.name))
                subscription.deactivate()
            log.logger.debug("{0} Delete subscription {1}".format(task_name, subscription.name))
            subscription.delete()
            deleted_subscriptions.append(subscription.name)
        except Exception as e:
            profile.add_error_as_exception(e)

        log.logger.debug("{0} Remove subscription {1} from teardown list (containing {2} items)"
                         .format(task_name, subscription.name, len(profile.teardown_list)))
        for item in profile.teardown_list:
            if isinstance(item, Subscription) and subscription.name in item.name:
                profile.teardown_list.remove(item)
                log.logger.debug("{0} Subscription {1} removed from teardown list (containing {2} items)"
                                 .format(task_name, subscription.name, len(profile.teardown_list)))

        time_taken = get_int_time_in_secs_since_epoch() - time_at_start_of_iteration
        sleep_time = interval_secs - time_taken
        log.logger.debug("{0} Sleeping for {1}s".format(task_name, sleep_time))
        time.sleep(sleep_time)

    log.logger.debug("{0} Removing subscriptions {0} from list".format(task_name))
    for name in deleted_subscriptions:
        profile.subscriptions = [subscription for subscription in profile.subscriptions if subscription.name != name]

    log.logger.debug("{0} has completed".format(task_name))


def change_counters_task_set(users, _, profile):
    """
    Changes counters on a subscription with name WORKER-0 or WORKER-1

    :param users: List of users performing task
    :type users: list
    :param _: Nodes assigned to profile (not required in this task set)
    :type _: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    task_name = "Task 4 {0}:".format(inspect.stack()[0][3])
    worker_index_1 = 0
    worker_index_2 = 1
    log.logger.debug("{0} Start - Changes counters on a subscription with name WORKER-{1} or WORKER-{2}"
                     .format(task_name, worker_index_1, worker_index_2))

    log.logger.debug("{0} Sleeping for 2 hours".format(task_name))
    time.sleep(60 * 60 * 2)

    iteration_count = 20
    for iteration in xrange(iteration_count):
        log.logger.debug("{0} Performing iteration {1}/{2}".format(task_name, iteration + 1, iteration_count))
        sub_user = choice(users)
        name = "WORKER-" + str(randint(worker_index_1, worker_index_2))
        for subscription in profile.subscriptions:
            if name in subscription.name:
                log.logger.debug("{0} Processing subscription {1}".format(task_name, subscription.name))
                subscription.user = sub_user
                try:
                    number_of_counters = randint(1, 100)
                    log.logger.debug("{0} Updating subscription {1} with {2} random counters"
                                     .format(task_name, subscription.name, number_of_counters))
                    subscription.update(counters=number_of_counters)
                    log.logger.debug("{0} Subscription {1} updated".format(task_name, subscription.name))
                    break
                except Exception as e:
                    profile.add_error_as_exception(e)

        log.logger.debug("{0} Sleeping for 1 hour".format(task_name))
        time.sleep(60 * 60)

    log.logger.debug("{0} has completed".format(task_name))


def add_delete_nodes_task_set(users, profile_nodes_list, profile):
    """
    Add & deletes nodes from subscription WORKER-4

    :param users: user list assigned for this task set
    :type users: list
    :param profile_nodes_list: Nodes assigned to profile
    :type profile_nodes_list: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    task_name = "Task 5 {0}:".format(inspect.stack()[0][3])
    log.logger.debug("{0} Start - Add & deletes nodes to/from active subscription {1}"
                     .format(task_name, profile.ADD_NODES_TO_SUBSCRIPTION))

    log.logger.debug("{0} Sleeping for 6 hours".format(task_name))
    time.sleep(60 * 60 * 6)

    profile_nodes = [node for node in profile_nodes_list if
                     node.primary_type not in profile.STATS_UNSUPPORTED_NODE_TYPES]

    action = "Delete"
    name = profile.ADD_NODES_TO_SUBSCRIPTION
    action_count = 0
    for _ in xrange(profile.MAX_NODES_TO_ADD * 2):
        action = "Add" if action == "Delete" else "Delete"
        action_count += 1
        log.logger.debug("{0} Performing iteration {1}: {2} nodes".format(task_name, action_count, action))

        sub_user = choice(users)
        for subscription in profile.subscriptions:
            if name in subscription.name:
                log.logger.debug("{0} Processing subscription {1}".format(task_name, subscription.name))
                subscription.user = sub_user
                try:
                    updated_nodes = get_nodes_to_be_updated_for_subscription(action, subscription, profile_nodes)
                    log.logger.debug("{0} Updating subscription {1} with following nodes {2}"
                                     .format(task_name, subscription.name, [node.node_id for node in updated_nodes]))

                    subscription.update(nodes=updated_nodes)
                    log.logger.debug("{0} Subscription {1} updated".format(task_name, subscription.name))
                    break
                except Exception as e:
                    profile.add_error_as_exception(e)

        log.logger.debug("{0} Sleeping for 1.5 hours".format(task_name))
        time.sleep(60 * 60 * 1.5)

    log.logger.debug("{0} has completed".format(task_name))


def get_nodes_to_be_updated_for_subscription(action, subscription, profile_nodes):
    """
    Fetch list of nodes to be used for subscription

    :param action: String to indicate if nodes are being added or deleted
    :type action: str
    :param subscription: Subscription object
    :type subscription: `Subscription`
    :param profile_nodes: List of nodes allocated to profile
    :type profile_nodes:
    :return: List of nodes to be used for subscription
    :rtype: list

    """
    log.logger.debug("Determine nodes to be added/removed from subscription")
    new_nodes = subscription.nodes
    if action == "Add":
        candidate_nodes = [node for node in profile_nodes if node not in subscription.nodes]
        if candidate_nodes:
            node_to_be_added = sample(candidate_nodes, 1)
            new_nodes = subscription.nodes + node_to_be_added

        else:
            log.logger.debug("No suitable nodes available to be added")

    else:
        candidate_nodes = subscription.nodes[1:]
        if candidate_nodes:
            node_to_be_removed = sample(candidate_nodes, 1)[0]
            new_nodes = [node for node in subscription.nodes if node is not node_to_be_removed]
        else:
            log.logger.debug("No suitable nodes available to be removed")

    log.logger.debug("Nodes determined: {0}".format([node.node_id for node in new_nodes]))
    return new_nodes


def activate_deactivate_subscriptions(users, _, profile):
    """
    Activate or deactivate subscription WORKER-2 or WORKER-3

    :param users: List of users performing task
    :type users: list
    :param _: Nodes assigned to profile (not required in this task set)
    :type _: list
    :param profile: pm_06 profile instance
    :type profile: PM_06
    """
    task_name = "Task 6 {0}:".format(inspect.stack()[0][3])
    worker_index_2 = 2
    worker_index_3 = 3
    log.logger.debug("{0} Start - Activate or deactivate subscription WORKER-{1} or WORKER-{2}"
                     .format(task_name, worker_index_2, worker_index_3))

    log.logger.debug("{0} Sleeping for 2 hours".format(task_name))
    time.sleep(60 * 60 * 2)

    iteration_count = 5
    for iteration in xrange(iteration_count):
        log.logger.debug("{0} Performing iteration {1}/{2}".format(task_name, iteration + 1, iteration_count))
        sub_user = choice(users)
        name = "WORKER-" + str(randint(worker_index_2, worker_index_3))
        for subscription in profile.subscriptions:
            if name in subscription.name:
                log.logger.debug("{0} Processing subscription {1}".format(task_name, subscription.name))
                subscription.user = sub_user
                try:
                    subscription.activate()
                except Exception as e:
                    profile.add_error_as_exception(e)
                log.logger.debug("{0} Sleeping for 1.5 hours".format(task_name))
                time.sleep(60 * 60 * 1.5)
                try:
                    subscription.deactivate()
                except Exception as e:
                    profile.add_error_as_exception(e)
                log.logger.debug("{0} Sleeping for 1.5 hours".format(task_name))
                time.sleep(60 * 60 * 1.5)
                break

    log.logger.debug("{0} has completed".format(task_name))


def get_pm_home(user, profile):
    """
    Visit the PM home page

    :param user: user to send get request
    :type user: enmutils.lib.enm_user_2.User
    :param profile: Profile object
    :type profile: PM_06
    """
    log.logger.debug("Sending get request to PM home page")
    home_url = '/#pmiclistsubscription'
    try:
        user.get(home_url)
    except Exception:
        profile.add_error_as_exception(EnmApplicationError("Errors occurred while access PM landing page"))


def poll_pm(user, profile):
    """
    Poll the pm application

    :param user: user to send get request
    :type user: enmutils.lib.enm_user_2.User
    :param profile: Profile object
    :type profile: PM_06
    :return: Integer to indicate if there were errors experienced or not
    :rtype: int
    """
    log.logger.debug("Polling PM application")

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    urls = ["/pm-service/rest/subscription/",
            "/pm-service/rest/pmchartdata/bytesStored/1/60",
            "/pm-service/rest/pmchartdata/filesMissed/1/60"]

    errors_occurred = 0
    for url in urls:
        try:
            response = user.get(url, headers=headers)
            if not response.ok:
                raise Exception
        except Exception:
            errors_occurred += 1

    log.logger.debug("Polling PM application has completed")
    return errors_occurred


pm_06 = PM_06()
