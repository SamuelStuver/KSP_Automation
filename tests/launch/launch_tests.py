import pytest
import time
from kRPC_Automation.tests.common_fixtures import krpc_connect, setup_active_vessel
from kRPC_Automation.tests.common_support import Throttle, get_throttle, set_autopilot, crew_list
from kRPC_Automation.tests.launch.launch_support import simple_launch

from kRPC_Automation.log_setup import logger

g_accel = 9.81

def test_simple_launch(setup_active_vessel, krpc_connect):
    vessel = setup_active_vessel
    conn = krpc_connect
    success = simple_launch(conn, vessel)
    assert success
