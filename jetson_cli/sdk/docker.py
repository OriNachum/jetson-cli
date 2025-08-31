#!/usr/bin/env python3
"""
Docker Management Module

This module handles Docker-related configuration for Jetson devices including
installation, runtime configuration, data directory migration, and group management.
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil

from ..utils import ensure_root


class DockerManager:
    """Manager for Docker operations on Jetson devices."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize DockerManager.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.daemon_json_path = Path('/etc/docker/daemon.json')
        self.docker_lib_path = Path('/var/lib/docker')
    
    def is_docker_installed(self) -> bool:
        """Check if Docker is installed."""
        try:
            result = subprocess.run(['docker', '--version'], 
                                 capture_output=True, text=True, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install_docker(self, interactive: bool = True) -> Dict[str, Any]:
        """Install Docker and NVIDIA container runtime.
        
        Args:
            interactive: Whether to prompt for user confirmation
            
        Returns:
            Dictionary containing installation results
        """
        if self.is_docker_installed():
            return {
                'status': 'info',
                'message': 'Docker is already installed'
            }
        
        if interactive:
            print("⚠️ Docker and NVIDIA container runtime will be installed.")
            print("⚠️ This process requires internet access and may take a few minutes.")
            confirm = input("Are you sure you want to install Docker? (y/N): ").lower()
            if confirm not in ['y', 'yes']:
                return {
                    'status': 'cancelled',
                    'message': 'Installation aborted by user'
                }
        
        try:
            # Use temporary directory for installation
            temp_dir = Path('/tmp/install-docker')
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            # Clone installation repository
            result = subprocess.run([
                'git', 'clone', 
                'https://github.com/jetsonhacks/install-docker.git',
                str(temp_dir)
            ], cwd='/tmp', capture_output=True, text=True, check=True)
            
            # Run installation script
            install_script = temp_dir / 'install_nvidia_docker.sh'
            result = subprocess.run([
                'bash', str(install_script)
            ], cwd=str(temp_dir), capture_output=True, text=True, check=True)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            return {
                'status': 'success',
                'message': 'Docker and NVIDIA runtime installation complete',
                'details': result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Docker installation failed: {e}',
                'details': e.stderr if hasattr(e, 'stderr') else str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error during installation: {e}'
            }
    
    def configure_nvidia_runtime(self) -> Dict[str, Any]:
        """Configure Docker with NVIDIA runtime as default.
        
        Returns:
            Dictionary containing configuration results
        """
        try:
            # Check if already configured
            if self._is_nvidia_runtime_configured():
                return {
                    'status': 'info',
                    'message': 'NVIDIA runtime is already set as default in Docker daemon.json'
                }
            
            # Install jq if not available
            self._ensure_jq_installed()
            
            # Configure NVIDIA runtime
            if self.daemon_json_path.exists():
                # Update existing daemon.json
                result = subprocess.run([
                    'jq', '. + {"default-runtime": "nvidia"}', 
                    str(self.daemon_json_path)
                ], capture_output=True, text=True, check=True)
                
                # Write to temporary file first
                temp_file = self.daemon_json_path.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    f.write(result.stdout)
                
                # Validate JSON before replacing
                self._validate_json(temp_file)
                temp_file.replace(self.daemon_json_path)
            else:
                # Create new daemon.json
                daemon_config = {"default-runtime": "nvidia"}
                with open(self.daemon_json_path, 'w') as f:
                    json.dump(daemon_config, f, indent=2)
            
            # Restart Docker service
            self._restart_docker_service()
            
            return {
                'status': 'success',
                'message': 'NVIDIA runtime is now set as default'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to configure NVIDIA runtime: {e}'
            }
    
    def setup_docker_group(self, user: Optional[str] = None) -> Dict[str, Any]:
        """Add user to docker group.
        
        Args:
            user: Username to add. If None, uses current user.
            
        Returns:
            Dictionary containing setup results
        """
        if user is None:
            user = os.getenv('USER', 'jetson')
        
        try:
            # Check if user is already in docker group
            result = subprocess.run(['groups', user], 
                                 capture_output=True, text=True, check=True)
            
            if 'docker' in result.stdout.split():
                return {
                    'status': 'info',
                    'message': f"User '{user}' is already in the docker group"
                }
            
            # Add user to docker group
            subprocess.run(['usermod', '-aG', 'docker', user], 
                         check=True)
            
            return {
                'status': 'success',
                'message': f"User '{user}' added to docker group. "
                          "Please log out and log back in for changes to take effect.",
                'action_required': 'logout_login'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to add user to docker group: {e}'
            }
    
    def migrate_docker_data(self, target_path: Optional[str] = None, 
                           interactive: bool = True) -> Dict[str, Any]:
        """Migrate Docker data directory to NVMe SSD.
        
        Args:
            target_path: Target directory path. If None, detects NVMe mount points.
            interactive: Whether to prompt user for confirmation
            
        Returns:
            Dictionary containing migration results
        """
        try:
            # Check if L4T is on NVMe (no migration needed)
            if self._is_l4t_on_nvme():
                return {
                    'status': 'info',
                    'message': 'No need to migrate Docker data as your entire system is on NVMe SSD'
                }
            
            # Check if data-root is already configured
            if self._is_data_root_configured():
                return {
                    'status': 'info',
                    'message': 'Docker data-root directory is already configured'
                }
            
            # Find NVMe mount points
            nvme_mount_points = self._get_nvme_mount_points()
            if not nvme_mount_points:
                return {
                    'status': 'error',
                    'message': 'No NVMe mount points found'
                }
            
            # Determine target path
            if target_path is None:
                if interactive:
                    print("Available NVMe mount points:")
                    for i, mp in enumerate(nvme_mount_points):
                        print(f"  {i+1}. {mp}")
                    
                    default_path = f"{nvme_mount_points[0]}/docker"
                    user_input = input(f"Enter Docker data-root directory [{default_path}]: ").strip()
                    target_path = user_input if user_input else default_path
                else:
                    target_path = f"{nvme_mount_points[0]}/docker"
            
            # Confirm migration
            if interactive:
                print(f"⚠️ Docker data will be migrated to: {target_path}")
                print("⚠️ This may take time if you have many Docker images/containers.")
                confirm = input("Continue with migration? (y/N): ").lower()
                if confirm not in ['y', 'yes']:
                    return {
                        'status': 'cancelled',
                        'message': 'Migration cancelled by user'
                    }
            
            # Perform migration
            return self._perform_docker_migration(target_path)
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Docker data migration failed: {e}'
            }
    
    def _perform_docker_migration(self, target_path: str) -> Dict[str, Any]:
        """Perform the actual Docker data migration.
        
        Args:
            target_path: Target directory for Docker data
            
        Returns:
            Dictionary containing migration results
        """
        target_path_obj = Path(target_path)
        
        try:
            # Stop Docker service
            subprocess.run(['systemctl', 'stop', 'docker'], check=True)
            
            # Get current Docker data size
            result = subprocess.run(['du', '-csh', str(self.docker_lib_path)],
                                 capture_output=True, text=True, check=True)
            current_size = result.stdout.split('\n')[0].split('\t')[0]
            
            # Create target directory
            target_path_obj.mkdir(parents=True, exist_ok=True)
            
            # Migrate data using rsync
            subprocess.run([
                'rsync', '-axPS', 
                f"{self.docker_lib_path}/", 
                str(target_path_obj)
            ], check=True)
            
            # Verify migration
            result = subprocess.run(['du', '-csh', str(target_path_obj)],
                                 capture_output=True, text=True, check=True)
            new_size = result.stdout.split('\n')[0].split('\t')[0]
            
            # Update daemon.json with new data-root
            self._update_data_root_config(target_path)
            
            # Rename old Docker directory
            old_docker_path = self.docker_lib_path.with_suffix('.old')
            self.docker_lib_path.rename(old_docker_path)
            
            # Restart Docker service
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'restart', 'docker'], check=True)
            
            return {
                'status': 'success',
                'message': f'Docker data successfully migrated to {target_path}',
                'details': {
                    'original_size': current_size,
                    'migrated_size': new_size,
                    'old_path_renamed': str(old_docker_path)
                }
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Migration failed: {e}',
                'details': 'Docker service may need manual restart'
            }
    
    def setup_docker(self, no_migrate: bool = False, 
                    interactive: bool = True) -> Dict[str, Any]:
        """Complete Docker setup including installation, configuration, and migration.
        
        Args:
            no_migrate: Skip Docker data directory migration
            interactive: Whether to run in interactive mode
            
        Returns:
            Dictionary containing setup results
        """
        results = []
        
        # Install Docker if needed
        if not self.is_docker_installed():
            install_result = self.install_docker(interactive=interactive)
            results.append(('Installation', install_result))
            if install_result['status'] == 'error':
                return {
                    'status': 'error',
                    'message': 'Docker setup failed during installation',
                    'details': results
                }
        
        # Configure NVIDIA runtime
        runtime_result = self.configure_nvidia_runtime()
        results.append(('NVIDIA Runtime', runtime_result))
        
        # Setup docker group
        group_result = self.setup_docker_group()
        results.append(('Docker Group', group_result))
        
        # Migrate data if requested and needed
        if not no_migrate:
            migrate_result = self.migrate_docker_data(interactive=interactive)
            results.append(('Data Migration', migrate_result))
        
        # Determine overall status
        error_results = [r for r in results if r[1]['status'] == 'error']
        if error_results:
            return {
                'status': 'error',
                'message': 'Docker setup completed with errors',
                'details': results
            }
        else:
            return {
                'status': 'success',
                'message': 'Docker setup completed successfully',
                'details': results
            }
    
    def _is_nvidia_runtime_configured(self) -> bool:
        """Check if NVIDIA runtime is configured as default."""
        if not self.daemon_json_path.exists():
            return False
        
        try:
            with open(self.daemon_json_path, 'r') as f:
                config = json.load(f)
            return config.get('default-runtime') == 'nvidia'
        except (json.JSONDecodeError, IOError):
            return False
    
    def _is_data_root_configured(self) -> bool:
        """Check if Docker data-root is already configured."""
        if not self.daemon_json_path.exists():
            return False
        
        try:
            with open(self.daemon_json_path, 'r') as f:
                config = json.load(f)
            return 'data-root' in config
        except (json.JSONDecodeError, IOError):
            return False
    
    def _is_l4t_on_nvme(self) -> bool:
        """Check if L4T is installed on NVMe."""
        try:
            result = subprocess.run(['findmnt', '-n', '-o', 'SOURCE', '/'],
                                 capture_output=True, text=True, check=True)
            root_device = result.stdout.strip()
            return 'nvme' in root_device
        except subprocess.CalledProcessError:
            return False
    
    def _get_nvme_mount_points(self) -> List[str]:
        """Get list of NVMe mount points."""
        try:
            result = subprocess.run(['lsblk', '-nr', '-o', 'NAME,MOUNTPOINT'],
                                 capture_output=True, text=True, check=True)
            
            mount_points = []
            for line in result.stdout.split('\n'):
                if line.startswith('nvme') and ' ' in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1]:  # Has mount point
                        mount_points.append(parts[1])
            
            return mount_points
        except subprocess.CalledProcessError:
            return []
    
    def _ensure_jq_installed(self):
        """Ensure jq is installed for JSON processing."""
        try:
            subprocess.run(['jq', '--version'], 
                         capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            subprocess.run(['apt', 'install', '-y', 'jq'], check=True)
    
    def _validate_json(self, json_file: Path):
        """Validate JSON file format."""
        try:
            with open(json_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _update_data_root_config(self, data_root_path: str):
        """Update daemon.json with new data-root path."""
        if self.daemon_json_path.exists():
            with open(self.daemon_json_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        config['data-root'] = data_root_path
        
        # Write to temporary file first
        temp_file = self.daemon_json_path.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Validate and replace
        self._validate_json(temp_file)
        temp_file.replace(self.daemon_json_path)
    
    def _restart_docker_service(self):
        """Restart Docker service."""
        subprocess.run(['systemctl', 'restart', 'docker'], check=True)