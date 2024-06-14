from locust import HttpUser, task, User, LoadTestShape, events

from itertools import chain
from typing import TYPE_CHECKING, Any
from locust.clients import HttpSession
from locust.event import EventHook
from locust.exception import LocustError, StopUser
from locust.runners import MasterRunner, WorkerRunner, LocalRunner
from locust.stats import RequestStats, sort_stats
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
def on_my_event(environment, request, **kw):
    if not hasattr(environment.runner.environment, 'custom_stats'):
        print(1111111111111111)
        environment.runner.environment.custom_stats = RequestStats()
    environment.runner.environment.custom_stats.log_request("reqyest_type_test", "reqyest_type_test", 0, 0)


my_event.add_listener(on_my_event)


class HelloWorldUser(HttpUser2):
    host = "http://0.0.0.0:8089/"
    @task(1)
    def hello_world1(self):
        request = {
            "request_type": "1",
            "request_timestamp": "response_time"
        }
        my_event.fire(environment=self.environment, request=request)
        self.client.get("/total_test")
        print(1)
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
            worker_nodes = list(self.runner.clients.value())
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

        return (0,1)




@events.init.add_listener
def on_locust_init(environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        print("MasterRunner", environment.runner)
    elif isinstance(environment.runner, (WorkerRunner, LocalRunner)):
        print("Runner", environment.runner)
        environment.runner.register_message("add_user", add_user)


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--rps", type=int, default=0, help="Stable RPS")



