"""Test full WatchdogApp Textual application lifecycle."""

import pytest

from watchdog.ui.app import WatchdogApp
from watchdog.ui.widgets.container_table import ContainerTableWidget
from watchdog.ui.widgets.header_stats import HeaderStatsWidget
from watchdog.ui.widgets.service_table import ServiceTableWidget


@pytest.mark.asyncio
async def test_watchdog_app_lifecycle():
    app = WatchdogApp(poll_interval=10.0)
    async with app.run_test() as pilot:
        # Check widgets existence
        header = app.query_one(HeaderStatsWidget)
        assert header is not None

        c_table = app.query_one(ContainerTableWidget)
        assert c_table is not None

        s_table = app.query_one(ServiceTableWidget)
        assert s_table is not None

        # Test switching tabs
        app.action_tab_services()
        await pilot.pause(0.1)

        app.action_tab_containers()
        await pilot.pause(0.1)
