#!/usr/bin/env python3
"""
Power Management Module

This module handles Jetson power mode configuration and management.
"""

import subprocess
from typing import Dict, List, Optional, Any


class PowerManager:
    """Manager for Jetson power mode operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PowerManager.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
    
    def get_current_power_mode(self) -> Dict[str, Any]:
        """Get the current power mode.
        
        Returns:
            Dictionary containing current power mode information
        """
        try:
            result = subprocess.run(['nvpmodel', '-q'], 
                                 capture_output=True, text=True, check=True)
            
            # Parse the output to extract power mode information
            mode_info = {
                'mode': 'Unknown',
                'name': 'Unknown',
                'raw_output': result.stdout
            }
            
            for line in result.stdout.split('\n'):
                if 'NV Power Mode' in line:
                    # Extract mode information
                    parts = line.split(':')
                    if len(parts) >= 2:
                        mode_info['name'] = parts[1].strip()
                elif 'NV Fan Mode' in line:
                    # Extract fan mode if available
                    parts = line.split(':')
                    if len(parts) >= 2:
                        mode_info['fan_mode'] = parts[1].strip()
            
            return {
                'status': 'success',
                'mode_info': mode_info
            }
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return {
                'status': 'error',
                'message': f'Failed to get power mode: {e}'
            }
    
    def get_available_power_modes(self) -> Dict[str, Any]:
        """Get list of available power modes.
        
        Returns:
            Dictionary containing available power modes
        """
        try:
            result = subprocess.run(['nvpmodel', '-p', '--verbose'], 
                                 capture_output=True, text=True, check=True)
            
            modes = []
            current_mode = None
            
            # Parse output to extract available modes
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('*'):
                    # Current active mode
                    parts = line[1:].strip().split()
                    if len(parts) >= 2:
                        current_mode = {
                            'id': parts[0],
                            'name': ' '.join(parts[1:]),
                            'active': True
                        }
                        modes.append(current_mode)
                elif line and not line.startswith('NV'):
                    # Other available modes
                    parts = line.split()
                    if len(parts) >= 2:
                        modes.append({
                            'id': parts[0],
                            'name': ' '.join(parts[1:]),
                            'active': False
                        })
            
            return {
                'status': 'success',
                'available_modes': modes,
                'current_mode': current_mode,
                'raw_output': result.stdout
            }
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return {
                'status': 'error',
                'message': f'Failed to get available power modes: {e}'
            }
    
    def set_power_mode(self, mode: str) -> Dict[str, Any]:
        """Set the Jetson power mode.
        
        Args:
            mode: Power mode ID or name to set
            
        Returns:
            Dictionary containing operation results
        """
        try:
            # First, validate that the mode exists
            available_modes = self.get_available_power_modes()
            if available_modes['status'] != 'success':
                return available_modes
            
            valid_modes = available_modes['available_modes']
            mode_found = False
            
            # Check if mode is valid (by ID or name)
            for valid_mode in valid_modes:
                if mode == valid_mode['id'] or mode.lower() in valid_mode['name'].lower():
                    mode = valid_mode['id']  # Use ID for setting
                    mode_found = True
                    break
            
            if not mode_found:
                return {
                    'status': 'error',
                    'message': f'Invalid power mode: {mode}',
                    'available_modes': [f"{m['id']}: {m['name']}" for m in valid_modes]
                }
            
            # Set the power mode
            result = subprocess.run(['nvpmodel', '-m', mode], 
                                 capture_output=True, text=True, check=True)
            
            # Verify the change
            verification = self.get_current_power_mode()
            if verification['status'] == 'success':
                return {
                    'status': 'success',
                    'message': f'Power mode set to: {mode}',
                    'current_mode': verification['mode_info'],
                    'command_output': result.stdout
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'Power mode command executed but verification failed',
                    'command_output': result.stdout
                }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to set power mode: {e}',
                'stderr': e.stderr if hasattr(e, 'stderr') else None
            }
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'nvpmodel command not found. This may not be a Jetson device.'
            }
    
    def get_power_consumption_info(self) -> Dict[str, Any]:
        """Get power consumption information if available.
        
        Returns:
            Dictionary containing power consumption data
        """
        info = {
            'available': False,
            'sensors': []
        }
        
        try:
            # Try to read power monitoring files
            power_paths = [
                '/sys/bus/i2c/drivers/ina3221x',
                '/sys/devices/50000000.host1x/546c0000.i2c/i2c-6/6-0040/iio_device',
                '/sys/devices/3160000.i2c/i2c-0/0-0040/iio_device',
                '/sys/devices/c240000.i2c/i2c-1/1-0040/iio_device'
            ]
            
            # Check for power monitoring capabilities
            import os
            from pathlib import Path
            
            for power_path in power_paths:
                path = Path(power_path)
                if path.exists():
                    info['available'] = True
                    try:
                        # Try to read power values
                        for power_file in path.rglob('*power*'):
                            if power_file.is_file():
                                try:
                                    with open(power_file, 'r') as f:
                                        value = f.read().strip()
                                        info['sensors'].append({
                                            'file': str(power_file),
                                            'value': value
                                        })
                                except (PermissionError, IOError):
                                    pass
                    except Exception:
                        pass
            
            # Try tegrastats for additional power info
            try:
                result = subprocess.run(['tegrastats', '--interval', '1000'], 
                                     timeout=3, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    info['tegrastats_available'] = True
                    info['tegrastats_sample'] = result.stdout
                else:
                    info['tegrastats_available'] = False
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                info['tegrastats_available'] = False
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def get_thermal_info(self) -> Dict[str, Any]:
        """Get thermal information from the system.
        
        Returns:
            Dictionary containing thermal sensor data
        """
        thermal_info = {
            'available': False,
            'zones': []
        }
        
        try:
            from pathlib import Path
            
            # Read thermal zones
            thermal_base = Path('/sys/class/thermal')
            if thermal_base.exists():
                thermal_info['available'] = True
                
                for zone_dir in thermal_base.glob('thermal_zone*'):
                    zone_info = {
                        'zone': zone_dir.name,
                        'type': 'unknown',
                        'temp': None,
                        'temp_celsius': None
                    }
                    
                    # Read zone type
                    type_file = zone_dir / 'type'
                    if type_file.exists():
                        try:
                            with open(type_file, 'r') as f:
                                zone_info['type'] = f.read().strip()
                        except (PermissionError, IOError):
                            pass
                    
                    # Read temperature
                    temp_file = zone_dir / 'temp'
                    if temp_file.exists():
                        try:
                            with open(temp_file, 'r') as f:
                                temp_millicelsius = int(f.read().strip())
                                zone_info['temp'] = temp_millicelsius
                                zone_info['temp_celsius'] = temp_millicelsius / 1000.0
                        except (PermissionError, IOError, ValueError):
                            pass
                    
                    thermal_info['zones'].append(zone_info)
        
        except Exception as e:
            thermal_info['error'] = str(e)
        
        return thermal_info
    
    def configure_power_mode(self, mode: str, 
                           interactive: bool = True) -> Dict[str, Any]:
        """Configure power mode with optional interactive confirmation.
        
        Args:
            mode: Power mode to set
            interactive: Whether to ask for confirmation
            
        Returns:
            Dictionary containing configuration results
        """
        try:
            # Get current mode first
            current = self.get_current_power_mode()
            if current['status'] != 'success':
                return current
            
            current_mode_name = current['mode_info'].get('name', 'Unknown')
            
            # Get available modes for validation and display
            available = self.get_available_power_modes()
            if available['status'] != 'success':
                return available
            
            if interactive:
                print(f"Current power mode: {current_mode_name}")
                print("\nAvailable power modes:")
                for mode_info in available['available_modes']:
                    status = " (current)" if mode_info['active'] else ""
                    print(f"  {mode_info['id']}: {mode_info['name']}{status}")
                
                print(f"\nRequested mode: {mode}")
                confirm = input("Continue with power mode change? (y/N): ").lower()
                if confirm not in ['y', 'yes']:
                    return {
                        'status': 'cancelled',
                        'message': 'Power mode change cancelled by user'
                    }
            
            # Set the power mode
            result = self.set_power_mode(mode)
            
            if result['status'] == 'success':
                print(f"✅ Power mode changed successfully")
                print(f"   Previous: {current_mode_name}")
                print(f"   Current: {result['current_mode']['name']}")
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Power mode configuration failed: {e}'
            }
    
    def get_comprehensive_power_info(self) -> Dict[str, Any]:
        """Get comprehensive power management information.
        
        Returns:
            Dictionary containing all power-related information
        """
        info = {
            'current_mode': self.get_current_power_mode(),
            'available_modes': self.get_available_power_modes(),
            'power_consumption': self.get_power_consumption_info(),
            'thermal': self.get_thermal_info()
        }
        
        return info