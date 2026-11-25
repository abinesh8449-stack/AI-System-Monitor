import socket
import time
import sys
from pathlib import Path
import psutil  # type: ignore

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
            NETWORK_PING_HOST = "8.8.8.8"
            NETWORK_PING_PORT = 53
            NETWORK_TIMEOUT = 1.5
        return _FallbackConfig

Config = _resolve_config()

class NetworkMonitor:
    """Monitors network I/O transfer rates, connectivity status, and interface details."""
    
    def __init__(self):
        self._prev_counters = psutil.net_io_counters()
        self._prev_time = time.time()
        
    def get_transfer_rates(self):
        """Calculate network upload and download speed in KB/s since last measurement."""
        current_counters = psutil.net_io_counters()
        current_time = time.time()
        
        delta_time = current_time - self._prev_time
        if delta_time <= 0:
            delta_time = 1.0
            
        bytes_sent_delta = current_counters.bytes_sent - self._prev_counters.bytes_sent
        bytes_recv_delta = current_counters.bytes_recv - self._prev_counters.bytes_recv
        
        # Handle counter overflow/resets
        if bytes_sent_delta < 0:
            bytes_sent_delta = 0
        if bytes_recv_delta < 0:
            bytes_recv_delta = 0
            
        upload_speed_kb = round((bytes_sent_delta / 1024.0) / delta_time, 2)
        download_speed_kb = round((bytes_recv_delta / 1024.0) / delta_time, 2)
        
        # Update baseline
        self._prev_counters = current_counters
        self._prev_time = current_time
        
        return {
            "upload_speed_kb": upload_speed_kb,
            "download_speed_kb": download_speed_kb,
            "upload_speed_mb": round(upload_speed_kb / 1024.0, 3),
            "download_speed_mb": round(download_speed_kb / 1024.0, 3),
            "total_sent_mb": round(current_counters.bytes_sent / (1024 ** 2), 2),
            "total_recv_mb": round(current_counters.bytes_recv / (1024 ** 2), 2)
        }
        
    @staticmethod
    def check_connectivity(host=None, port=None, timeout=None):
        """Test internet connectivity via lightweight socket connection probe."""
        target_host = host or Config.NETWORK_PING_HOST
        target_port = port or Config.NETWORK_PING_PORT
        target_timeout = timeout or Config.NETWORK_TIMEOUT
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(target_timeout)
            sock.connect((target_host, target_port))
            sock.close()
            return True, "Connected"
        except socket.timeout:
            return False, "High Latency / Timed Out"
        except Exception:
            # Fallback probe to Cloudflare DNS
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(target_timeout)
                sock.connect(("1.1.1.1", 53))
                sock.close()
                return True, "Connected"
            except Exception:
                return False, "Disconnected"

    @staticmethod
    def get_interface_details():
        """Retrieve hardware and virtual network interface details."""
        interfaces = []
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for iface_name, addr_list in addrs.items():
            ipv4 = "N/A"
            netmask = "N/A"
            mac = "N/A"
            
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    ipv4 = addr.address
                    netmask = addr.netmask
                elif hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                    mac = addr.address
                elif addr.family == -1 or str(addr.family) == "AddressFamily.AF_LINK":
                    mac = addr.address
                    
            stat = stats.get(iface_name)
            is_up = stat.isup if stat else False
            speed = stat.speed if stat else 0
            
            interfaces.append({
                "interface": iface_name,
                "ipv4": ipv4,
                "netmask": netmask,
                "mac": mac,
                "is_up": is_up,
                "speed_mbps": speed
            })
            
        # Get Primary Host IP
        primary_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                primary_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                pass

        return {
            "primary_ip": primary_ip,
            "interfaces": interfaces
        }

# Global singleton monitor instance for steady speed calculations
network_monitor = NetworkMonitor()

if __name__ == '__main__':
    print("=" * 60)
    print("  NETWORK MONITOR MODULE SELF-TEST")
    print("=" * 60)
    connected, status = network_monitor.check_connectivity()
    details = network_monitor.get_interface_details()
    print(f"  Connectivity : {'ONLINE' if connected else 'OFFLINE'} ({status})")
    print(f"  Primary IP   : {details.get('primary_ip', 'Unknown')}")
    print(f"  NIC Count    : {len(details.get('interfaces', []))}")
    print("  Measuring transfer rates over 1 second...")
    time.sleep(1.0)
    rates = network_monitor.get_transfer_rates()
    print(f"  Upload Speed : {rates['upload_speed_kb']} KB/s")
    print(f"  Download Spd : {rates['download_speed_kb']} KB/s")
    print("=" * 60)
    print("NetworkMonitor self-test completed successfully!")
