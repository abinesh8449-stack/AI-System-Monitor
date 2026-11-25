import sys
from pathlib import Path

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import importlib

def _resolve_config():
    try:
        return importlib.import_module("config").Config
    except Exception:
        class _FallbackConfig:
            CPU_WARNING = 50.0
            CPU_CRITICAL = 80.0
            RAM_WARNING = 50.0
            RAM_CRITICAL = 80.0
            DISK_WARNING = 70.0
            DISK_CRITICAL = 85.0
        return _FallbackConfig

Config = _resolve_config()

class HealthChecker:
    """Centralized rule-based health classification engine based on Config thresholds."""

    @staticmethod
    def classify_metric(value, warning_threshold, critical_threshold):
        """Classify a single numerical metric into HEALTHY, WARNING, or CRITICAL."""
        if value >= critical_threshold:
            return "CRITICAL"
        elif value >= warning_threshold:
            return "WARNING"
        return "HEALTHY"

    @classmethod
    def evaluate_health(cls, cpu_percent, ram_percent, disk_percent, network_connected, network_status_text):
        """
        Evaluate full system health state.
        Returns:
            dict containing statuses of individual components, overall status, and summary statistics.
        """
        cpu_status = cls.classify_metric(cpu_percent, Config.CPU_WARNING, Config.CPU_CRITICAL)
        ram_status = cls.classify_metric(ram_percent, Config.RAM_WARNING, Config.RAM_CRITICAL)
        disk_status = cls.classify_metric(disk_percent, Config.DISK_WARNING, Config.DISK_CRITICAL)
        
        # Network classification
        if network_connected and "Connected" in network_status_text:
            network_status = "HEALTHY"
        elif "Latency" in network_status_text:
            network_status = "WARNING"
        else:
            network_status = "CRITICAL"

        component_statuses = {
            "CPU": cpu_status,
            "RAM": ram_status,
            "Disk": disk_status,
            "Network": network_status
        }

        # Calculate counts
        healthy_count = sum(1 for s in component_statuses.values() if s == "HEALTHY")
        warning_count = sum(1 for s in component_statuses.values() if s == "WARNING")
        critical_count = sum(1 for s in component_statuses.values() if s == "CRITICAL")

        # Determine overall condition
        if critical_count > 0:
            overall_status = "CRITICAL"
        elif warning_count > 0:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"

        flagged_resources = [res for res, st in component_statuses.items() if st in ("WARNING", "CRITICAL")]

        return {
            "overall_status": overall_status,
            "cpu_status": cpu_status,
            "ram_status": ram_status,
            "disk_status": disk_status,
            "network_status": network_status,
            "counts": {
                "healthy": healthy_count,
                "warning": warning_count,
                "critical": critical_count,
                "total": len(component_statuses)
            },
            "flagged_resources": flagged_resources
        }


if __name__ == '__main__':
    print("=" * 60)
    print("  HEALTH CHECKER MODULE SELF-TEST")
    print("=" * 60)
    print(f"  CPU Thresholds  : Warning >= {Config.CPU_WARNING}%, Critical >= {Config.CPU_CRITICAL}%")
    print(f"  RAM Thresholds  : Warning >= {Config.RAM_WARNING}%, Critical >= {Config.RAM_CRITICAL}%")
    print(f"  Disk Thresholds : Warning >= {Config.DISK_WARNING}%, Critical >= {Config.DISK_CRITICAL}%")
    print("-" * 60)
    test_eval = HealthChecker.evaluate_health(
        cpu_percent=45.0, ram_percent=75.0, disk_percent=55.0,
        network_connected=True, network_status_text="Connected"
    )
    print("Sample Evaluation (CPU 45%, RAM 75%, Disk 55%):")
    print(f"  Overall Status   : {test_eval['overall_status']}")
    print(f"  CPU Status       : {test_eval['cpu_status']}")
    print(f"  RAM Status       : {test_eval['ram_status']}")
    print(f"  Disk Status      : {test_eval['disk_status']}")
    print(f"  Network Status   : {test_eval['network_status']}")
    print(f"  Flagged Resources: {test_eval['flagged_resources']}")
    print("=" * 60)
    print("HealthChecker self-test completed successfully!")
