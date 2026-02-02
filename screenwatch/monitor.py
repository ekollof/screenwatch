#!/usr/bin/env python3
"""Monitor udev for screen connection/disconnection events."""

import os
import sys
import time
import logging
import subprocess
import configparser
from pathlib import Path
from threading import Timer
import pyudev


class ScreenMonitor:
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.debounce_timer = None
        self.last_event_time = 0
        
    def _load_config(self, config_path=None):
        """Load configuration from file."""
        config = configparser.ConfigParser()
        
        # Set defaults
        config['DEFAULT'] = {
            'command': 'autorandr -c',
            'excluded_desktops': 'COSMIC,GNOME,KDE,Plasma,XFCE,X-Cinnamon',
            'debounce_delay': '2.0',
            'log_level': 'INFO'
        }
        
        # Try to load from config file
        config_locations = []
        if config_path:
            config_locations.append(Path(config_path))
        
        config_locations.extend([
            Path.home() / '.config' / 'screenwatch' / 'config.ini',
            Path('/etc/screenwatch/config.ini')
        ])
        
        for location in config_locations:
            if location.exists():
                config.read(location)
                break
                
        return config
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = self.config['DEFAULT'].get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('screenwatch')
    
    def _get_desktop_environment(self):
        """Detect the current desktop environment."""
        # Check various environment variables
        for var in ['XDG_CURRENT_DESKTOP', 'XDG_SESSION_DESKTOP', 'DESKTOP_SESSION']:
            desktop = os.environ.get(var, '').strip()
            if desktop:
                self.logger.debug(f"Detected desktop environment from {var}: {desktop}")
                return desktop
        
        self.logger.debug("No desktop environment detected")
        return None
    
    def _is_desktop_excluded(self):
        """Check if current desktop environment is in exclusion list."""
        desktop = self._get_desktop_environment()
        if not desktop:
            return False
        
        excluded = self.config['DEFAULT'].get('excluded_desktops', '').split(',')
        excluded = [d.strip().lower() for d in excluded if d.strip()]
        
        desktop_lower = desktop.lower()
        
        # Check if any excluded desktop matches
        for excluded_de in excluded:
            if excluded_de in desktop_lower or desktop_lower in excluded_de:
                self.logger.info(f"Desktop environment '{desktop}' is excluded, not running command")
                return True
        
        return False
    
    def _execute_command(self):
        """Execute the configured command."""
        if self._is_desktop_excluded():
            return
        
        command = self.config['DEFAULT'].get('command', 'autorandr -c')
        self.logger.info(f"Executing command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(f"Command executed successfully")
                if result.stdout:
                    self.logger.debug(f"Output: {result.stdout}")
            else:
                self.logger.warning(f"Command failed with return code {result.returncode}")
                if result.stderr:
                    self.logger.warning(f"Error: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            self.logger.error("Command execution timed out")
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
    
    def _debounced_execute(self):
        """Execute command with debouncing to avoid rapid repeated calls."""
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        delay = float(self.config['DEFAULT'].get('debounce_delay', '2.0'))
        
        def execute_with_wait():
            self._wait_for_displays_ready()
            self._execute_command()
        
        self.debounce_timer = Timer(delay, execute_with_wait)
        self.debounce_timer.start()
    
    def _wait_for_displays_ready(self):
        """Wait until displays are actually detected by X11/Wayland."""
        import time
        max_wait = 5.0  # Maximum wait time in seconds
        check_interval = 0.2  # Check every 200ms
        waited = 0.0
        
        self.logger.debug("Waiting for displays to be ready...")
        
        # Give the kernel/X11 time to detect and register displays
        time.sleep(1.0)
        waited += 1.0
        
        # Check if we can detect display connectors in a ready state
        context = pyudev.Context()
        while waited < max_wait:
            # Count connected displays
            connected = 0
            for device in context.list_devices(subsystem='drm'):
                # Check for connector devices with connected status
                if 'card' in device.sys_name and 'status' in device.attributes.available_attributes:
                    try:
                        status = device.attributes.asstring('status')
                        if status == 'connected':
                            connected += 1
                    except:
                        pass
            
            if connected > 0:
                self.logger.debug(f"Detected {connected} connected display(s) after {waited:.1f}s")
                return True
            
            time.sleep(check_interval)
            waited += check_interval
        
        self.logger.debug(f"Finished waiting after {waited:.1f}s")
        return True
    
    def _handle_device_event(self, device):
        """Handle udev device event."""
        if device.action in ['change', 'add', 'remove']:
            # Only process connector events or card changes
            if 'card' in device.sys_name or device.device_type == 'drm_minor':
                self.logger.debug(
                    f"Device event: {device.action} on {device.sys_name}"
                )
                self._debounced_execute()
    
    def monitor(self):
        """Start monitoring udev events."""
        if self._is_desktop_excluded():
            self.logger.info("Desktop environment is excluded, exiting")
            return 0
        
        self.logger.info("Starting screen monitor")
        self.logger.info(f"Command to execute: {self.config['DEFAULT'].get('command')}")
        
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        
        # Monitor DRM subsystem for display events
        monitor.filter_by(subsystem='drm')
        
        self.logger.info("Monitoring for screen connection/disconnection events...")
        
        try:
            for device in iter(monitor.poll, None):
                self._handle_device_event(device)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt, shutting down")
            if self.debounce_timer:
                self.debounce_timer.cancel()
            return 0
        except Exception as e:
            self.logger.error(f"Error in monitor loop: {e}")
            return 1


def main():
    """Main entry point."""
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    monitor = ScreenMonitor(config_path)
    return monitor.monitor()


if __name__ == '__main__':
    sys.exit(main())
