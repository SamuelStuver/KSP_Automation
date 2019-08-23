import pytest
from example_support import establish_connection


@pytest.fixture(scope="module")
def krpc_connect():
    conn = establish_connection(
                                name="Connection",
                                address='192.168.0.11',
                                rpc_port=5000,
                                stream_port=5001
                                )
    assert conn is not None
    yield conn
