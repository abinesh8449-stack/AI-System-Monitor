import os
import sys
from pathlib import Path
import platform
import psutil  # type: ignore
from datetime import datetime, timedelta

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Warmup psutil cpu_percent
psutil.cpu_percent(interval=None)

def bytes_to_gb(bytes_value):
    """Convert bytes to Gigabytes with 2 decimal precision."""
    if not bytes_value:
        return 0.0
    return round(bytes_value / (1024 ** 3), 2)

def bytes_to_mb(bytes_value):
    """Convert bytes to Megabytes with 2 decimal precision."""
    if not bytes_value:
        return 0.0
    return round(bytes_value / (1024 ** 2), 2)

def get_cpu_metrics():
    """Retrieve actual CPU performance metrics using psutil."""
    cpu_percent = psutil.cpu_percent(interval=None)
    per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
    physical_cores = psutil.cpu_count(logical=False) or 1
    logical_cores = psutil.cpu_count(logical=True) or 1
    
    freq_data = psutil.cpu_freq()
    current_freq = round(freq_data.current, 1) if freq_data else 0.0
    min_freq = round(freq_data.min, 1) if freq_data and freq_data.min else 0.0
    max_freq = round(freq_data.max, 1) if freq_data and freq_data.max else 0.0
    
    return {
        "cpu_percent": round(cpu_percent, 1),
        "per_cpu_percent": per_cpu_percent,
        "physical_cores": physical_cores,
        "logical_cores": logical_cores,
        "frequency_current_mhz": current_freq,
        "frequency_min_mhz": min_freq,
        "frequency_max_mhz": max_freq
    }

def get_ram_metrics():
    """Retrieve actual RAM utilization and memory buffers."""
    vmem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "ram_percent": round(vmem.percent, 1),
        "total_ram_gb": bytes_to_gb(vmem.total),
        "used_ram_gb": bytes_to_gb(vmem.used),
        "available_ram_gb": bytes_to_gb(vmem.available),
        "free_ram_gb": bytes_to_gb(vmem.free),
        "swap_percent": round(swap.percent, 1),
        "swap_total_gb": bytes_to_gb(swap.total),
        "swap_used_gb": bytes_to_gb(swap.used)
    }

def get_disk_metrics():
    """Retrieve primary storage and partition metrics."""
    # Determine primary root mount point
    if os.name == 'nt':
        root_path = os.environ.get('SystemDrive', 'C:') + '\\'
    else:
        root_path = '/'
        
    disk = psutil.disk_usage(root_path)
    
    partitions = []
    try:
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                partitions.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total_gb": bytes_to_gb(usage.total),
                    "used_gb": bytes_to_gb(usage.used),
                    "free_gb": bytes_to_gb(usage.free),
                    "percent": round(usage.percent, 1)
                })
            except (PermissionError, FileNotFoundError):
                continue
    except Exception:
        pass
        
    return {
        "disk_percent": round(disk.percent, 1),
        "total_disk_gb": bytes_to_gb(disk.total),
        "used_disk_gb": bytes_to_gb(disk.used),
        "free_disk_gb": bytes_to_gb(disk.free),
        "mount_point": root_path,
        "partitions": partitions
    }

PSEUDO_PROCESS_NAMES = {
    "system idle process", "system", "registry", "memcompression", "idle", "unknown"
}

