# Screenwatch

A systemd user service that monitors udev for screen/monitor connection and disconnection events, automatically executing a configured command when displays are attached or detached.

## Features

- **Automatic screen detection**: Monitors udev DRM (Direct Rendering Manager) events
- **Configurable command**: Run any command on screen changes (default: `autorandr -c`)
- **Desktop environment exclusions**: Skip execution on DEs that handle screen management natively (GNOME, KDE, XFCE, COSMIC, etc.)
- **Debouncing**: Prevents rapid repeated executions when screens stabilize
- **User service**: Runs in user session, no root required
- **Easy installation**: Install with pipx and manage with Make

## Use Case

Perfect for users who:
- Use `autorandr` to manage multiple monitor configurations
- Switch between docked/undocked laptop setups
- Want automatic screen configuration without relying on DE-specific tools
- Use lightweight window managers (i3, sway, bspwm, etc.) without built-in display management

## Requirements

- Python 3.8+
- pipx (for installation)
- systemd (user session)
- pyudev library (installed automatically)

## Installation

### Quick Install

```bash
# Install pipx if not already installed
# Debian/Ubuntu:
sudo apt install pipx

# Fedora:
sudo dnf install pipx

# Arch:
sudo pacman -S python-pipx

# Install screenwatch
make install

# Enable and start the service
make enable
make start
```

### Manual Installation

```bash
# Install dependencies
make install-deps

# Install systemd service
make install-service

# Enable service
make enable

# Start service
make start
```

## Configuration

Configuration file: `~/.config/screenwatch/config.ini`

```ini
[DEFAULT]
# Command to execute when screen is connected/disconnected
command = autorandr -c

# Comma-separated list of desktop environments to exclude
excluded_desktops = COSMIC,GNOME,KDE,Plasma,XFCE,X-Cinnamon

# Debounce delay in seconds
debounce_delay = 2.0

# Log level: DEBUG, INFO, WARNING, ERROR
log_level = INFO
```

### Using a Wrapper Script (Recommended)

For better control over the environment and additional functionality, use a wrapper script:

1. Copy the example script:
```bash
cp screenwatch-handler.sh.example ~/.local/bin/screenwatch-handler.sh
chmod +x ~/.local/bin/screenwatch-handler.sh
```

2. Edit your config to use the script:
```ini
command = /home/youruser/.local/bin/screenwatch-handler.sh
```

The wrapper script can:
- Ensure `DISPLAY` and `XAUTHORITY` are set correctly
- Add logging for debugging
- Run additional commands (restore wallpaper, restart compositor, etc.)
- Handle errors gracefully

### Customization Examples

**Use a wrapper script (recommended):**
```ini
command = /home/youruser/.local/bin/screenwatch-handler.sh
```

**Use a different command:**
```ini
command = /home/user/bin/my-screen-script.sh
```

**Reduce exclusions** (e.g., to use with XFCE):
```ini
excluded_desktops = COSMIC,GNOME,KDE,Plasma
```

**Enable debug logging:**
```ini
log_level = DEBUG
```

## Usage

### Makefile Commands

```bash
make install          # Install everything
make install-deps     # Install Python package only
make install-service  # Install systemd service only
make uninstall        # Remove package and service

make enable           # Enable service (auto-start on login)
make disable          # Disable service
make start            # Start service now
make stop             # Stop service
make restart          # Restart service
make status           # Show service status
make logs             # Show live service logs

make clean            # Remove build artifacts
```

### Manual Service Control

```bash
# Enable service
systemctl --user enable screenwatch.service

# Start service
systemctl --user start screenwatch.service

# Check status
systemctl --user status screenwatch.service

# View logs
journalctl --user -u screenwatch.service -f
```

## How It Works

1. The service monitors the `drm` subsystem in udev for device events
2. When a display is connected, disconnected, or changed, udev emits an event
3. The service detects the event and checks the current desktop environment
4. If the desktop is not in the exclusion list, it waits for the debounce delay
5. After the delay, it executes the configured command
6. The command (e.g., `autorandr -c`) reconfigures displays automatically

## Desktop Environment Exclusions

By default, screenwatch skips execution on these desktop environments:

- **COSMIC** - System76's COSMIC desktop
- **GNOME** - GNOME desktop environment
- **KDE/Plasma** - KDE Plasma desktop
- **XFCE** - XFCE desktop environment
- **X-Cinnamon** - Linux Mint's Cinnamon desktop

These DEs have built-in display management that conflicts with external tools like autorandr.

## Troubleshooting

### Service not starting

Check status and logs:
```bash
make status
make logs
```

### Command not executing

1. Verify your desktop is not excluded: `echo $XDG_CURRENT_DESKTOP`
2. Check logs for exclusion messages: `make logs`
3. Enable debug logging in config: `log_level = DEBUG`

### autorandr not working / DISPLAY issues

If autorandr fails with "Can't open display" errors:

1. Use the wrapper script (see "Using a Wrapper Script" above)
2. The script handles DISPLAY detection automatically
3. Check the wrapper script's log: `~/.local/share/screenwatch/screenwatch-handler.log`

### Permission issues

The service runs as your user and should have access to udev. If you encounter permission issues, check that your user is in the appropriate groups:
```bash
groups
```

## Uninstallation

```bash
make uninstall
```

This removes the package and service but keeps your configuration file in `~/.config/screenwatch/`.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.
