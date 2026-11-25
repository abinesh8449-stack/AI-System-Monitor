import logging
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

class AIRecommendationEngine:
    """
    Intelligent AI Recommendation and Diagnostic Engine.
    Employs a multi-dimensional expert system with support for single and
    multi-resource root-cause analysis, and hooks for external LLM models.
    """

    def __init__(self):
        self._last_state = None
        self._last_recommendation = None

    def analyze(self, metrics, health_eval, top_processes=None, force=False):
        """
        Analyze current system performance and generate intelligent recommendations.
        Only generates a new diagnostic when system state changes or force is True.
        """
        overall_status = health_eval["overall_status"]
        cpu_status = health_eval["cpu_status"]
        ram_status = health_eval["ram_status"]
        disk_status = health_eval["disk_status"]
        net_status = health_eval["network_status"]

        # Current state signature
        current_state = f"{overall_status}:{cpu_status}:{ram_status}:{disk_status}:{net_status}"
        state_changed = (self._last_state != current_state)
        
        # Check if recovered
        is_recovery = False
        if self._last_state and ("CRITICAL" in self._last_state or "WARNING" in self._last_state) and overall_status == "HEALTHY":
            is_recovery = True

        if not state_changed and not force and self._last_recommendation is not None:
            return self._last_recommendation, False, is_recovery

        # Generate recommendation
        rec = self._generate_recommendation(
            metrics, health_eval, top_processes, is_recovery
        )

        self._last_state = current_state
        self._last_recommendation = rec

        return rec, True, is_recovery

    def _generate_recommendation(self, metrics, health_eval, top_processes, is_recovery):
        overall_status = health_eval["overall_status"]
        cpu_p = metrics.get("cpu_percent", 0.0)
        ram_p = metrics.get("ram_percent", 0.0)
        disk_p = metrics.get("disk_percent", 0.0)
        net_status = health_eval["network_status"]

        cpu_flag = health_eval["cpu_status"] in ("WARNING", "CRITICAL")
        ram_flag = health_eval["ram_status"] in ("WARNING", "CRITICAL")
        disk_flag = health_eval["disk_status"] in ("WARNING", "CRITICAL")
        net_flag = net_status in ("WARNING", "CRITICAL")

        # Top processes context
        top_cpu_proc = ""
        if top_processes and top_processes.get("top_cpu_processes"):
            p = top_processes["top_cpu_processes"][0]
            top_cpu_proc = f" (Top CPU consumer: '{p['name']}' PID {p['pid']} at {p['cpu_percent']}%)"

        top_ram_proc = ""
        if top_processes and top_processes.get("top_ram_processes"):
            p = top_processes["top_ram_processes"][0]
            top_ram_proc = f" (Top Memory consumer: '{p['name']}' PID {p['pid']} at {p['memory_percent']}%)"

        # Case 1: Recovery Event
        if is_recovery:
            return {
                "status": "HEALTHY",
                "severity": "NORMAL",
                "trigger_event": "System Stabilization & Recovery",
                "problem": "System resources have normalized within safe operational thresholds.",
                "possible_cause": "Intensive processes concluded, memory buffers were freed, or network connectivity stabilized.",
                "recommended_action": "Verify completed task status and maintain standard continuous monitoring.",
                "preventive_action": "Log peak load timestamps to establish baseline capacity trends.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Case 2: Multi-Resource High Utilization (Intelligent Correlation)
        if cpu_flag and ram_flag and disk_flag:
            return {
                "status": overall_status,
                "severity": overall_status,
                "trigger_event": "Full Spectrum System Saturation",
                "problem": f"CPU ({cpu_p}%), Memory ({ram_p}%), and Disk ({disk_p}%) are concurrently elevated under heavy stress.",
                "possible_cause": f"Severe resource contention, intensive computational batch pipeline, or system-wide deadlock with heavy virtual swap paging.{top_cpu_proc}{top_ram_proc}",
                "recommended_action": "Identify and pause non-essential background tasks immediately; check swap file thrashing and verify free disk space on root volume.",
                "preventive_action": "Consider vertical scaling (adding CPU cores and RAM), or partition workloads across distributed nodes.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        if cpu_flag and ram_flag:
            return {
                "status": overall_status,
                "severity": overall_status,
                "trigger_event": "CPU & Memory Resource Exhaustion",
                "problem": f"CPU utilization ({cpu_p}%) and Memory utilization ({ram_p}%) are both elevated simultaneously.",
                "possible_cause": f"Resource-intensive multi-threaded software or memory leak causing high garbage collection and CPU overhead.{top_cpu_proc}{top_ram_proc}",
                "recommended_action": "Inspect active process tree, isolate memory-leaking workers, and restart offending services.",
                "preventive_action": "Implement process memory quotas (cgroups/systemd limits) and profile long-running application memory usage.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        if cpu_flag and disk_flag:
            return {
                "status": overall_status,
                "severity": overall_status,
                "trigger_event": "High CPU & Disk I/O Bottleneck",
                "problem": f"CPU usage ({cpu_p}%) and Disk utilization ({disk_p}%) indicate high I/O wait state.",
                "possible_cause": "Heavy disk-bound database indexing, unindexed query scans, log accumulation, or swap thrashing.",
                "recommended_action": "Review disk I/O wait times, check active database queries, and inspect rotating log files for runaway growth.",
                "preventive_action": "Provision faster NVMe SSD storage, implement database query caching, and configure aggressive log rotation.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        if ram_flag and disk_flag:
            return {
                "status": overall_status,
                "severity": overall_status,
                "trigger_event": "Memory Pressure with Low Disk Capacity",
                "problem": f"Memory is constrained at {ram_p}% while Disk space is utilized at {disk_p}%.",
                "possible_cause": "System lacks sufficient swap space due to low disk capacity, risking severe OOM (Out-of-Memory) kernel kills.",
                "recommended_action": "Clear temporary files in /tmp or %TEMP%, truncate old logs, and restart memory-hungry daemons.",
                "preventive_action": "Expand primary disk volume and allocate dedicated swap partition to prevent out-of-memory crashes.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Case 3: Single Resource Spikes
        if cpu_flag:
            severity = health_eval["cpu_status"]
            return {
                "status": overall_status,
                "severity": severity,
                "trigger_event": f"Elevated CPU Activity ({cpu_p}%)",
                "problem": f"CPU utilization has reached {cpu_p}%, crossing the {severity.lower()} threshold.",
                "possible_cause": f"A computationally intensive process, infinite loop, or high background thread count is consuming cycles.{top_cpu_proc}",
                "recommended_action": "Review active processes, terminate or renice the resource-heavy process, and verify if workload is scheduled.",
                "preventive_action": "Benchmark CPU trends and consider setting affinity or CPU throttling on unmanaged background jobs.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        if ram_flag:
            severity = health_eval["ram_status"]
            return {
                "status": overall_status,
                "severity": severity,
                "trigger_event": f"Elevated Memory Usage ({ram_p}%)",
                "problem": f"RAM utilization has escalated to {ram_p}%, exceeding safe operating margins.",
                "possible_cause": f"Memory retention by unmanaged worker processes, large in-memory caches, or software memory leaks.{top_ram_proc}",
                "recommended_action": "Inspect active memory consumers, flush application caches, and restart suspect daemons.",
                "preventive_action": "Establish automated memory profiling and configure alerts before utilization exceeds 80%.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        if disk_flag:
            severity = health_eval["disk_status"]
            return {
                "status": overall_status,
                "severity": severity,
                "trigger_event": f"High Disk Capacity Utilization ({disk_p}%)",
                "problem": f"Storage capacity on primary volume is {disk_p}% full.",
                "possible_cause": "Rapid accumulation of application logs, database tablespaces, system crash dumps, or uncleaned temporary files.",
                "recommended_action": "Audit large files using disk usage tools, clean package caches, and archive legacy logs.",
                "preventive_action": "Configure logrotate with gzip compression and set automated storage expansion alerts.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        if net_flag:
            return {
                "status": overall_status,
                "severity": net_status,
                "trigger_event": "Network Connectivity Degradation",
                "problem": f"Network probe failed or encountered high latency ({metrics.get('network_status', 'Offline')}).",
                "possible_cause": "Local network interface down, gateway unreachable, DNS server timeout, or upstream link interruption.",
                "recommended_action": "Inspect physical cable / Wi-Fi adapter, verify default gateway ping, and validate DNS resolver configuration.",
                "preventive_action": "Configure redundant secondary DNS resolvers (e.g., 8.8.8.8 and 1.1.1.1) and monitor router uplink stability.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Case 4: Default Healthy State
        return {
            "status": "HEALTHY",
            "severity": "NORMAL",
            "trigger_event": "System Nominal",
            "problem": "All primary subsystems (CPU, RAM, Storage, Network) are functioning within nominal parameters.",
            "possible_cause": "Hardware capacity is adequately provisioned for the current workload profile.",
            "recommended_action": "No immediate intervention required. System is healthy and operating optimally.",
            "preventive_action": "Maintain scheduled patch management and automated continuous system monitoring.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Global singleton AI recommendation engine
recommendation_engine = AIRecommendationEngine()

if __name__ == '__main__':
    print("=" * 60)
    print("  AI RECOMMENDATION ENGINE MODULE SELF-TEST")
    print("=" * 60)
    mock_metrics = {"cpu_percent": 91.5, "ram_percent": 88.0, "disk_percent": 65.0, "network_status": "Connected"}
    mock_health = {
        "overall_status": "CRITICAL",
        "cpu_status": "CRITICAL",
        "ram_status": "CRITICAL",
        "disk_status": "HEALTHY",
        "network_status": "HEALTHY",
        "flagged_resources": ["CPU", "RAM"]
    }
    rec, changed, is_rec = recommendation_engine.analyze(mock_metrics, mock_health)
    print(f"  Trigger Event: {rec['trigger_event']}")
    print(f"  Problem      : {rec['problem']}")
    print(f"  Cause        : {rec['possible_cause']}")
    print(f"  Recommended  : {rec['recommended_action']}")
    print(f"  Preventive   : {rec['preventive_action']}")
    print("=" * 60)
    print("AIRecommendationEngine self-test completed successfully!")
