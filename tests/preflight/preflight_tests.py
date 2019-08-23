import pytest
import time
from kRPC_Automation.tests.common_fixtures import krpc_connect
from kRPC_Automation.log_setup import logger


def test_connection(krpc_connect):
    conn = krpc_connect()
    assert conn is not None
