"""Main Textual Application for Watchdog."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Input, TabbedContent, TabPane

from watchdog.core.docker_manager import DockerManager
from watchdog.core.proxy_detector import ProxyDetector
from watchdog.core.system_monitor import SystemMonitor
from watchdog.models import ContainerInfo
from watchdog.ui.widgets.confirm_modal import ConfirmModal
from watchdog.ui.widgets.container_table import ContainerTableWidget
from watchdog.ui.widgets.header_stats import HeaderStatsWidget
from watchdog.ui.widgets.help_modal import HelpModal
from watchdog.ui.widgets.inspect_modal import InspectModal
from watchdog.ui.widgets.log_modal import LogModal
from watchdog.ui.widgets.service_table import ServiceTableWidget


class WatchdogApp(App):
    """Modern Docker & Service Status Monitor Dashboard."""

    TITLE = "Watchdog - Docker & Service Monitor"
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "restart_container", "Restart", show=True),
        Binding("s", "toggle_start_stop", "Start/Stop", show=True),
        Binding("p", "toggle_pause", "Pause", show=True),
        Binding("l", "view_logs", "Logs", show=True),
        Binding("i", "inspect_container", "Inspect", show=True),
        Binding("x", "remove_container", "Remove", show=True),
        Binding("f", "focus_search", "Filter", show=True),
        Binding("slash", "focus_search", "Filter", show=False),
        Binding("1", "tab_containers", "Containers", show=True),
        Binding("2", "tab_services", "Proxy & Ports", show=True),
        Binding("question_mark", "show_help", "Help", show=True),
    ]

    def __init__(
        self,
        docker_host: str | None = None,
        poll_interval: float = 2.0,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.docker_manager = DockerManager(base_url=docker_host)
        self.system_monitor = SystemMonitor()
        self.poll_interval = poll_interval
        self._is_refreshing: bool = False

    def compose(self) -> ComposeResult:
        yield HeaderStatsWidget(id="header-container")

        with TabbedContent(id="main-tabs", initial="tab-containers"):
            with TabPane("🐳 Containers & Stats (1)", id="tab-containers"):
                yield ContainerTableWidget(id="container-table-widget")

            with TabPane("🌐 Reverse Proxy & Ports (2)", id="tab-services"):
                yield ServiceTableWidget(id="service-table-widget")

        yield Footer(id="action-footer")

    def on_mount(self) -> None:
        """Called when App finishes loading."""
        # Initial refresh
        self.run_worker(self._update_all_data, exclusive=True, thread=True)

        # Periodic refresh loop
        self.set_interval(self.poll_interval, self._trigger_refresh)

    def _trigger_refresh(self) -> None:
        if not self._is_refreshing:
            self.run_worker(self._update_all_data, exclusive=True, thread=True)

    def _update_all_data(self) -> None:
        """Background worker thread fetching docker & host metrics."""
        self._is_refreshing = True
        try:
            # 1. Host Stats
            sys_stats = self.system_monitor.get_stats()

            # 2. Docker info & containers
            docker_info = self.docker_manager.get_system_summary()
            containers = self.docker_manager.list_containers(all_containers=True)

            # 3. Update container stats for running containers
            if self.docker_manager.is_connected:
                for c in containers:
                    if c.is_running:
                        st = self.docker_manager.update_container_stats(c.id)
                        if st:
                            c.stats = st

            # 4. Detect reverse proxy routes
            routes = ProxyDetector.detect_routes(containers)

            # Schedule UI updates back onto main event loop
            self.call_from_thread(self._apply_data, sys_stats, docker_info, containers, routes)
        except Exception as e:
            self.call_from_thread(self.notify, f"Error updating metrics: {e!s}", severity="error")
        finally:
            self._is_refreshing = False

    def _apply_data(self, sys_stats, docker_info, containers, routes) -> None:
        """Update Textual widgets with fresh data on the main thread."""
        try:
            header = self.query_one("#header-container", HeaderStatsWidget)
            header.update_stats(sys_stats, docker_info)

            c_widget = self.query_one("#container-table-widget", ContainerTableWidget)
            c_widget.set_containers(containers)

            s_widget = self.query_one("#service-table-widget", ServiceTableWidget)
            s_widget.set_routes(routes)
        except Exception:
            pass

    # Keyboard Action Handlers
    def action_focus_search(self) -> None:
        """Focus the search bar on the active tab."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-containers":
            try:
                inp = self.query_one("#container-search-input", Input)
                inp.focus()
            except Exception:
                pass
        elif tabs.active == "tab-services":
            try:
                inp = self.query_one("#service-search-input", Input)
                inp.focus()
            except Exception:
                pass

    def action_tab_containers(self) -> None:
        tabs = self.query_one("#main-tabs", TabbedContent)
        tabs.active = "tab-containers"

    def action_tab_services(self) -> None:
        tabs = self.query_one("#main-tabs", TabbedContent)
        tabs.active = "tab-services"

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def _get_active_container(self) -> ContainerInfo | None:
        c_widget = self.query_one("#container-table-widget", ContainerTableWidget)
        selected = c_widget.get_selected_container()
        if not selected:
            self.notify("No container selected. Highlight a container first.", severity="warning")
            return None
        return selected

    def action_restart_container(self) -> None:
        """Restart selected container asynchronously."""
        c = self._get_active_container()
        if not c:
            return

        self.notify(f"Restarting '{c.name}'...", severity="information", timeout=3)

        def _do_restart():
            success, msg = self.docker_manager.restart_container(c.id)
            if success:
                self.call_from_thread(self.notify, msg, severity="information")
                self.call_from_thread(self._trigger_refresh)
            else:
                self.call_from_thread(self.notify, msg, severity="error")

        self.run_worker(_do_restart, thread=True)

    def action_toggle_start_stop(self) -> None:
        """Start container if stopped, or stop with confirm if running."""
        c = self._get_active_container()
        if not c:
            return

        if not c.is_running:
            # Start directly
            self.notify(f"Starting '{c.name}'...", severity="information")

            def _do_start():
                success, msg = self.docker_manager.start_container(c.id)
                if success:
                    self.call_from_thread(self.notify, msg, severity="information")
                    self.call_from_thread(self._trigger_refresh)
                else:
                    self.call_from_thread(self.notify, msg, severity="error")

            self.run_worker(_do_start, thread=True)
        else:
            # Confirm before stopping
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.notify(f"Stopping '{c.name}'...", severity="information")

                    def _do_stop():
                        success, msg = self.docker_manager.stop_container(c.id)
                        if success:
                            self.call_from_thread(self.notify, msg, severity="information")
                            self.call_from_thread(self._trigger_refresh)
                        else:
                            self.call_from_thread(self.notify, msg, severity="error")

                    self.run_worker(_do_stop, thread=True)

            self.push_screen(
                ConfirmModal(
                    title="🛑 Stop Container",
                    message=f"Are you sure you want to stop container '{c.name}' ({c.short_id})?",
                    action_label="Stop Container",
                    is_danger=True
                ),
                on_confirm
            )

    def action_toggle_pause(self) -> None:
        """Toggle pause / unpause state."""
        c = self._get_active_container()
        if not c:
            return

        def _do_pause():
            success, msg = self.docker_manager.pause_container(c.id)
            if success:
                self.call_from_thread(self.notify, msg, severity="information")
                self.call_from_thread(self._trigger_refresh)
            else:
                self.call_from_thread(self.notify, msg, severity="error")

        self.run_worker(_do_pause, thread=True)

    def action_view_logs(self) -> None:
        """Open Log viewer modal."""
        c = self._get_active_container()
        if not c:
            return
        self.push_screen(LogModal(self.docker_manager, c))

    def action_inspect_container(self) -> None:
        """Open Inspect modal."""
        c = self._get_active_container()
        if not c:
            return
        self.push_screen(InspectModal(c))

    def action_remove_container(self) -> None:
        """Remove container with confirmation dialog."""
        c = self._get_active_container()
        if not c:
            return

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self.notify(f"Removing '{c.name}'...", severity="information")

                def _do_remove():
                    success, msg = self.docker_manager.remove_container(c.id, force=True)
                    if success:
                        self.call_from_thread(self.notify, msg, severity="information")
                        self.call_from_thread(self._trigger_refresh)
                    else:
                        self.call_from_thread(self.notify, msg, severity="error")

                self.run_worker(_do_remove, thread=True)

        self.push_screen(
            ConfirmModal(
                title="⚠️ Delete Container",
                message=f"Permanently remove container '{c.name}' ({c.short_id})? This cannot be undone.",
                action_label="Delete",
                is_danger=True
            ),
            on_confirm
        )