def get_top_processes(limit=5, excluded_pids=None, excluded_names=None):
    """Fetch top real user/system processes sorted by CPU and memory consumption."""
    excluded_p = excluded_pids or set()
    excluded_n = {n.lower() for n in (excluded_names or set())}
    logical_cores = psutil.cpu_count(logical=True) or 1
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = proc.info
            pid = info['pid']
            if pid is None or pid <= 4 or pid in excluded_p:
                continue
            name = (info['name'] or "").strip()
            name_lower = name.lower()
            if not name or name_lower in PSEUDO_PROCESS_NAMES or name_lower in excluded_n:
                continue

            raw_cpu = info['cpu_percent'] or 0.0
            if raw_cpu > 100.0:
                raw_cpu = raw_cpu / logical_cores
            cpu_val = min(100.0, round(raw_cpu, 1))
            mem_val = round(info['memory_percent'] or 0.0, 1)

            processes.append({
                "pid": pid,
                "name": name,
                "cpu_percent": cpu_val,
                "memory_percent": mem_val,
                "status": info['status']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort and deduplicate by process name so killing a process removes it completely from display
    cpu_sorted = sorted(processes, key=lambda p: (p['cpu_percent'], p['memory_percent']), reverse=True)
    top_cpu = []
    seen_cpu_names = set()
    for p in cpu_sorted:
        lname = str(p['name']).lower()
        if lname not in seen_cpu_names:
            seen_cpu_names.add(lname)
            top_cpu.append(p)
            if len(top_cpu) >= limit:
                break

    ram_sorted = sorted(processes, key=lambda p: (p['memory_percent'], p['cpu_percent']), reverse=True)
    top_ram = []
    seen_ram_names = set()
    for p in ram_sorted:
        lname = str(p['name']).lower()
        if lname not in seen_ram_names:
            seen_ram_names.add(lname)
            top_ram.append(p)
            if len(top_ram) >= limit:
                break

    return {
        "top_cpu_processes": top_cpu,
        "top_ram_processes": top_ram
    }

def get_system_info():
    """Retrieve detailed static and runtime host information."""
    boot_timestamp = psutil.boot_time()
    boot_datetime = datetime.fromtimestamp(boot_timestamp)
    uptime_seconds = int((datetime.now() - boot_datetime).total_seconds())
    uptime_str = str(timedelta(seconds=uptime_seconds))
    
    cpu_info = get_cpu_metrics()
    ram_info = get_ram_metrics()
    disk_info = get_disk_metrics()
    
    return {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "hostname": platform.node(),
        "machine": platform.machine(),
        "processor": platform.processor() or platform.machine(),
        "cpu_physical_cores": cpu_info["physical_cores"],
        "cpu_logical_cores": cpu_info["logical_cores"],
        "cpu_frequency_current_mhz": cpu_info["frequency_current_mhz"],
        "total_ram_gb": ram_info["total_ram_gb"],
        "total_disk_gb": disk_info["total_disk_gb"],
        "python_version": sys.version.split()[0],
        "boot_time": boot_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds
    }

def get_all_system_metrics():
    """Consolidate current CPU, RAM, and Disk metrics into a single dictionary."""
    cpu = get_cpu_metrics()
    ram = get_ram_metrics()
    disk = get_disk_metrics()
    
    return {
        "cpu_percent": cpu["cpu_percent"],
        "cpu_metrics": cpu,
        "ram_percent": ram["ram_percent"],
        "ram_metrics": ram,
        "disk_percent": disk["disk_percent"],
        "disk_metrics": disk,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == '__main__':
    print("=" * 60)
    print("  SYSTEM MONITOR MODULE SELF-TEST")
    print("=" * 60)
    sys_info = get_system_info()
    cpu = get_cpu_metrics()
    ram = get_ram_metrics()
    disk = get_disk_metrics()
    procs = get_top_processes(limit=3)
    print(f"  OS / Host   : {sys_info['os_name']} {sys_info['os_release']} ({sys_info['hostname']})")
    print(f"  Uptime      : {sys_info['uptime']}")
    print(f"  CPU Cores   : {cpu['physical_cores']} Phys / {cpu['logical_cores']} Log @ {cpu['cpu_percent']}%")
    print(f"  RAM Usage   : {ram['used_ram_gb']} / {ram['total_ram_gb']} GB ({ram['ram_percent']}%)")
    print(f"  Disk Usage  : {disk['used_disk_gb']} / {disk['total_disk_gb']} GB ({disk['disk_percent']}%)")
    print(f"  Top CPU Proc: {procs['top_cpu_processes'][0]['name']} (PID {procs['top_cpu_processes'][0]['pid']}) @ {procs['top_cpu_processes'][0]['cpu_percent']}%" if procs['top_cpu_processes'] else "  No processes")
    print("=" * 60)
    print("SystemMonitor self-test completed successfully!")
