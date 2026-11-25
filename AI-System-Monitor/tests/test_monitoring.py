import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitoring.system_monitor import (
    get_cpu_metrics, get_ram_metrics, get_disk_metrics,
    get_top_processes, get_system_info
)
from monitoring.network_monitor import network_monitor

class TestSystemMonitoring(unittest.TestCase):
    """Test actual psutil metric collectors."""

    def test_cpu_metrics(self):
        cpu = get_cpu_metrics()
        self.assertIn("cpu_percent", cpu)
        self.assertIsInstance(cpu["cpu_percent"], float)
        self.assertGreaterEqual(cpu["cpu_percent"], 0.0)
        self.assertLessEqual(cpu["cpu_percent"], 100.0)
        self.assertGreaterEqual(cpu["logical_cores"], 1)
        self.assertGreaterEqual(cpu["physical_cores"], 1)

    def test_ram_metrics(self):
        ram = get_ram_metrics()
        self.assertIn("ram_percent", ram)
        self.assertIsInstance(ram["ram_percent"], float)
        self.assertGreaterEqual(ram["ram_percent"], 0.0)
        self.assertLessEqual(ram["ram_percent"], 100.0)
        self.assertGreater(ram["total_ram_gb"], 0.0)
        self.assertGreaterEqual(ram["used_ram_gb"], 0.0)

    def test_disk_metrics(self):
        disk = get_disk_metrics()
        self.assertIn("disk_percent", disk)
        self.assertIsInstance(disk["disk_percent"], float)
        self.assertGreaterEqual(disk["disk_percent"], 0.0)
        self.assertLessEqual(disk["disk_percent"], 100.0)
        self.assertGreater(disk["total_disk_gb"], 0.0)

    def test_top_processes(self):
        procs = get_top_processes(limit=3)
        self.assertIn("top_cpu_processes", procs)
        self.assertIn("top_ram_processes", procs)
        if procs["top_cpu_processes"]:
            p = procs["top_cpu_processes"][0]
            self.assertIn("pid", p)
            self.assertIn("name", p)

    def test_network_metrics(self):
        rates = network_monitor.get_transfer_rates()
        self.assertIn("upload_speed_kb", rates)
        self.assertIn("download_speed_kb", rates)
        self.assertGreaterEqual(rates["upload_speed_kb"], 0.0)
        self.assertGreaterEqual(rates["download_speed_kb"], 0.0)

        connected, status_text = network_monitor.check_connectivity()
        self.assertIsInstance(connected, bool)
        self.assertIsInstance(status_text, str)

        iface_data = network_monitor.get_interface_details()
        self.assertIn("primary_ip", iface_data)
        self.assertIn("interfaces", iface_data)

    def test_system_info(self):
        info = get_system_info()
        self.assertIn("os_name", info)
        self.assertIn("hostname", info)
        self.assertIn("python_version", info)
        self.assertIn("uptime", info)

if __name__ == '__main__':
    unittest.main()
