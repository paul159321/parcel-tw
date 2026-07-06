import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="run tests that call external carrier services",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        return

    skip_live = pytest.mark.skip(reason="need --run-live option to run live tests")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
