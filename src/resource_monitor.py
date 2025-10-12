import psutil
import logging
from datetime import datetime

class ResourceMonitor:
    """Monitor system resources (CPU, RAM, Disk, Network) - Works on Windows and Linux"""
    
    def __init__(self):
        self.history_size = 60  # Keep 60 seconds of history
        self.cpu_history = []
        self.ram_history = []
        self.disk_history = []
        self.network_history = []
        
        # For network rate calculation
        self.last_network_io = None
        self.last_network_time = None
    
    def get_current_stats(self):
        """Get current system resource statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # RAM usage
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)
            
            # Disk usage (main drive) - use '/' for Linux, 'C:\' for Windows
            try:
                import sys
                if sys.platform.startswith('linux'):
                    disk = psutil.disk_usage('/')
                else:
                    disk = psutil.disk_usage('C:\\')
            except:
                # Fallback to root
                disk = psutil.disk_usage('/')
                
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent_mb = network_io.bytes_sent / (1024 ** 2)
            network_recv_mb = network_io.bytes_recv / (1024 ** 2)
            
            # Calculate network rate (MB/s)
            network_rate = self._calculate_network_rate(network_io)
            
            stats = {
                'timestamp': datetime.now().timestamp(),
                'cpu_percent': round(cpu_percent, 1),
                'ram_percent': round(ram_percent, 1),
                'ram_used_gb': round(ram_used_gb, 2),
                'ram_total_gb': round(ram_total_gb, 2),
                'disk_percent': round(disk_percent, 1),
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_total_gb': round(disk_total_gb, 2),
                'network_sent_mb': round(network_sent_mb, 2),
                'network_recv_mb': round(network_recv_mb, 2),
                'network_rate_mbps': round(network_rate, 2)
            }
            
            # Update history
            self._update_history(stats)
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting resource stats: {e}")
            return None
    
    def _calculate_network_rate(self, current_io):
        """Calculate network transfer rate in MB/s"""
        current_time = datetime.now().timestamp()
        
        if self.last_network_io is None:
            self.last_network_io = current_io
            self.last_network_time = current_time
            return 0.0
        
        # Calculate time difference
        time_diff = current_time - self.last_network_time
        if time_diff == 0:
            return 0.0
        
        # Calculate bytes transferred
        bytes_sent_diff = current_io.bytes_sent - self.last_network_io.bytes_sent
        bytes_recv_diff = current_io.bytes_recv - self.last_network_io.bytes_recv
        total_bytes = bytes_sent_diff + bytes_recv_diff
        
        # Calculate rate in MB/s
        rate_mbps = (total_bytes / time_diff) / (1024 ** 2)
        
        # Update last values
        self.last_network_io = current_io
        self.last_network_time = current_time
        
        return rate_mbps
    
    def _update_history(self, stats):
        """Update history lists with new stats"""
        self.cpu_history.append(stats['cpu_percent'])
        self.ram_history.append(stats['ram_percent'])
        self.disk_history.append(stats['disk_percent'])
        self.network_history.append(stats['network_rate_mbps'])
        
        # Keep only last N entries
        if len(self.cpu_history) > self.history_size:
            self.cpu_history.pop(0)
        if len(self.ram_history) > self.history_size:
            self.ram_history.pop(0)
        if len(self.disk_history) > self.history_size:
            self.disk_history.pop(0)
        if len(self.network_history) > self.history_size:
            self.network_history.pop(0)
    
    def get_status_indicator(self, percent):
        """Get status indicator emoji based on usage percentage"""
        if percent >= 90:
            return '🔴'  # Red - Critical
        elif percent >= 75:
            return '🟡'  # Yellow - Warning
        else:
            return '🟢'  # Green - Good
    
    def get_worst_status(self, stats):
        """Get the worst status indicator from all metrics"""
        if not stats:
            return '⚫'  # Black - No data
        
        indicators = [
            self.get_status_indicator(stats['cpu_percent']),
            self.get_status_indicator(stats['ram_percent']),
            self.get_status_indicator(stats['disk_percent'])
        ]
        
        # Priority: Red > Yellow > Green
        if '🔴' in indicators:
            return '🔴'
        elif '🟡' in indicators:
            return '🟡'
        else:
            return '🟢'
