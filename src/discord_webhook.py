import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from config_manager import get_data_dir, load_config
import os

# Default messages with emojis
DEFAULT_MESSAGES = {
    "server_start": "🚀 **Server Started**\nThe FXServer has been started successfully.",
    "server_stop": "🛑 **Server Stopped**\nThe FXServer has been stopped.",
    "server_restart": "🔄 **Server Restarting**\nThe FXServer is being restarted.",
    "database_backup": "💾 **Database Backup Complete**\nA database backup has been created successfully.",
    "server_backup": "📦 **Server Backup Complete**\nA server files backup has been created successfully.",
    "txadmin_update": "⬆️ **TxAdmin Update**\nTxAdmin has been updated to the latest version.",
    "backup_failed": "❌ **Backup Failed**\nA backup operation has failed. Check logs for details.",
    "server_error": "⚠️ **Server Error**\nAn error occurred with the server. Check logs for details."
}

DEFAULT_COLORS = {
    "server_start": 0x00FF00,      # Green
    "server_stop": 0xFF0000,        # Red
    "server_restart": 0xFFA500,     # Orange
    "database_backup": 0x0099FF,    # Blue
    "server_backup": 0x9966FF,      # Purple
    "txadmin_update": 0x00FFFF,     # Cyan
    "backup_failed": 0xFF0000,      # Red
    "server_error": 0xFF6600        # Orange-Red
}

def load_webhook_config():
    """Load Discord webhook configuration from config file"""
    try:
        config = load_config()
        webhook_config = config.get('DISCORD_WEBHOOK', {})
        
        # If webhook_config is empty or doesn't have required fields, return defaults
        if not webhook_config or not isinstance(webhook_config, dict):
            logging.warning("Discord webhook config not found or invalid, using defaults")
            return {
                'enabled': False,
                'webhook_url': '',
                'notifications': {
                    'server_start': True,
                    'server_stop': True,
                    'server_restart': True,
                    'database_backup': True,
                    'server_backup': True,
                    'txadmin_update': True,
                    'backup_failed': True,
                    'server_error': True
                },
                'messages': DEFAULT_MESSAGES.copy(),
                'colors': DEFAULT_COLORS.copy()
            }
        
        # Ensure all required fields exist with defaults
        result = {
            'enabled': webhook_config.get('enabled', False),
            'webhook_url': webhook_config.get('webhook_url', ''),
            'notifications': webhook_config.get('notifications', {}),
            'messages': webhook_config.get('messages', {}),
            'colors': webhook_config.get('colors', {})
        }
        
        # Merge with defaults for any missing notification types
        for event_type in DEFAULT_MESSAGES.keys():
            if event_type not in result['notifications']:
                result['notifications'][event_type] = True
            if event_type not in result['messages']:
                result['messages'][event_type] = DEFAULT_MESSAGES[event_type]
            if event_type not in result['colors']:
                result['colors'][event_type] = DEFAULT_COLORS[event_type]
        
        logging.info(f"Loaded Discord webhook config: enabled={result['enabled']}, url={'set' if result['webhook_url'] else 'not set'}")
        logging.debug(f"Notifications enabled: {result['notifications']}")
        
        return result
        
    except Exception as e:
        logging.error(f"Failed to load webhook config: {e}")
        logging.error(f"Exception details:", exc_info=True)
        return {
            'enabled': False,
            'webhook_url': '',
            'notifications': {},
            'messages': DEFAULT_MESSAGES.copy(),
            'colors': DEFAULT_COLORS.copy()
        }

def send_discord_webhook(event_type, custom_message=None, custom_color=None):
    """
    Send a message to Discord via webhook
    
    Args:
        event_type: Type of event (server_start, database_backup, etc.)
        custom_message: Optional custom message to override default
        custom_color: Optional custom color to override default
    
    Returns:
        tuple: (success, message)
    """
    try:
        logging.info(f"Attempting to send Discord webhook for event: {event_type}")
        
        config = load_webhook_config()
        
        # Check if webhooks are enabled
        if not config.get('enabled', False):
            logging.info("Discord webhooks are disabled")
            return True, "Webhooks disabled"
        
        # Check if this notification type is enabled
        notifications = config.get('notifications', {})
        if event_type not in notifications:
            logging.warning(f"Event type '{event_type}' not found in notifications config")
            return True, f"Event type '{event_type}' not configured"
        
        if not notifications.get(event_type, False):
            logging.info(f"Notifications disabled for event type: {event_type}")
            return True, f"Notifications disabled for {event_type}"
        
        webhook_url = config.get('webhook_url', '')
        if not webhook_url:
            logging.error("Webhook URL not configured")
            return False, "Webhook URL not configured"
        
        logging.info(f"Sending webhook to: {webhook_url[:50]}... for event: {event_type}")
        
        # Get message and color
        message = custom_message or config.get('messages', {}).get(event_type, DEFAULT_MESSAGES.get(event_type, "Event occurred"))
        color = custom_color or config.get('colors', {}).get(event_type, DEFAULT_COLORS.get(event_type, 0x3b82f6))
        
        # Parse message for title and description
        parts = message.split('\n', 1)
        title = parts[0].strip('*').strip()
        description = parts[1] if len(parts) > 1 else ""
        
        # Create embed with proper timestamp format
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),  # Use timezone-aware datetime
            "footer": {
                "text": "FIVEM & REDM Server Controller"
            }
        }
        
        # Create payload
        payload = {
            "embeds": [embed]
        }
        
        # Convert to JSON and encode
        json_data = json.dumps(payload)
        data = json_data.encode('utf-8')
        
        logging.debug(f"Webhook payload: {json_data}")
        
        # Create request with proper headers
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'DiscordBot (FIVEM-REDM-Controller, 1.0)',
                'Content-Length': str(len(data))
            },
            method='POST'
        )
        
        # Send webhook
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            if response.status in [200, 204]:
                logging.info(f"Discord webhook sent successfully for {event_type}")
                return True, "Webhook sent successfully"
            else:
                error_msg = f"Webhook failed with status {response.status}: {response_data}"
                logging.error(error_msg)
                return False, error_msg
                
    except urllib.error.HTTPError as e:
        # Read the error response for more details
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except:
            pass
        
        error_msg = f"HTTP Error sending webhook: {e.code} - {e.reason}"
        if error_body:
            error_msg += f"\nResponse: {error_body}"
        
        logging.error(error_msg)
        logging.error(f"Request URL: {webhook_url}")
        logging.error(f"Request payload: {json_data if 'json_data' in locals() else 'N/A'}")
        
        return False, f"{e.code} - {e.reason}"
    except urllib.error.URLError as e:
        error_msg = f"URL Error sending webhook: {e.reason}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error sending Discord webhook: {str(e)}"
        logging.error(error_msg)
        logging.error(f"Exception type: {type(e).__name__}")
        import traceback
        logging.error(traceback.format_exc())
        return False, error_msg
