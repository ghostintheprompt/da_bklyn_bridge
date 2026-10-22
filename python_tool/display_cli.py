import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from vendors import resolve_vendor

class SentinelDashboard:
    def __init__(self, db, capturer):
        self.db = db
        self.capturer = capturer
        self.console = Console()

    def make_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        layout["left"].split_column(
            Layout(name="aps"),
            Layout(name="probes")
        )
        return layout

    def generate_ap_table(self):
        table = Table(title="Nearby Access Points", expand=True)
        table.add_column("BSSID", style="cyan")
        table.add_column("SSID", style="magenta")
        table.add_column("Ch", style="green")
        table.add_column("RSSI", style="yellow")
        table.add_column("Security", style="red")
        
        aps = self.db.get_recent_aps(limit=10)
        for ap in aps:
            table.add_row(ap[0], ap[1], str(ap[2]), str(ap[3]), ap[4])
        return table

    def generate_probe_table(self):
        table = Table(title="Recent Probe Requests", expand=True)
        table.add_column("MAC", style="cyan")
        table.add_column("Vendor", style="dim")
        table.add_column("SSID", style="magenta")
        table.add_column("RSSI", style="yellow")
        table.add_column("Time", style="dim")
        
        probes = self.db.get_recent_probes(limit=10)
        for p in probes:
            vendor = resolve_vendor(p[1])
            table.add_row(p[1], vendor, p[2], str(p[3]), str(p[-1]))
        return table

    def generate_alert_panel(self):
        alerts = self.db.get_recent_alerts(limit=5)
        text = ""
        for a in alerts:
            color = "red" if a[3] == "critical" else "yellow"
            text += f"[{color}][{a[1]}][/] {a[2]} ({a[4]})\n"
        return Panel(text or "No active alerts", title="Security Alerts", border_style="bold red")

    def run(self):
        layout = self.make_layout()
        with Live(layout, refresh_per_second=1):
            while True:
                layout["header"].update(Panel(f"Da Bklyn Bridge :: Interface: {self.capturer.interface} :: Channel: {self.capturer.current_channel}", style="bold blue"))
                layout["aps"].update(self.generate_ap_table())
                layout["probes"].update(self.generate_probe_table())
                layout["right"].update(self.generate_alert_panel())
                layout["footer"].update(Panel("Press Ctrl+C to exit sentinel", style="dim"))
                time.sleep(1)
