#!/usr/bin/env python3
"""
GUI Management Module

This module handles desktop GUI configuration for Jetson devices,
including enabling/disabling the desktop environment on boot.
"""

import subprocess
from typing import Dict, Optional, Any


class GUIManager:
    """Manager for GUI operations on Jetson devices."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GUIManager.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
    
    def get_gui_status(self) -> Dict[str, Any]:
        """Get current GUI configuration status.
        
        Returns:
            Dictionary containing GUI status information
        """
        try:
            # Get current default target
            result = subprocess.run(['systemctl', 'get-default'], 
                                 capture_output=True, text=True, check=True)
            
            current_target = result.stdout.strip()
            
            # Determine GUI status
            if 'graphical.target' in current_target:
                gui_enabled = True
                status_message = "Desktop GUI is enabled on boot"
            elif 'multi-user.target' in current_target:
                gui_enabled = False
                status_message = "Desktop GUI is disabled on boot (console mode)"
            else:
                gui_enabled = None
                status_message = f"Unknown target: {current_target}"
            
            # Check if GUI is currently running
            gui_running = self._is_gui_currently_running()
            
            return {
                'status': 'success',
                'gui_enabled_on_boot': gui_enabled,
                'gui_currently_running': gui_running,
                'current_target': current_target,
                'message': status_message
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to get GUI status: {e}'
            }
    
    def enable_gui(self, interactive: bool = True) -> Dict[str, Any]:
        """Enable desktop GUI on boot.
        
        Args:
            interactive: Whether to ask for confirmation
            
        Returns:
            Dictionary containing operation results
        """
        try:
            # Check current status
            current_status = self.get_gui_status()
            if current_status['status'] != 'success':
                return current_status
            
            if current_status['gui_enabled_on_boot']:
                return {
                    'status': 'info',
                    'message': 'Desktop GUI is already enabled on boot'
                }
            
            if interactive:
                print("This will enable the desktop GUI on boot.")
                print("The system will start in graphical mode after reboot.")
                confirm = input("Continue? (y/N): ").lower()
                if confirm not in ['y', 'yes']:
                    return {
                        'status': 'cancelled',
                        'message': 'GUI enable operation cancelled by user'
                    }
            
            # Set graphical target as default
            result = subprocess.run(['systemctl', 'set-default', 'graphical.target'], 
                                 capture_output=True, text=True, check=True)
            
            # Verify the change
            verification = self.get_gui_status()
            if verification['status'] == 'success' and verification['gui_enabled_on_boot']:
                return {
                    'status': 'success',
                    'message': 'Desktop GUI enabled on boot. Reboot to take effect.',
                    'action_required': 'reboot'
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'GUI enable command executed but verification failed'
                }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to enable GUI: {e}'
            }
    
    def disable_gui(self, interactive: bool = True) -> Dict[str, Any]:
        """Disable desktop GUI on boot (console mode).
        
        Args:
            interactive: Whether to ask for confirmation
            
        Returns:
            Dictionary containing operation results
        """
        try:
            # Check current status
            current_status = self.get_gui_status()
            if current_status['status'] != 'success':
                return current_status
            
            if not current_status['gui_enabled_on_boot']:
                return {
                    'status': 'info',
                    'message': 'Desktop GUI is already disabled on boot'
                }
            
            if interactive:
                print("This will disable the desktop GUI on boot.")
                print("The system will start in console mode after reboot.")
                confirm = input("Continue? (y/N): ").lower()
                if confirm not in ['y', 'yes']:
                    return {
                        'status': 'cancelled',
                        'message': 'GUI disable operation cancelled by user'
                    }
            
            # Set multi-user target as default
            result = subprocess.run(['systemctl', 'set-default', 'multi-user.target'], 
                                 capture_output=True, text=True, check=True)
            
            # Verify the change
            verification = self.get_gui_status()
            if verification['status'] == 'success' and not verification['gui_enabled_on_boot']:
                return {
                    'status': 'success',
                    'message': 'Desktop GUI disabled on boot. Reboot to take effect.',
                    'action_required': 'reboot'
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'GUI disable command executed but verification failed'
                }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to disable GUI: {e}'
            }
    
    def set_gui_state(self, enable: bool, interactive: bool = True) -> Dict[str, Any]:
        """Set GUI state (enable or disable).
        
        Args:
            enable: True to enable GUI, False to disable
            interactive: Whether to ask for confirmation
            
        Returns:
            Dictionary containing operation results
        """
        if enable:
            return self.enable_gui(interactive=interactive)
        else:
            return self.disable_gui(interactive=interactive)
    
    def start_gui_session(self) -> Dict[str, Any]:
        """Start GUI session immediately (without changing boot configuration).
        
        Returns:
            Dictionary containing operation results
        """
        try:
            # Check if GUI is already running
            if self._is_gui_currently_running():
                return {
                    'status': 'info',
                    'message': 'GUI session is already running'
                }
            
            # Try to start GUI session
            result = subprocess.run(['systemctl', 'start', 'graphical.target'], 
                                 capture_output=True, text=True, check=True)
            
            return {
                'status': 'success',
                'message': 'GUI session started successfully'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to start GUI session: {e}'
            }
    
    def stop_gui_session(self) -> Dict[str, Any]:
        """Stop GUI session immediately (without changing boot configuration).
        
        Returns:
            Dictionary containing operation results
        """
        try:
            # Check if GUI is running
            if not self._is_gui_currently_running():
                return {
                    'status': 'info',
                    'message': 'GUI session is not currently running'
                }
            
            # Stop GUI session
            result = subprocess.run(['systemctl', 'isolate', 'multi-user.target'], 
                                 capture_output=True, text=True, check=True)
            
            return {
                'status': 'success',
                'message': 'GUI session stopped successfully'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to stop GUI session: {e}'
            }
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get display and X server information.
        
        Returns:
            Dictionary containing display information
        """
        info = {
            'display_available': False,
            'x_server_running': False,
            'displays': []
        }
        
        try:
            # Check for X server
            try:
                result = subprocess.run(['pgrep', '-f', 'Xorg'], 
                                     capture_output=True, text=True, check=False)
                info['x_server_running'] = result.returncode == 0
            except subprocess.CalledProcessError:
                pass
            
            # Check for displays using xrandr if available
            try:
                result = subprocess.run(['xrandr', '--query'], 
                                     capture_output=True, text=True, check=True)
                
                info['display_available'] = True
                
                # Parse xrandr output for display information
                for line in result.stdout.split('\n'):
                    if ' connected' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            display_name = parts[0]
                            status = parts[1]
                            resolution = parts[2] if len(parts) > 2 else 'unknown'
                            
                            info['displays'].append({
                                'name': display_name,
                                'status': status,
                                'resolution': resolution
                            })
                
                info['xrandr_output'] = result.stdout
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                # xrandr not available or no display
                pass
            
            # Check for Wayland
            try:
                wayland_display = subprocess.run(['echo', '$WAYLAND_DISPLAY'], 
                                               capture_output=True, text=True, shell=True)
                info['wayland_display'] = wayland_display.stdout.strip()
            except subprocess.CalledProcessError:
                pass
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def get_desktop_environment_info(self) -> Dict[str, Any]:
        """Get information about the desktop environment.
        
        Returns:
            Dictionary containing desktop environment information
        """
        info = {
            'desktop_session': None,
            'window_manager': None,
            'available_sessions': []
        }
        
        try:
            # Get current desktop session
            desktop_session = subprocess.run(['echo', '$DESKTOP_SESSION'], 
                                          capture_output=True, text=True, shell=True)
            info['desktop_session'] = desktop_session.stdout.strip()
            
            # Get XDG current desktop
            xdg_desktop = subprocess.run(['echo', '$XDG_CURRENT_DESKTOP'], 
                                      capture_output=True, text=True, shell=True)
            info['xdg_current_desktop'] = xdg_desktop.stdout.strip()
            
            # Check for available desktop sessions
            import os
            from pathlib import Path
            
            session_dirs = [
                Path('/usr/share/xsessions'),
                Path('/usr/share/wayland-sessions')
            ]
            
            for session_dir in session_dirs:
                if session_dir.exists():
                    for session_file in session_dir.glob('*.desktop'):
                        info['available_sessions'].append(session_file.stem)
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def _is_gui_currently_running(self) -> bool:
        """Check if GUI is currently running."""
        try:
            # Check for graphical session
            result = subprocess.run(['systemctl', 'is-active', 'graphical-session.target'], 
                                 capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                return True
            
            # Alternative check: look for X server or display manager
            x_processes = ['Xorg', 'gdm', 'lightdm', 'sddm', 'xdm']
            for process in x_processes:
                result = subprocess.run(['pgrep', '-f', process], 
                                     capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    return True
            
            return False
            
        except subprocess.CalledProcessError:
            return False
    
    def configure_gui(self, enable: bool, 
                     interactive: bool = True) -> Dict[str, Any]:
        """Configure GUI with comprehensive setup.
        
        Args:
            enable: True to enable GUI, False to disable
            interactive: Whether to run in interactive mode
            
        Returns:
            Dictionary containing configuration results
        """
        try:
            # Get current status
            status = self.get_gui_status()
            if status['status'] != 'success':
                return status
            
            if interactive:
                print("=== GUI Configuration ===")
                print(f"Current status: {status['message']}")
                print(f"GUI currently running: {status['gui_currently_running']}")
                
                action = "enable" if enable else "disable"
                print(f"\nRequested action: {action} GUI on boot")
            
            # Perform the configuration
            result = self.set_gui_state(enable, interactive=interactive)
            
            if result['status'] == 'success' and interactive:
                print("\n✅ GUI configuration completed successfully")
                if result.get('action_required') == 'reboot':
                    print("⚠️ Reboot required for changes to take effect")
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'GUI configuration failed: {e}'
            }