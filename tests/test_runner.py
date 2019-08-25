import pytest
from enum import Enum

class PytestExitCodes(Enum):
    ALL_PASSING    = 0
    SOME_FAILURES  = 1
    USER_INTERRUPT = 2
    INTERNAL_ERROR = 3
    USAGE_ERROR    = 4
    NO_TESTS_COLL  = 5


def test_runner(directory):
    result_code = pytest.main(args=['-svx', directory])
    result = PytestExitCodes(result_code)
    return result

if __name__ == "__main__":
    pass
