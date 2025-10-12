# Changelog

All notable changes to the FIVEM & REDM Server Controller will be documented in this file.

## [2.7.7]

### Added
- **Discord Webhook Integration** - Send notifications to Discord for server events
  - Separate Discord Webhooks configuration tab for easy management
  - Configurable webhook URL with test functionality
  - Per-event notification toggles (server start/stop/restart, backups, updates, errors)
  - Customizable message content for each event type with emoji support
  - Color-coded embed messages with hex color input and live preview
  - Default messages included with appropriate emojis for all events
  - Rich embed format with timestamps and footer branding
- Discord webhook notifications for:
  - Server start, stop, and restart operations
  - Database and server backup completion
  - TxAdmin updates
  - Backup failures and server errors
- Webhook configuration saved to JSON config file
- Input validation for webhook URLs

### Changed
- Main application window width increased to 975px (from 925px) to accommodate Discord tab
- Discord webhook settings separated from main configuration tab
- Improved error handling for Discord webhook delivery
- Enhanced logging for webhook operations with detailed error responses

### Fixed
- Discord webhook HTTP 403 errors resolved with proper headers and timestamp format
- Webhook requests now include User-Agent and Content-Length headers
- Timezone-aware timestamps for Discord API compatibility
- Better error reporting when webhook delivery fails

## [2.7.6]

### Added
- **Resource Monitoring Tab** - Remote app now displays live system resource statistics
  - Real-time monitoring of CPU, RAM, Disk, and Network usage
  - Live graphs showing 60 seconds of usage history
  - Data updates every second with minimal delay
  - Main app broadcasts resource stats to all connected remote clients
- Cross-platform resource monitoring support (Windows and Linux)
- New `psutil` dependency for system resource collection

### Changed
- Remote app window width increased to 925px to accommodate new Resources tab
- Resource monitor runs in background thread on main app (no UI impact)

### Fixed
- Improved platform detection for disk usage monitoring
- Enhanced Linux compatibility for file removal operations

## [2.7.5]

### Added
- Automatic application updates via GitHub releases
- Update notification dialog with changelog display
- Option to skip specific update versions
- Update progress tracking with visual feedback
- Automatic configuration preservation during updates

### Changed
- Improved update checking logic with 24-hour interval
- Enhanced error handling for update operations
- Update process now uses install scripts for clean updates

### Fixed
- Configuration settings now properly preserved across updates
- Update download progress now shows accurate file size

## [2.7.4] 

### Added
- Cross-platform support for Windows and Linux
- Platform-specific default paths for MySQL and 7-Zip
- Automatic platform detection and configuration
- JSON-based configuration system for easier management
- Data and logs directories organized by execution mode (dev vs exe)

### Changed
- Configuration now stored in JSON format instead of Python file
- Settings separated into `data/` folder for better organization
- Logs moved to dedicated `logs/` folder
- Remote control settings now stored in `remote_config.json`

### Fixed
- Firewall rule management now properly skips on non-Windows systems
- MySQL executables now found in PATH on Linux systems
- File paths now use platform-appropriate separators

## [2.6.0]

### Added
- TxAdmin automatic updates
- TxAdmin backup before updates
- TxAdmin version tracking
- Rollback functionality for TxAdmin updates
- Progress tracking for TxAdmin operations

### Changed
- Improved TxAdmin update detection
- Enhanced 7-Zip integration
- Better error handling for TxAdmin operations

### Fixed
- TxAdmin extraction issues on some systems
- Download progress reporting accuracy

## [2.5.0]

### Added
- Server resources folder backup
- Scheduled server backups
- Server backup restoration
- Configurable server backup retention

### Changed
- Improved backup scheduling system
- Enhanced progress reporting for backups

## [2.4.0] 

### Added
- FXServer process control (start, stop, restart)
- Server status monitoring
- Process ID tracking
- Real-time server status updates

### Changed
- Improved process detection for FXServer
- Better error handling for server operations

## [2.3.0]

### Added
- Database backup scheduling
- Automatic old backup cleanup
- Backup retention policy (keep last 100 backups)
- Next backup countdown timer

### Changed
- Enhanced backup timing accuracy
- Improved schedule configuration

## [2.2.0] 

### Added
- Database restoration from backup
- Backup file selection interface
- Confirmation dialogs for dangerous operations

### Security
- Added warnings for destructive operations

## [2.1.0]

### Added
- Manual database backup functionality
- Backup file listing
- Backup timestamp display

### Changed
- Improved mysqldump integration
- Better error messages for backup failures

## [2.0.0]

### Added
- Modern GUI using tkinter
- Tab-based interface
- Activity logging
- Status bar
- Styled components with dark theme

### Changed
- Complete UI overhaul from command-line to graphical interface
- Improved user experience

## [1.0.0]

### Added
- Initial release
- Basic database backup functionality
- Command-line interface
- MySQL integration

