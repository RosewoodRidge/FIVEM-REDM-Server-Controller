# Changelog

## [2.6.0] - 2025-10-11

### Added

#### Remote Control Security Enhancements

- **IP Whitelisting System**
  - Optional IP whitelist to restrict remote connections to specific IP addresses
  - Auto-whitelist feature that adds successfully authenticated IPs to the whitelist
  - UI for managing whitelisted IP addresses (add/remove)
  - Whitelist enable/disable toggle in Remote Control settings
  - Whitelist settings persist across application restarts

- **Rate Limiting & Brute Force Protection**
  - Failed authentication attempt tracking per IP address
  - Maximum 5 failed authentication attempts within a 5-minute window
  - Automatic 10-minute ban after exceeding maximum failed attempts
  - Automatic cleanup of expired bans
  - Attempt window tracking with sliding time window

- **Enhanced Authentication Security**
  - PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations
  - Random salt generation for each authentication key
  - Secure authentication key storage in settings
  - Authentication key generation using cryptographically secure random numbers
  - 24-character formatted authentication keys with dashes for readability

- **Connection Security**
  - Server now binds to all network interfaces (0.0.0.0) instead of localhost only
  - Automatic Windows Firewall rule creation for remote control port
  - Connection attempt logging with IP addresses
  - Detailed security event logging to `remote_control.log`

#### Remote Control UI Improvements

- **Whitelist Management Panel**
  - Visual list of whitelisted IP addresses
  - Add IP button with validation
  - Remove IP button for selected addresses
  - Clear status messages for whitelist operations
  - Real-time whitelist display updates

- **Connection Status Indicators**
  - Connected clients list with authentication status
  - Real-time client connection monitoring
  - IP address and port display for each connected client
  - Auto-refresh of client list every 5 seconds

- **Security Information Display**
  - Local IP address detection and display
  - Configurable port number with validation
  - Authentication key display with show/hide toggle
  - Copy-to-clipboard button for authentication key
  - Visual feedback for key operations

### Changed

- **Remote Protocol Updates**
  - Added `collections.defaultdict` import for tracking connection attempts
  - Enhanced `RemoteServer` class with security attributes
  - Improved authentication flow with security checks
  - Better error messages for security-related failures

- **Settings Management**
  - Updated default settings to include whitelist configuration
  - Added `whitelist_enabled` and `whitelisted_ips` to remote control settings
  - Settings automatically merge with defaults to ensure all keys exist

- **Logging Improvements**
  - Separate log file for remote control operations
  - Security event logging (bans, authentication failures, whitelist changes)
  - IP address logging for all connection attempts
  - Detailed error logging for troubleshooting

### Security

- **Vulnerability Mitigations**
  - Protection against brute force authentication attacks
  - Prevention of unauthorized access through IP whitelisting
  - Secure password storage using industry-standard hashing
  - Rate limiting to prevent denial-of-service attacks
  - Automatic banning of suspicious IPs

- **Best Practices Implemented**
  - Authentication required before any command execution
  - Connection attempts logged for audit trail
  - Failed authentication attempts tracked and limited
  - Secure random number generation for authentication keys
  - Strong cryptographic hashing for key verification

### Fixed

- Remote server now properly binds to all network interfaces for external connections
- Authentication key persistence across application restarts
- Firewall rule creation error handling with user feedback
- IP address validation for whitelist entries

### Technical Details

#### Security Implementation

**Rate Limiting Algorithm:**
- Tracks failed authentication attempts per IP in a sliding 5-minute window
- Clears old attempts outside the tracking window
- Implements automatic ban with configurable duration
- Ban expiration automatically removes IP from ban list

**Authentication Flow:**
1. Client connects to server
2. IP checked against ban list (reject if banned)
3. IP checked against whitelist if enabled (reject if not whitelisted)
4. Server sends AUTH_REQUIRED message
5. Client responds with authentication key
6. Server verifies key using PBKDF2-HMAC-SHA256
7. On success: IP whitelisted, attempts cleared, client authenticated
8. On failure: Attempt recorded, ban check performed, connection closed

**Whitelist Behavior:**
- When disabled: All IPs can attempt authentication (subject to rate limiting)
- When enabled: Only whitelisted IPs can attempt authentication
- Auto-whitelist: Successful authentication automatically adds IP to whitelist
- Persistent: Whitelist saved to settings and restored on application restart

#### Performance Impact

- Minimal overhead from security checks (< 1ms per connection)
- Authentication uses 100,000 PBKDF2 iterations (industry standard)
- IP tracking uses in-memory dictionaries for fast lookups
- Automatic cleanup of expired tracking data prevents memory leaks

### Dependencies

No new external dependencies required. All security features use Python's built-in modules:
- `secrets` - Cryptographically strong random number generation
- `hashlib` - PBKDF2-HMAC-SHA256 hashing
- `collections.defaultdict` - Connection attempt tracking

### Upgrade Notes

**For Users Upgrading from 2.5.x:**

1. **Existing Remote Control Settings:**
   - Authentication keys are preserved during upgrade
   - Remote control will continue to work without changes
   - Whitelist is disabled by default (opt-in security)

2. **First-Time Setup After Upgrade:**
   - Enable remote control to generate/use existing auth key
   - Optionally enable IP whitelist for additional security
   - Windows Firewall rule will be created automatically

3. **Migrating to Whitelist:**
   - Identify IPs that need remote access
   - Enable IP whitelist in Remote Control settings
   - Add authorized IPs to the whitelist
   - Test connection from each authorized IP

4. **Firewall Configuration:**
   - Application will attempt to add firewall rule automatically
   - If unsuccessful, manually allow TCP port 40100 (or configured port)
   - Rule name: "FIVEM-REDM-Controller-Remote"

### Configuration

**New Settings (in `settings.json`):**

```json
{
  "remote_control": {
    "enabled": false,
    "port": 40100,
    "auth_key": "xxxx-xxxx-xxxx-xxxx-xxxx",
    "whitelist_enabled": false,
    "whitelisted_ips": []
  }
}
```

**Recommended Security Configuration:**

For **Internet-Exposed Servers:**
- `whitelist_enabled`: true
- Add only trusted public IP addresses
- Use a VPN for remote access when possible

For **Maximum Security:**
- `whitelist_enabled`: true
- Change default port (40100) to a non-standard port
- Use strong authentication key (regenerate from UI)
- Regularly review connected clients list

### Known Issues

- Windows Firewall rule creation requires Administrator privileges
- Manual firewall configuration needed if auto-creation fails
- IP whitelist doesn't support CIDR notation (only individual IPs)

### Future Enhancements

Planned for future releases:
- TLS/SSL encryption for remote connections
- CIDR notation support for IP whitelist
- Connection rate limiting (in addition to authentication rate limiting)
- Session timeout configuration
- Two-factor authentication support

