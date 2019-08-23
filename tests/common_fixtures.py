import pytest
import krpc
from kRPC_Automation.tests.common_support import establish_connection
from kRPC_Automation.log_setup import logger

@pytest.fixture(scope="module")
def krpc_connect():

    def _establish_connection(name="Connection",address='192.168.0.11',rpc_port=5000,stream_port=5001):
        logger.debug(f"Attempting to connect to {address}:{rpc_port}")
        try:
            conn = krpc.connect(name=name, address=address, rpc_port=rpc_port, stream_port=stream_port)
        except Exception as ex:
            logger.error(f"Unable to connect to {address}:{rpc_port}")
            logger.error(f"Reason: {ex}")
            return None
        logger.debug(f"Successfully connected to {address}:{rpc_port}")
        return conn

    conn = _establish_connection()
    if conn is not None:
        yield conn
    else:
        assert False, f"Failed to establish connection"
