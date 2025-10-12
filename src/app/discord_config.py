import tkinter as tk
from tkinter import ttk, messagebox
import logging

from config import COLORS
from config_manager import load_config, save_config
from discord_webhook import DEFAULT_MESSAGES, DEFAULT_COLORS, send_discord_webhook

class DiscordConfigTab:
    def __init__(self, notebook, app):
        self.app = app
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Discord Webhooks")
        
        # Dictionary to store configuration values
        self.config_vars = {}
        
        # Create tab contents
        self.create_tab_contents()
        
        # Load current configuration
        self.load_config()
    
    def create_tab_contents(self):
        # Create main frame with scrollbar
        main_container = ttk.Frame(self.tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main settings frame
        settings_frame = ttk.LabelFrame(scrollable_frame, text="Webhook Settings")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Enable checkbox
        self.config_vars['DISCORD_WEBHOOK_ENABLED'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            settings_frame,
            text="Enable Discord Webhooks",
            variable=self.config_vars['DISCORD_WEBHOOK_ENABLED']
        ).pack(anchor=tk.W, padx=10, pady=10)
        
        # Webhook URL
        url_frame = ttk.Frame(settings_frame)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            url_frame,
            text="Webhook URL:",
            width=15
        ).pack(side=tk.LEFT)
        
        self.config_vars['DISCORD_WEBHOOK_URL'] = tk.StringVar(value="")
        ttk.Entry(
            url_frame,
            textvariable=self.config_vars['DISCORD_WEBHOOK_URL'],
            width=60
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Notification types section
        notif_frame = ttk.LabelFrame(scrollable_frame, text="Enabled Notifications")
        notif_frame.pack(fill=tk.X, padx=10, pady=10)
        
        notification_types = [
            ('server_start', 'Server Start'),
            ('server_stop', 'Server Stop'),
            ('server_restart', 'Server Restart'),
            ('database_backup', 'Database Backup'),
            ('server_backup', 'Server Backup'),
            ('txadmin_update', 'TxAdmin Update'),
            ('backup_failed', 'Backup Failed'),
            ('server_error', 'Server Error')
        ]
        
        # Create two columns of checkboxes
        col1_frame = ttk.Frame(notif_frame)
        col1_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        col2_frame = ttk.Frame(notif_frame)
        col2_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        for i, (event_type, label) in enumerate(notification_types):
            var = tk.BooleanVar(value=True)
            self.config_vars[f'DISCORD_NOTIFY_{event_type.upper()}'] = var
            
            parent = col1_frame if i < 4 else col2_frame
            ttk.Checkbutton(
                parent,
                text=label,
                variable=var
            ).pack(anchor=tk.W, pady=2)
        
        # Messages and colors section
        messages_frame = ttk.LabelFrame(scrollable_frame, text="Customize Messages and Colors")
        messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable area for messages
        msg_canvas = tk.Canvas(messages_frame, bg=COLORS['panel'], height=400, highlightthickness=0)
        msg_scrollbar = ttk.Scrollbar(messages_frame, orient="vertical", command=msg_canvas.yview)
        msg_scrollable = ttk.Frame(msg_canvas)
        
        msg_scrollable.bind(
            "<Configure>",
            lambda e: msg_canvas.configure(scrollregion=msg_canvas.bbox("all"))
        )
        
        msg_canvas.create_window((0, 0), window=msg_scrollable, anchor="nw")
        msg_canvas.configure(yscrollcommand=msg_scrollbar.set)
        
        msg_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        msg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Add message and color inputs for each notification type
        for event_type, label in notification_types:
            # Event label
            ttk.Label(
                msg_scrollable,
                text=f"{label}:",
                font=('Segoe UI', 10, 'bold')
            ).pack(anchor=tk.W, padx=5, pady=(10, 5))
            
            # Message frame
            msg_frame = ttk.Frame(msg_scrollable)
            msg_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(
                msg_frame,
                text="Message:",
                width=10
            ).pack(side=tk.LEFT, anchor=tk.N, padx=(0, 5))
            
            msg_entry = tk.Text(msg_frame, width=60, height=3, wrap=tk.WORD, font=('Segoe UI', 9))
            msg_entry.insert('1.0', DEFAULT_MESSAGES.get(event_type, ""))
            msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Store text widget reference
            self.config_vars[f'DISCORD_MSG_{event_type.upper()}_WIDGET'] = msg_entry
            
            # Color frame
            color_frame = ttk.Frame(msg_scrollable)
            color_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(
                color_frame,
                text="Color:",
                width=10
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            color_var = tk.StringVar(value=hex(DEFAULT_COLORS.get(event_type, 0x3b82f6)))
            self.config_vars[f'DISCORD_COLOR_{event_type.upper()}'] = color_var
            
            ttk.Entry(
                color_frame,
                textvariable=color_var,
                width=15
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            # Color preview
            color_preview = tk.Label(
                color_frame,
                text="   ",
                bg=self._hex_to_color(color_var.get()),
                relief=tk.RAISED,
                width=3
            )
            color_preview.pack(side=tk.LEFT, padx=5)
            
            # Update preview when color changes
            color_var.trace('w', lambda *args, p=color_preview, v=color_var: self._update_preview(p, v))
            
            # Separator
            ttk.Separator(msg_scrollable, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons at the bottom
        button_frame = ttk.Frame(self.tab)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ttk.Button(
            button_frame,
            text="Test Webhook",
            command=self.test_webhook
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_config,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            button_frame,
            text="Ready",
            foreground=COLORS['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def load_config(self):
        """Load Discord webhook configuration"""
        try:
            config_dict = load_config()
            webhook_config = config_dict.get('DISCORD_WEBHOOK', {})
            
            # Load basic settings
            self.config_vars['DISCORD_WEBHOOK_ENABLED'].set(webhook_config.get('enabled', False))
            self.config_vars['DISCORD_WEBHOOK_URL'].set(webhook_config.get('webhook_url', ''))
            
            # Load notification settings
            notifications = webhook_config.get('notifications', {})
            for event_type in ['server_start', 'server_stop', 'server_restart', 
                             'database_backup', 'server_backup', 'txadmin_update',
                             'backup_failed', 'server_error']:
                var = self.config_vars.get(f'DISCORD_NOTIFY_{event_type.upper()}')
                if var:
                    var.set(notifications.get(event_type, True))
            
            # Load messages
            messages = webhook_config.get('messages', {})
            for event_type in ['server_start', 'server_stop', 'server_restart', 
                             'database_backup', 'server_backup', 'txadmin_update',
                             'backup_failed', 'server_error']:
                widget = self.config_vars.get(f'DISCORD_MSG_{event_type.upper()}_WIDGET')
                if widget:
                    msg = messages.get(event_type, DEFAULT_MESSAGES.get(event_type, ''))
                    widget.delete('1.0', tk.END)
                    widget.insert('1.0', msg)
            
            # Load colors
            colors = webhook_config.get('colors', {})
            for event_type in ['server_start', 'server_stop', 'server_restart', 
                             'database_backup', 'server_backup', 'txadmin_update',
                             'backup_failed', 'server_error']:
                var = self.config_vars.get(f'DISCORD_COLOR_{event_type.upper()}')
                if var:
                    color = colors.get(event_type, DEFAULT_COLORS.get(event_type, 0x3b82f6))
                    var.set(hex(color))
            
            self.app.log_message("Discord webhook configuration loaded")
        
        except Exception as e:
            logging.error(f"Failed to load Discord webhook config: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_config(self):
        """Save Discord webhook configuration"""
        try:
            # Load existing config
            config_dict = load_config()
            
            # Build webhook configuration
            webhook_config = {
                'enabled': self.config_vars['DISCORD_WEBHOOK_ENABLED'].get(),
                'webhook_url': self.config_vars['DISCORD_WEBHOOK_URL'].get(),
                'notifications': {},
                'messages': {},
                'colors': {}
            }
            
            notification_types = ['server_start', 'server_stop', 'server_restart', 
                                'database_backup', 'server_backup', 'txadmin_update',
                                'backup_failed', 'server_error']
            
            for event_type in notification_types:
                # Notification enabled
                var = self.config_vars.get(f'DISCORD_NOTIFY_{event_type.upper()}')
                if var:
                    webhook_config['notifications'][event_type] = var.get()
                
                # Message
                widget = self.config_vars.get(f'DISCORD_MSG_{event_type.upper()}_WIDGET')
                if widget:
                    webhook_config['messages'][event_type] = widget.get('1.0', tk.END).strip()
                
                # Color
                var = self.config_vars.get(f'DISCORD_COLOR_{event_type.upper()}')
                if var:
                    try:
                        color_str = var.get().replace('0x', '').replace('#', '')
                        webhook_config['colors'][event_type] = int(color_str, 16)
                    except:
                        webhook_config['colors'][event_type] = DEFAULT_COLORS.get(event_type, 0x3b82f6)
            
            # Update config dict
            config_dict['DISCORD_WEBHOOK'] = webhook_config
            
            # Save to JSON
            success, result = save_config(config_dict)
            
            if success:
                self.status_label.config(text="Configuration saved successfully!", foreground="green")
                self.app.log_message(f"Discord webhook configuration saved to {result}")
                messagebox.showinfo("Success", "Discord webhook configuration saved successfully!")
            else:
                raise Exception(result)
        
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", foreground="red")
            error_msg = f"Failed to save configuration: {e}"
            logging.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def test_webhook(self):
        """Test the Discord webhook"""
        try:
            from discord_webhook import send_discord_webhook
            
            # Temporarily save current config
            webhook_url = self.config_vars['DISCORD_WEBHOOK_URL'].get()
            enabled = self.config_vars['DISCORD_WEBHOOK_ENABLED'].get()
            
            if not enabled:
                messagebox.showwarning("Webhook Disabled", "Please enable Discord webhooks first.")
                return
            
            if not webhook_url:
                messagebox.showerror("No Webhook URL", "Please enter a webhook URL first.")
                return
            
            # Validate webhook URL format
            if not webhook_url.startswith('https://discord.com/api/webhooks/'):
                messagebox.showerror("Invalid URL", "Webhook URL must start with 'https://discord.com/api/webhooks/'")
                return
            
            # Create temporary config for testing
            test_config = {
                'enabled': True,
                'webhook_url': webhook_url,
                'notifications': {'server_start': True},
                'messages': {'server_start': "🧪 **Webhook Test**\nThis is a test message from your FIVEM & REDM Server Controller!"},
                'colors': {'server_start': 0x00FF00}
            }
            
            # Temporarily override load_webhook_config
            import discord_webhook
            original_load = discord_webhook.load_webhook_config
            discord_webhook.load_webhook_config = lambda: test_config
            
            try:
                # Send test
                success, message = send_discord_webhook('server_start')
                
                if success:
                    messagebox.showinfo("Success", "Test webhook sent successfully! Check your Discord channel.")
                    self.app.log_message("Discord webhook test sent successfully")
                else:
                    messagebox.showerror("Failed", f"Failed to send webhook:\n{message}")
                    self.app.log_message(f"Discord webhook test failed: {message}")
            finally:
                # Restore original function
                discord_webhook.load_webhook_config = original_load
                
        except Exception as e:
            messagebox.showerror("Error", f"Error testing webhook:\n{str(e)}")
            logging.error(f"Error testing webhook: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _hex_to_color(self, hex_str):
        """Convert hex string to color string for tkinter"""
        try:
            hex_str = hex_str.replace('0x', '').replace('#', '')
            if len(hex_str) == 6:
                return f'#{hex_str}'
            elif len(hex_str) < 6:
                return f'#{"0" * (6 - len(hex_str))}{hex_str}'
        except:
            pass
        return '#3b82f6'
    
    def _update_preview(self, preview_label, var):
        """Update color preview"""
        try:
            color = self._hex_to_color(var.get())
            preview_label.config(bg=color)
        except:
            pass
