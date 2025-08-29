# conftest.py
import os
import pytest

def pytest_addoption(parser):
    parser.addoption("--port", help="Serial port (e.g. COM5 or /dev/ttyACM0)",
                     default=os.environ.get("TACTILE_PORT", ""))
    parser.addoption("--baud", help="Baud rate", type=int, default=int(os.environ.get("TACTILE_BAUD", "9600")))
    parser.addoption("--bank", help="audio bank (HUMAN or GENERA~1)",
                     default=os.environ.get("TACTILE_BANK", "GENERA~1"))
    parser.addoption("--key", help="key folder (e.g. A, J, SHIFT)", default=os.environ.get("TACTILE_KEY", "J"))

@pytest.fixture(scope="session")
def port(pytestconfig):
    p = pytestconfig.getoption("port")
    if not p:
        pytest.skip("No --port specified and TACTILE_PORT not set")
    return p

@pytest.fixture(scope="session")
def baud(pytestconfig):
    return pytestconfig.getoption("baud")

@pytest.fixture(scope="session")
def bank(pytestconfig):
    return pytestconfig.getoption("bank")

@pytest.fixture(scope="session")
def key(pytestconfig):
    return pytestconfig.getoption("key")
