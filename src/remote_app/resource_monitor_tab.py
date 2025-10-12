import tkinter as tk
from tkinter import ttk
from datetime import datetime
from collections import deque

from config import COLORS

class ResourceMonitorTab:
    """Remote resource monitoring tab with live graphs"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        
        # Tab will be added to notebook by main app
        self.tab_index = None
        
        # History for graphs (60 data points = 1 minute)
        self.history_size = 60
        self.cpu_history = deque(maxlen=self.history_size)
        self.ram_history = deque(maxlen=self.history_size)
        self.disk_history = deque(maxlen=self.history_size)
        self.network_history = deque(maxlen=self.history_size)
        
        # Current stats
        self.current_stats = None
        self.worst_status = '⚫'
        
        # Create tab contents
        self.create_tab_contents()
    
    def create_tab_contents(self):
        """Create the resource monitoring UI"""
        # Main container
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row - Current stats
        stats_frame = ttk.LabelFrame(main_frame, text="Current Usage")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create stats display
        self.create_stats_display(stats_frame)
        
        # Bottom row - Graphs
        graphs_frame = ttk.LabelFrame(main_frame, text="Resource History (Last 60 seconds)")
        graphs_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create graph canvases
        self.create_graphs(graphs_frame)
    
    def create_stats_display(self, parent):
        """Create current stats display with indicators"""
        # Grid layout for stats
        stats_container = ttk.Frame(parent)
        stats_container.pack(fill=tk.X, padx=10, pady=10)
        
        # CPU
        cpu_frame = ttk.Frame(stats_container)
        cpu_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.cpu_indicator = ttk.Label(cpu_frame, text="⚫", font=('Segoe UI', 16))
        self.cpu_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        cpu_info_frame = ttk.Frame(cpu_frame)
        cpu_info_frame.pack(side=tk.LEFT)
        
        ttk.Label(cpu_info_frame, text="CPU", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        self.cpu_label = ttk.Label(cpu_info_frame, text="---%", font=('Segoe UI', 14))
        self.cpu_label.pack(anchor=tk.W)
        
        # RAM
        ram_frame = ttk.Frame(stats_container)
        ram_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        self.ram_indicator = ttk.Label(ram_frame, text="⚫", font=('Segoe UI', 16))
        self.ram_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        ram_info_frame = ttk.Frame(ram_frame)
        ram_info_frame.pack(side=tk.LEFT)
        
        ttk.Label(ram_info_frame, text="RAM", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        self.ram_label = ttk.Label(ram_info_frame, text="---% (-- / -- GB)", font=('Segoe UI', 14))
        self.ram_label.pack(anchor=tk.W)
        
        # Disk
        disk_frame = ttk.Frame(stats_container)
        disk_frame.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.disk_indicator = ttk.Label(disk_frame, text="⚫", font=('Segoe UI', 16))
        self.disk_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        disk_info_frame = ttk.Frame(disk_frame)
        disk_info_frame.pack(side=tk.LEFT)
        
        ttk.Label(disk_info_frame, text="Disk", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        self.disk_label = ttk.Label(disk_info_frame, text="---% (-- / -- GB)", font=('Segoe UI', 14))
        self.disk_label.pack(anchor=tk.W)
        
        # Network
        network_frame = ttk.Frame(stats_container)
        network_frame.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        ttk.Label(network_frame, text="📡", font=('Segoe UI', 16)).pack(side=tk.LEFT, padx=(0, 5))
        
        network_info_frame = ttk.Frame(network_frame)
        network_info_frame.pack(side=tk.LEFT)
        
        ttk.Label(network_info_frame, text="Network", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        self.network_label = ttk.Label(network_info_frame, text="-- MB/s", font=('Segoe UI', 14))
        self.network_label.pack(anchor=tk.W)
    
    def create_graphs(self, parent):
        """Create canvas-based graphs for resource history"""
        graph_container = ttk.Frame(parent)
        graph_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights
        graph_container.grid_rowconfigure(0, weight=1)
        graph_container.grid_rowconfigure(1, weight=1)
        graph_container.grid_columnconfigure(0, weight=1)
        graph_container.grid_columnconfigure(1, weight=1)
        
        # CPU Graph
        cpu_frame = ttk.LabelFrame(graph_container, text="CPU Usage")
        cpu_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        self.cpu_canvas = tk.Canvas(cpu_frame, bg='#1e293b', height=150, highlightthickness=0)
        self.cpu_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # RAM Graph
        ram_frame = ttk.LabelFrame(graph_container, text="RAM Usage")
        ram_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        self.ram_canvas = tk.Canvas(ram_frame, bg='#1e293b', height=150, highlightthickness=0)
        self.ram_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Disk Graph
        disk_frame = ttk.LabelFrame(graph_container, text="Disk Usage")
        disk_frame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        self.disk_canvas = tk.Canvas(disk_frame, bg='#1e293b', height=150, highlightthickness=0)
        self.disk_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Network Graph
        network_frame = ttk.LabelFrame(graph_container, text="Network Rate")
        network_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        self.network_canvas = tk.Canvas(network_frame, bg='#1e293b', height=150, highlightthickness=0)
        self.network_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_stats(self, stats):
        """Update display with new stats"""
        if not stats:
            return
        
        self.current_stats = stats
        
        # Update history
        self.cpu_history.append(stats['cpu_percent'])
        self.ram_history.append(stats['ram_percent'])
        self.disk_history.append(stats['disk_percent'])
        self.network_history.append(stats['network_rate_mbps'])
        
        # Update labels
        self.cpu_label.config(text=f"{stats['cpu_percent']}%")
        self.ram_label.config(text=f"{stats['ram_percent']}% ({stats['ram_used_gb']:.1f} / {stats['ram_total_gb']:.1f} GB)")
        self.disk_label.config(text=f"{stats['disk_percent']}% ({stats['disk_used_gb']:.1f} / {stats['disk_total_gb']:.1f} GB)")
        self.network_label.config(text=f"{stats['network_rate_mbps']:.2f} MB/s")
        
        # Update indicators
        self.cpu_indicator.config(text=self.get_status_indicator(stats['cpu_percent']))
        self.ram_indicator.config(text=self.get_status_indicator(stats['ram_percent']))
        self.disk_indicator.config(text=self.get_status_indicator(stats['disk_percent']))
        
        # Update worst status and tab header
        self.update_worst_status(stats)
        
        # Redraw graphs
        self.draw_graphs()
    
    def get_status_indicator(self, percent):
        """Get status indicator emoji based on usage percentage"""
        if percent >= 90:
            return '🔴'
        elif percent >= 75:
            return '🟡'
        else:
            return '🟢'
    
    def update_worst_status(self, stats):
        """Update worst status indicator and tab header"""
        indicators = [
            self.get_status_indicator(stats['cpu_percent']),
            self.get_status_indicator(stats['ram_percent']),
            self.get_status_indicator(stats['disk_percent'])
        ]
        
        # Priority: Red > Yellow > Green
        if '🔴' in indicators:
            self.worst_status = '🔴'
        elif '🟡' in indicators:
            self.worst_status = '🟡'
        else:
            self.worst_status = '🟢'
        
        # Update tab header without emoji since it doesn't render in color
        if self.tab_index is not None and hasattr(self.app, 'notebook'):
            # Verify we're updating the correct tab by checking current text
            try:
                current_text = self.app.notebook.tab(self.tab_index, "text")
                # Only update if this tab currently says "Resources" (not "Activity Log")
                if current_text and "Resources" in current_text:
                    status_text = "Resources"
                    if self.worst_status == '🔴':
                        status_text = "Resources"
                    elif self.worst_status == '🟡':
                        status_text = "Resources"
                    else:
                        status_text = "Resources"
                    
                    self.app.notebook.tab(self.tab_index, text=status_text)
            except Exception as e:
                # Silently fail if tab doesn't exist
                pass

    def draw_graphs(self):
        """Draw line graphs for resource history"""
        self.draw_graph(self.cpu_canvas, self.cpu_history, '#3b82f6', 100)
        self.draw_graph(self.ram_canvas, self.ram_history, '#8b5cf6', 100)
        self.draw_graph(self.disk_canvas, self.disk_history, '#06b6d4', 100)
        
        # Network graph with dynamic max
        max_network = max(self.network_history) if self.network_history else 10
        max_network = max(max_network, 10)  # Minimum 10 MB/s scale
        self.draw_graph(self.network_canvas, self.network_history, '#10b981', max_network)
    
    def draw_graph(self, canvas, data, color, max_value):
        """Draw a line graph on canvas"""
        canvas.delete("all")
        
        if not data or len(data) < 2:
            return
        
        # Get canvas dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        # Calculate points
        points = []
        x_step = width / (self.history_size - 1)
        
        for i, value in enumerate(data):
            x = i * x_step
            # Invert y (canvas y increases downward)
            y = height - (value / max_value * height)
            points.append((x, y))
        
        # Draw grid lines
        for i in range(0, 101, 25):
            y = height - (i / 100 * height)
            canvas.create_line(0, y, width, y, fill='#334155', dash=(2, 2))
            canvas.create_text(5, y - 2, text=f"{i}%", anchor=tk.NW, fill='#64748b', font=('Segoe UI', 8))
        
        # Draw line
        if len(points) > 1:
            canvas.create_line(points, fill=color, width=2, smooth=True)
        
        # Draw current value
        if points:
            last_x, last_y = points[-1]
            canvas.create_oval(last_x - 3, last_y - 3, last_x + 3, last_y + 3, fill=color, outline='white')
