#!/usr/bin/env python3
"""
System Management Module

This module handles system-wide operations including probing system information,
creating environment profiles, and managing system configuration.
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil
import yaml

from ..utils import get_jetson_info, check_jetson_platform, format_size


class SystemManager:
    """Manager for system-wide Jetson operations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize SystemManager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment."""
        config = {}
        
        # Try to load from .env file first
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        # Override with environment variables
        config.update(os.environ)
        
        return config
    
    def probe_system(self, tests: Optional[List[str]] = None) -> Dict[str, Any]:
        """Probe and analyze the Jetson system configuration.
        
        Args:
            tests: Specific tests to run. If None, runs all tests.
            
        Returns:
            Dictionary containing system probe results
        """
        results = {
            'platform': self._get_platform_info(),
            'system': self._get_system_info(),
            'jetson': self._get_jetson_specific_info(),
            'checks': {}
        }
        
        # Define available checks
        available_checks = {
            'docker_installed': self._check_docker_installed,
            'nvme_mount': self._check_nvme_mount,
            'docker_runtime': self._check_docker_runtime,
            'docker_root': self._check_docker_root,
            'swap_file': self._check_swap_file,
            'disable_zram': self._check_zram,
            'nvzramconfig_service': self._check_nvzramconfig_service,
            'gui': self._check_gui,
            'docker_group': self._check_docker_group,
            'power_mode': self._check_power_mode,
            'prepare_nvme_partition': self._check_nvme_partition_prepared,
            'assign_nvme_drive': self._check_nvme_drive_assigned
        }
        
        # Run specified tests or all tests
        tests_to_run = tests if tests else available_checks.keys()
        
        for test in tests_to_run:
            if test in available_checks:
                try:
                    results['checks'][test] = available_checks[test]()
                except Exception as e:
                    results['checks'][test] = {
                        'status': 'error',
                        'message': f"Error running check: {str(e)}"
                    }
            else:
                results['checks'][test] = {
                    'status': 'error',
                    'message': f"Unknown test: {test}"
                }
        
        return results
    
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get basic platform information."""
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'is_jetson': check_jetson_platform()
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system resource information."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_count': psutil.cpu_count(),
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'total_formatted': format_size(memory.total),
                'available_formatted': format_size(memory.available)
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100,
                'total_formatted': format_size(disk.total),
                'used_formatted': format_size(disk.used),
                'free_formatted': format_size(disk.free)
            },
            'boot_time': psutil.boot_time()
        }
    
    def _get_jetson_specific_info(self) -> Dict[str, Any]:
        """Get Jetson-specific information."""
        if not check_jetson_platform():
            return {'available': False}
        
        jetson_info = get_jetson_info()
        
        # Add additional Jetson-specific checks
        try:
            # Check for Jetson model from device tree
            model_file = Path('/proc/device-tree/model')
            if model_file.exists():
                with open(model_file, 'r') as f:
                    jetson_info['model'] = f.read().strip().replace('\x00', '')
        except Exception:
            pass
        
        try:
            # Check JetPack version
            jetpack_file = Path('/etc/nv_tegra_release')
            if jetpack_file.exists():
                with open(jetpack_file, 'r') as f:
                    jetson_info['jetpack_info'] = f.read().strip()
        except Exception:
            pass
        
        jetson_info['available'] = True
        return jetson_info
    
    def _check_docker_installed(self) -> Dict[str, Any]:
        """Check if Docker is installed."""
        try:
            result = subprocess.run(['docker', '--version'], 
                                 capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'message': 'Docker is installed',
                    'version': result.stdout.strip()
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Docker is not installed'
                }
        except FileNotFoundError:
            return {
                'status': 'warning', 
                'message': 'Docker is not installed'
            }
    
    def _check_nvme_mount(self) -> Dict[str, Any]:
        """Check if NVMe is mounted."""
        mount_point = self.config.get('NVME_SETUP_OPTIONS_MOUNT_POINT')
        partition_name = self.config.get('NVME_SETUP_OPTIONS_PARTITION_NAME')
        
        if not mount_point or not partition_name:
            return {
                'status': 'info',
                'message': 'NVMe is not configured in environment file'
            }
        
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True, check=True)
            mount_pattern = f"/dev/{partition_name} on {mount_point}"
            
            if mount_pattern in result.stdout:
                return {
                    'status': 'success',
                    'message': f'NVMe is mounted on {mount_point}'
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'NVMe is not mounted on {mount_point}'
                }
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking mount: {e}'
            }
    
    def _check_docker_runtime(self) -> Dict[str, Any]:
        """Check Docker runtime configuration."""
        daemon_file = Path('/etc/docker/daemon.json')
        
        if not daemon_file.exists():
            return {
                'status': 'warning',
                'message': 'Docker daemon.json file does not exist'
            }
        
        try:
            with open(daemon_file, 'r') as f:
                daemon_config = json.load(f)
            
            if daemon_config.get('default-runtime') == 'nvidia':
                return {
                    'status': 'success',
                    'message': 'Docker runtime nvidia is set as default'
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Docker runtime nvidia is not set as default'
                }
        except (json.JSONDecodeError, IOError) as e:
            return {
                'status': 'error',
                'message': f'Error reading daemon.json: {e}'
            }
    
    def _check_docker_root(self) -> Dict[str, Any]:
        """Check Docker data root configuration."""
        daemon_file = Path('/etc/docker/daemon.json')
        docker_root_path = self.config.get('DOCKER_ROOT_OPTIONS_PATH')
        
        if not docker_root_path:
            return {
                'status': 'info',
                'message': 'Docker root path is not specified in environment file'
            }
        
        if not daemon_file.exists():
            return {
                'status': 'warning',
                'message': 'Docker daemon.json file does not exist'
            }
        
        try:
            with open(daemon_file, 'r') as f:
                daemon_config = json.load(f)
            
            if daemon_config.get('data-root') == docker_root_path:
                return {
                    'status': 'success',
                    'message': f'Docker data root is set to {docker_root_path}'
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'Docker data root is not set to {docker_root_path}'
                }
        except (json.JSONDecodeError, IOError) as e:
            return {
                'status': 'error',
                'message': f'Error reading daemon.json: {e}'
            }
    
    def _check_swap_file(self) -> Dict[str, Any]:
        """Check swap file configuration."""
        swap_file = self.config.get('SWAP_OPTIONS_PATH')
        
        try:
            result = subprocess.run(['swapon', '--show'], 
                                 capture_output=True, text=True, check=True)
            
            # Parse all active swap devices
            active_swaps = []
            total_swap_size = 0
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        swap_device = parts[0]
                        swap_type = parts[1]
                        swap_size = parts[2]
                        active_swaps.append({
                            'device': swap_device,
                            'type': swap_type,
                            'size': swap_size
                        })
                        
                        # Try to parse size for total calculation
                        try:
                            if swap_size.endswith('G'):
                                total_swap_size += float(swap_size[:-1]) * 1024**3
                            elif swap_size.endswith('M'):
                                total_swap_size += float(swap_size[:-1]) * 1024**2
                        except ValueError:
                            pass
            
            if not swap_file:
                # No specific swap file configured, report all active swap
                if active_swaps:
                    swap_summary = ", ".join([f"{s['device']} ({s['size']})" for s in active_swaps])
                    return {
                        'status': 'info',
                        'message': f'Swap is active: {swap_summary}',
                        'details': f'Total active swap devices: {len(active_swaps)}'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': 'No swap is configured'
                    }
            
            # Check for specific configured swap file
            if any(swap_file in swap['device'] for swap in active_swaps):
                matching_swap = next(swap for swap in active_swaps if swap_file in swap['device'])
                return {
                    'status': 'success',
                    'message': f'Configured swap file is active at {swap_file} ({matching_swap["size"]})'
                }
            else:
                # Configured swap file not found, but other swap may be active
                if active_swaps:
                    other_swaps = ", ".join([f"{s['device']} ({s['size']})" for s in active_swaps])
                    return {
                        'status': 'warning',
                        'message': f'Configured swap file {swap_file} not found, but other swap is active: {other_swaps}'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'Configured swap file {swap_file} not found and no swap is active'
                    }
                    
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking swap: {e}'
            }
    
    def _check_zram(self) -> Dict[str, Any]:
        """Check zRAM configuration."""
        disable_zram = self.config.get('SWAP_OPTIONS_DISABLE_ZRAM', '').lower() == 'true'
        
        try:
            # Check nvzramconfig service status
            service_result = subprocess.run(['systemctl', 'is-enabled', 'nvzramconfig'],
                                         capture_output=True, text=True, check=False)
            service_enabled = service_result.returncode == 0
            
            # Check for active zram devices
            result = subprocess.run(['swapon', '--show'], 
                                 capture_output=True, text=True, check=True)
            
            zram_devices = []
            for line in result.stdout.split('\n'):
                if 'zram' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        zram_devices.append({
                            'device': parts[0],
                            'size': parts[2]
                        })
            
            # Determine status based on configuration
            if disable_zram:
                # Configuration wants zRAM disabled
                if not service_enabled and not zram_devices:
                    return {
                        'status': 'success',
                        'message': 'zRAM is disabled as configured'
                    }
                elif service_enabled and zram_devices:
                    zram_summary = ", ".join([f"{z['device']} ({z['size']})" for z in zram_devices])
                    return {
                        'status': 'warning',
                        'message': f'Configuration expects zRAM disabled, but it is enabled',
                        'details': f'Active zRAM devices: {zram_summary}'
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'zRAM configuration partially matches expectation (service enabled: {service_enabled}, devices active: {len(zram_devices)})'
                    }
            else:
                # Configuration wants zRAM enabled or not specified
                if service_enabled and zram_devices:
                    zram_summary = ", ".join([f"{z['device']} ({z['size']})" for z in zram_devices])
                    return {
                        'status': 'success',
                        'message': f'zRAM is enabled with {len(zram_devices)} devices: {zram_summary}'
                    }
                else:
                    return {
                        'status': 'info',
                        'message': f'zRAM status: service enabled = {service_enabled}, active devices = {len(zram_devices)}'
                    }
                    
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking zRAM: {e}'
            }
    
    def _check_nvzramconfig_service(self) -> Dict[str, Any]:
        """Check nvzramconfig service status."""
        try:
            # Check if service is installed
            list_result = subprocess.run(['systemctl', 'list-unit-files'],
                                      capture_output=True, text=True, check=True)
            
            if 'nvzramconfig.service' in list_result.stdout:
                # Check if service is enabled
                enabled_result = subprocess.run(['systemctl', 'is-enabled', 'nvzramconfig.service'],
                                             capture_output=True, text=True, check=False)
                
                if enabled_result.returncode == 0:
                    return {
                        'status': 'warning',
                        'message': "Service 'nvzramconfig' is enabled"
                    }
                else:
                    return {
                        'status': 'success',
                        'message': "Service 'nvzramconfig' is disabled"
                    }
            else:
                return {
                    'status': 'warning',
                    'message': "Service 'nvzramconfig' is not installed"
                }
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking nvzramconfig service: {e}'
            }
    
    def _check_gui(self) -> Dict[str, Any]:
        """Check GUI configuration."""
        try:
            result = subprocess.run(['systemctl', 'get-default'],
                                 capture_output=True, text=True, check=True)
            
            if 'multi-user.target' in result.stdout:
                return {
                    'status': 'success',
                    'message': 'Desktop GUI is disabled on boot'
                }
            else:
                return {
                    'status': 'info',
                    'message': 'Desktop GUI is enabled on boot'
                }
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking GUI configuration: {e}'
            }
    
    def _check_docker_group(self) -> Dict[str, Any]:
        """Check Docker group membership."""
        add_user = self.config.get('DOCKER_GROUP_OPTIONS_ADD_USER')
        current_user = os.getenv('USER', 'unknown')
        results = []
        
        # Check configured user from .env if provided
        if add_user:
            try:
                result = subprocess.run(['groups', add_user],
                                     capture_output=True, text=True, check=True)
                if 'docker' in result.stdout.split():
                    results.append(f"User {add_user} is in the docker group")
                else:
                    results.append(f"User {add_user} is not in the docker group")
            except subprocess.CalledProcessError:
                results.append(f"User {add_user} not found")
        
        # Check current user if different from configured user
        if not add_user or current_user != add_user:
            try:
                result = subprocess.run(['groups', current_user],
                                     capture_output=True, text=True, check=True)
                if 'docker' in result.stdout.split():
                    results.append(f"Current user {current_user} is in the docker group")
                else:
                    results.append(f"Current user {current_user} is not in the docker group")
            except subprocess.CalledProcessError:
                results.append(f"Current user {current_user} not found")
        
        # Determine overall status
        if any('not in the docker group' in r for r in results):
            status = 'warning'
        else:
            status = 'success'
        
        return {
            'status': status,
            'message': '; '.join(results)
        }
    
    def _check_power_mode(self) -> Dict[str, Any]:
        """Check current power mode."""
        try:
            result = subprocess.run(['nvpmodel', '-q'],
                                 capture_output=True, text=True, check=True)
            
            # Parse the output to extract power mode
            for line in result.stdout.split('\n'):
                if 'NV Power Mode' in line:
                    mode = line.split(':')[1].strip()
                    return {
                        'status': 'info',
                        'message': f'Current power mode: {mode}'
                    }
            
            return {
                'status': 'info',
                'message': 'Power mode information not found'
            }
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return {
                'status': 'error',
                'message': f'Error checking power mode: {e}'
            }
    
    def _check_nvme_partition_prepared(self) -> Dict[str, Any]:
        """Check if NVMe partition is prepared."""
        partition_name = self.config.get('NVME_SETUP_OPTIONS_PARTITION_NAME')
        filesystem = self.config.get('NVME_SETUP_OPTIONS_FILESYSTEM')
        
        if not partition_name or not filesystem:
            return {
                'status': 'info',
                'message': 'NVMe is not configured in environment file'
            }
        
        partition_path = f"/dev/{partition_name}"
        
        # Check if partition exists
        if not Path(partition_path).exists():
            return {
                'status': 'warning',
                'message': f'NVMe partition {partition_path} does not exist'
            }
        
        try:
            # Check filesystem type
            result = subprocess.run(['blkid', partition_path],
                                 capture_output=True, text=True, check=True)
            
            if filesystem.lower() in result.stdout.lower():
                return {
                    'status': 'success',
                    'message': 'NVMe partition is prepared'
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'NVMe partition filesystem does not match expected {filesystem}'
                }
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking NVMe partition: {e}'
            }
    
    def _check_nvme_drive_assigned(self) -> Dict[str, Any]:
        """Check if NVMe drive is assigned/mounted."""
        mount_point = self.config.get('NVME_SETUP_OPTIONS_MOUNT_POINT')
        partition_name = self.config.get('NVME_SETUP_OPTIONS_PARTITION_NAME')
        
        if not mount_point or not partition_name:
            return {
                'status': 'info',
                'message': 'NVMe is not configured in environment file'
            }
        
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True, check=True)
            mount_pattern = f"/dev/{partition_name} on {mount_point}"
            
            if mount_pattern in result.stdout:
                return {
                    'status': 'success',
                    'message': 'NVMe drive is already assigned/mounted'
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'NVMe drive is not assigned/mounted'
                }
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Error checking NVMe assignment: {e}'
            }
    
    def create_env_profile(self, profile_name: str = "jetson-dev", 
                          force: bool = False) -> Dict[str, Any]:
        """Create an environment profile for Jetson development.
        
        Args:
            profile_name: Name for the environment profile
            force: Force recreate existing profile
            
        Returns:
            Dictionary containing creation results
        """
        env_file = Path('.env')
        
        if env_file.exists() and not force:
            return {
                'status': 'warning',
                'message': f'Environment profile already exists. Use force=True to recreate.'
            }
        
        try:
            # Get system information for profile creation
            jetson_info = get_jetson_info()
            
            # Detect current swap configuration
            current_swap_file = "/swapfile"  # default
            current_swap_size = "8G"  # default
            disable_zram = "false"  # default is to keep zRAM enabled
            
            try:
                import subprocess
                result = subprocess.run(['swapon', '--show'], capture_output=True, text=True, check=True)
                # Find the largest swap file (not zram)
                for line in result.stdout.split('\n')[1:]:
                    if line.strip() and 'zram' not in line and 'file' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            current_swap_file = parts[0]
                            current_swap_size = parts[2]
                            break
                
                # Check if zRAM is active (keep current state as default)
                zram_active = any('zram' in line for line in result.stdout.split('\n'))
                disable_zram = "false" if zram_active else "true"
            except subprocess.CalledProcessError:
                pass
            
            # Create environment profile content
            env_content = f"""# Jetson Development Environment Profile: {profile_name}
# Generated by jetson-cli
# Date: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

# Platform Information
JETSON_PLATFORM={jetson_info.get('platform', 'Unknown')}
JETSON_L4T_VERSION={jetson_info.get('l4t_version', 'Unknown')}
JETSON_CUDA_VERSION={jetson_info.get('cuda_version', 'Unknown')}

# Docker Configuration
DOCKER_ROOT_OPTIONS_PATH=/mnt/nvme/docker
DOCKER_GROUP_OPTIONS_ADD_USER={os.getenv('USER', 'jetson')}

# Storage Configuration  
NVME_SETUP_OPTIONS_MOUNT_POINT=/mnt/nvme
NVME_SETUP_OPTIONS_PARTITION_NAME=nvme0n1p1
NVME_SETUP_OPTIONS_FILESYSTEM=ext4

# Swap Configuration (detected current state)
SWAP_OPTIONS_PATH={current_swap_file}
SWAP_OPTIONS_SIZE={current_swap_size}
SWAP_OPTIONS_DISABLE_ZRAM={disable_zram}

# Power Configuration
POWER_MODE_OPTIONS_MODE=0

# Development Environment
PROFILE_NAME={profile_name}
JETSON_CLI_VERSION={getattr(sys.modules.get('jetson_cli'), '__version__', 'unknown')}
"""
            
            # Write environment file
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            return {
                'status': 'success',
                'message': f'Environment profile "{profile_name}" created successfully',
                'profile_path': str(env_file.absolute()),
                'detected_config': {
                    'swap_file': current_swap_file,
                    'swap_size': current_swap_size,
                    'zram_enabled': disable_zram == "false"
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error creating environment profile: {e}'
            }
    
    def format_probe_results(self, results: Dict[str, Any], 
                           output_format: str = 'table') -> str:
        """Format probe results for display.
        
        Args:
            results: Probe results from probe_system()
            output_format: Output format ('table', 'json', 'yaml')
            
        Returns:
            Formatted string representation
        """
        if output_format == 'json':
            return json.dumps(results, indent=2)
        elif output_format == 'yaml':
            return yaml.dump(results, default_flow_style=False, indent=2)
        else:
            # Table format (default)
            output = []
            
            # Platform information
            output.append("=== Platform Information ===")
            platform_info = results.get('platform', {})
            for key, value in platform_info.items():
                output.append(f"{key.replace('_', ' ').title()}: {value}")
            
            output.append("\n=== System Information ===")
            system_info = results.get('system', {})
            
            # CPU and Memory
            output.append(f"CPU Count: {system_info.get('cpu_count', 'Unknown')}")
            memory = system_info.get('memory', {})
            output.append(f"Memory: {memory.get('total_formatted', 'Unknown')} total, "
                         f"{memory.get('available_formatted', 'Unknown')} available "
                         f"({memory.get('percent', 0):.1f}% used)")
            
            # Disk
            disk = system_info.get('disk', {})
            output.append(f"Disk: {disk.get('total_formatted', 'Unknown')} total, "
                         f"{disk.get('free_formatted', 'Unknown')} free "
                         f"({disk.get('percent', 0):.1f}% used)")
            
            # Jetson-specific information
            jetson_info = results.get('jetson', {})
            if jetson_info.get('available'):
                output.append("\n=== Jetson Information ===")
                for key, value in jetson_info.items():
                    if key != 'available':
                        output.append(f"{key.replace('_', ' ').title()}: {value}")
            
            # Configuration checks
            checks = results.get('checks', {})
            if checks:
                output.append("\n=== Configuration Checks ===")
                for check_name, check_result in checks.items():
                    status = check_result.get('status', 'unknown')
                    message = check_result.get('message', 'No message')
                    
                    # Format status with colors/symbols
                    if status == 'success':
                        status_symbol = "✅"
                    elif status == 'warning':
                        status_symbol = "⚠️"
                    elif status == 'error':
                        status_symbol = "❌"
                    else:
                        status_symbol = "ℹ️"
                    
                    output.append(f"{status_symbol} {check_name.replace('_', ' ').title()}: {message}")
            
            return "\n".join(output)