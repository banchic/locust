import random

from locust import HttpUser, task, User, LoadTestShape, events

from itertools import chain
from typing import TYPE_CHECKING, Any
from locust.clients import HttpSession
from locust.event import EventHook
from locust.exception import LocustError, StopUser
from locust.runners import MasterRunner, WorkerRunner, LocalRunner
from locust.stats import RequestStats, sort_stats, StatsEntry
from locust.user.task import (
    LOCUST_STATE_RUNNING,
    LOCUST_STATE_STOPPING,
    LOCUST_STATE_WAITING,
    DefaultTaskSet,
    TaskSet,
    get_tasks_from_base_classes,
)
from locust.user.wait_time import constant
from locust.util import deprecation

import logging
import time
import traceback
from typing import Callable, final

from gevent import GreenletExit, greenlet
from gevent.pool import Group
from urllib3 import PoolManager

logger = logging.getLogger(__name__)


def add_user(environment, msg, **kwargs):
    environment.runner.spawn_users(msg.data)


custom_stats = RequestStats()
custom_stats2 = RequestStats()


class HttpUser2(User):
    """
    Represents an HTTP "user" which is to be spawned and attack the system that is to be load tested.

    The behaviour of this user is defined by its tasks. Tasks can be declared either directly on the
    class by using the :py:func:`@task decorator <locust.task>` on methods, or by setting
    the :py:attr:`tasks attribute <locust.User.tasks>`.

    This class creates a *client* attribute on instantiation which is an HTTP client with support
    for keeping a user session between requests.
    """

    abstract: bool = True
    """If abstract is True, the class is meant to be subclassed, and users will not choose this locust during a test"""

    pool_manager: PoolManager = None
    """Connection pool manager to use. If not given, a new manager is created per single user."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.host is None:
            raise LocustError(
                "You must specify the base host. Either in the host attribute in the User class, or on the command line using the --host option."
            )

        self.client = HttpSession(
            base_url=self.host,
            request_event=self.environment.events.request,
            user=self,
            pool_manager=self.pool_manager,
        )
        """
        Instance of HttpSession that is created upon instantiation of Locust.
        The client supports cookies, and therefore keeps the session between HTTP requests.
        """
        self.client.trust_env = False


# print(1)

my_event = EventHook()

my_event_two = EventHook()
global MASTER

def on_my_event(environment, request, **kw):
    if not hasattr(environment.runner.environment, 'custom_stats'):
        print(1111111111111111)
        environment.runner.environment.custom_stats = custom_stats
    environment.runner.environment.custom_stats.log_request("reqyest_type_test", "reqyest_type_test", 0, 0)


my_event.add_listener(on_my_event)

def on_my_event_two(environment, request, **kw):
    if not hasattr(environment.runner.environment, 'custom_stats_two'):
        print(222222222)
        environment.runner.environment.custom_stats_two = custom_stats2
    environment.runner.environment.custom_stats_two.log_request("reqyest_type_test", "reqyest_type_test", 0, 0)


my_event_two.add_listener(on_my_event_two)

class HelloWorldUser(HttpUser2):
    host = "http://0.0.0.0:8089/"

    @task(1)
    def hello_world1(self):
        request = {
            "request_type": "1",
            "name":"request_name",
            "start_time": time.time()
        }
        my_event.fire(environment=self.environment, request=request)
        self.client.get("/total_test")
        response = {
            "request_type": "2",
            "name":"response_name",
            "start_time": time.time()
        }

        my_event_two.fire(environment=self.environment, request=response)
        self.stop()

    # @task(2)
    # def hello_world(self):
    #     request = {
    #         "request_type": "1",
    #         "request_timestamp": "response_time"
    #     }
    #     my_event.fire(environment=self.environment, request=request)
    #     self.client.get("/total_tps")
    #     print(2)
    #     self.stop()


class RpsShape(LoadTestShape):

    def tick(self):
        if isinstance(self.runner, MasterRunner):
            worker_nodes = list(self.runner.clients.values())
        else:
            worker_nodes = [self.runner._local_worker_node]

        _users_dispatcher = self.runner.environment.dispatcher_class(
            worker_nodes=worker_nodes, user_classes=self.runner.environment.user_classes
        )
        _users_dispatcher.new_dispatch(
            target_user_count=self.runner.environment.parsed_options.rps,
            spawn_rate=self.runner.environment.parsed_options.rps,
            user_classes=None
        )

        for dispathced_users in _users_dispatcher:
            for worker_node_id, worker_user_classes_count in dispathced_users.items():
                self.runner.send_message("add_user", worker_user_classes_count, worker_node_id)

        return (0, 1)


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        print("MasterRunner", environment.runner)
        global MASTER
        MASTER = environment.runner.environment
        environment.runner.environment.custom_stats_two = custom_stats2
        environment.runner.environment.custom_stats = custom_stats
    elif isinstance(environment.runner, (WorkerRunner, LocalRunner)):
        print("Runner", environment.runner)
        environment.runner.register_message("add_user", add_user)


@events.report_to_master.add_listener
def report(client_id, data, **kwargs):
    data["custom_stats"] = custom_stats.serialize_stats()
    data["custom_stats_total"] = custom_stats.total.get_stripped_report()
    data["custom_stats_two"] = custom_stats2.serialize_stats()
    data["custom_stats_two_total"] = custom_stats2.total.get_stripped_report()

@events.worker_report.add_listener
def on_worker_report(client_id, data):
    print(data)
    """
    This event is triggered on the master instance when a new stats report arrives
    from a worker. Here we just add the content-length to the master's aggregated
    stats dict.
    """
    global MASTER
    for stats_data in data["custom_stats"]:
        entry = StatsEntry.unserialize(stats_data)
        request_key = (entry.name, entry.method)
        if request_key not in MASTER.custom_stats.entries:
            MASTER.custom_stats.entries[request_key] = StatsEntry(MASTER.custom_stats, entry.name, entry.method, use_response_times_cache=True)
        MASTER.custom_stats.entries[request_key].extend(entry)


    MASTER.custom_stats.total.extend(StatsEntry.unserialize(data["custom_stats_total"]))

    for stats_data in data["custom_stats_two"]:
        entry = StatsEntry.unserialize(stats_data)
        request_key = (entry.name, entry.method)
        if request_key not in MASTER.custom_stats_two.entries:
            MASTER.custom_stats_two.entries[request_key] = StatsEntry(MASTER.custom_stats_two, entry.name, entry.method, use_response_times_cache=True)
        MASTER.custom_stats_two.entries[request_key].extend(entry)
    MASTER.custom_stats_two.total.extend(StatsEntry.unserialize(data["custom_stats_two_total"]))



@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--rps", type=int, default=0, help="Stable RPS")
