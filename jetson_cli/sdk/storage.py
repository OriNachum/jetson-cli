#!/usr/bin/env python3
"""
Storage Management Module

This module handles storage-related operations including NVMe SSD configuration,
swap file setup, and zRAM management for Jetson devices.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil

from ..utils import ensure_root, format_size


class StorageManager:
    """Manager for storage operations on Jetson devices."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize StorageManager.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
    
    def setup_swap_file(self, swap_path: str = "/swapfile", 
                       swap_size: str = "8G",
                       disable_zram: bool = True) -> Dict[str, Any]:
        """Set up a swap file.
        
        Args:
            swap_path: Path for the swap file
            swap_size: Size of swap file (e.g., "8G", "4096M")
            disable_zram: Whether to disable zRAM
            
        Returns:
            Dictionary containing setup results
        """
        try:
            swap_file = Path(swap_path)
            
            # Check if swap file already exists and is active
            if self._is_swap_active(swap_path):
                return {
                    'status': 'info',
                    'message': f'Swap file {swap_path} is already active'
                }
            
            # Disable zRAM if requested
            if disable_zram:
                disable_result = self.disable_zram()
                if disable_result['status'] == 'error':
                    return disable_result
            
            # Parse swap size to bytes
            swap_bytes = self._parse_size_to_bytes(swap_size)
            
            # Check available disk space
            disk_usage = psutil.disk_usage(swap_file.parent)
            if disk_usage.free < swap_bytes * 1.1:  # 10% buffer
                return {
                    'status': 'error',
                    'message': f'Insufficient disk space. Need {format_size(swap_bytes)}, '
                              f'have {format_size(disk_usage.free)} available'
                }
            
            # Create swap file
            self._create_swap_file(swap_path, swap_bytes)
            
            # Format as swap
            subprocess.run(['mkswap', swap_path], check=True)
            
            # Enable swap
            subprocess.run(['swapon', swap_path], check=True)
            
            # Add to /etc/fstab for persistent mounting
            self._add_swap_to_fstab(swap_path)
            
            return {
                'status': 'success',
                'message': f'Swap file created and activated: {swap_path} ({swap_size})',
                'details': {
                    'path': swap_path,
                    'size': swap_size,
                    'size_bytes': swap_bytes
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to setup swap file: {e}'
            }
    
    def disable_zram(self) -> Dict[str, Any]:
        """Disable zRAM and nvzramconfig service.
        
        Returns:
            Dictionary containing disable results
        """
        try:
            results = []
            
            # Check if nvzramconfig service exists
            try:
                result = subprocess.run(['systemctl', 'list-unit-files', 'nvzramconfig.service'],
                                     capture_output=True, text=True, check=False)
                
                if 'nvzramconfig.service' in result.stdout:
                    # Stop and disable nvzramconfig service (requires root)
                    try:
                        subprocess.run(['sudo', 'systemctl', 'stop', 'nvzramconfig'], check=False)
                        subprocess.run(['sudo', 'systemctl', 'disable', 'nvzramconfig'], check=True)
                        results.append('nvzramconfig service disabled')
                    except subprocess.CalledProcessError as e:
                        results.append(f'Warning: Could not disable nvzramconfig: {e}')
                else:
                    results.append('nvzramconfig service not found')
            except subprocess.CalledProcessError as e:
                results.append(f'Warning: Could not check nvzramconfig service: {e}')
            
            # Disable any active zram devices
            try:
                # Find active zram devices
                result = subprocess.run(['lsblk'], capture_output=True, text=True, check=True)
                zram_devices = []
                for line in result.stdout.split('\n'):
                    if 'zram' in line:
                        device = line.split()[0]
                        zram_devices.append(f'/dev/{device}')
                
                # Disable zram devices (requires root)
                for device in zram_devices:
                    try:
                        subprocess.run(['sudo', 'swapoff', device], check=False)
                        results.append(f'Disabled zram device: {device}')
                    except subprocess.CalledProcessError:
                        pass
                
                if not zram_devices:
                    results.append('No active zram devices found')
                    
            except subprocess.CalledProcessError as e:
                results.append(f'Warning: Could not check zram devices: {e}')
            
            return {
                'status': 'success',
                'message': 'zRAM disabled successfully',
                'details': results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to disable zRAM: {e}'
            }
    
    def configure_nvme_ssd(self, device: str = "/dev/nvme0n1",
                          partition: str = "/dev/nvme0n1p1", 
                          mount_point: str = "/mnt/nvme",
                          filesystem: str = "ext4",
                          interactive: bool = True) -> Dict[str, Any]:
        """Configure NVMe SSD with partitioning, formatting, and mounting.
        
        Args:
            device: NVMe device path
            partition: Partition path
            mount_point: Mount point directory
            filesystem: Filesystem type
            interactive: Whether to prompt for confirmation
            
        Returns:
            Dictionary containing configuration results
        """
        try:
            device_path = Path(device)
            partition_path = Path(partition)
            mount_point_path = Path(mount_point)
            
            # Check if device exists
            if not device_path.exists():
                return {
                    'status': 'error',
                    'message': f'NVMe device {device} not found'
                }
            
            # Check if already configured
            if self._is_nvme_mounted(partition, mount_point):
                return {
                    'status': 'info',
                    'message': f'NVMe {partition} is already mounted at {mount_point}'
                }
            
            # Warn about data loss
            if interactive:
                print(f"⚠️ WARNING: This will format {device} and destroy all data!")
                print(f"⚠️ Device will be partitioned and formatted as {filesystem}")
                confirm = input("Continue? (y/N): ").lower()
                if confirm not in ['y', 'yes']:
                    return {
                        'status': 'cancelled',
                        'message': 'NVMe configuration cancelled by user'
                    }
            
            # Partition the device
            partition_result = self._partition_nvme(device)
            if partition_result['status'] != 'success':
                return partition_result
            
            # Format the partition
            format_result = self._format_partition(partition, filesystem)
            if format_result['status'] != 'success':
                return format_result
            
            # Create mount point and mount
            mount_result = self._mount_partition(partition, mount_point)
            if mount_result['status'] != 'success':
                return mount_result
            
            # Add to fstab for persistent mounting
            fstab_result = self._add_nvme_to_fstab(partition, mount_point, filesystem)
            if fstab_result['status'] != 'success':
                return fstab_result
            
            return {
                'status': 'success',
                'message': f'NVMe SSD configured successfully at {mount_point}',
                'details': {
                    'device': device,
                    'partition': partition,
                    'mount_point': mount_point,
                    'filesystem': filesystem
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'NVMe SSD configuration failed: {e}'
            }
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get comprehensive storage information.
        
        Returns:
            Dictionary containing storage information
        """
        info = {
            'disks': [],
            'mounts': [],
            'swap': [],
            'nvme_devices': []
        }
        
        try:
            # Get disk information
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info['mounts'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100,
                        'total_formatted': format_size(usage.total),
                        'used_formatted': format_size(usage.used),
                        'free_formatted': format_size(usage.free)
                    })
                except PermissionError:
                    # Skip inaccessible mounts
                    continue
            
            # Get swap information
            swap_info = psutil.swap_memory()
            info['swap'] = {
                'total': swap_info.total,
                'used': swap_info.used,
                'free': swap_info.free,
                'percent': swap_info.percent,
                'total_formatted': format_size(swap_info.total),
                'used_formatted': format_size(swap_info.used),
                'free_formatted': format_size(swap_info.free)
            }
            
            # Get NVMe devices
            try:
                result = subprocess.run(['lsblk', '-J'], capture_output=True, text=True, check=True)
                import json
                lsblk_data = json.loads(result.stdout)
                
                for device in lsblk_data.get('blockdevices', []):
                    if 'nvme' in device.get('name', ''):
                        info['nvme_devices'].append({
                            'name': device.get('name'),
                            'size': device.get('size'),
                            'type': device.get('type'),
                            'mountpoint': device.get('mountpoint'),
                            'children': device.get('children', [])
                        })
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                pass
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def _is_swap_active(self, swap_path: str) -> bool:
        """Check if swap file is active."""
        try:
            result = subprocess.run(['swapon', '--show'], 
                                 capture_output=True, text=True, check=True)
            return swap_path in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def _parse_size_to_bytes(self, size_str: str) -> int:
        """Parse size string to bytes (e.g., '8G' -> 8589934592)."""
        size_str = size_str.upper().strip()
        
        multipliers = {
            'B': 1,
            'K': 1024,
            'KB': 1024,
            'M': 1024**2,
            'MB': 1024**2,
            'G': 1024**3,
            'GB': 1024**3,
            'T': 1024**4,
            'TB': 1024**4
        }
        
        # Extract number and unit
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
        
        # If no unit, assume bytes
        try:
            return int(size_str)
        except ValueError:
            raise ValueError(f"Invalid size format: {size_str}")
    
    def _create_swap_file(self, swap_path: str, size_bytes: int):
        """Create a swap file with the specified size."""
        # Use fallocate for faster allocation if available
        try:
            subprocess.run(['fallocate', '-l', str(size_bytes), swap_path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to dd
            block_size = 1024 * 1024  # 1MB blocks
            count = size_bytes // block_size
            subprocess.run([
                'dd', 'if=/dev/zero', f'of={swap_path}', 
                f'bs={block_size}', f'count={count}'
            ], check=True)
        
        # Set proper permissions
        os.chmod(swap_path, 0o600)
    
    def _add_swap_to_fstab(self, swap_path: str):
        """Add swap file to /etc/fstab for persistent mounting."""
        fstab_path = Path('/etc/fstab')
        fstab_line = f"{swap_path} none swap sw 0 0\n"
        
        # Check if already in fstab
        if fstab_path.exists():
            with open(fstab_path, 'r') as f:
                if swap_path in f.read():
                    return  # Already exists
        
        # Add to fstab
        with open(fstab_path, 'a') as f:
            f.write(fstab_line)
    
    def _is_nvme_mounted(self, partition: str, mount_point: str) -> bool:
        """Check if NVMe partition is mounted at the specified mount point."""
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True, check=True)
            mount_pattern = f"{partition} on {mount_point}"
            return mount_pattern in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def _partition_nvme(self, device: str) -> Dict[str, Any]:
        """Partition the NVMe device."""
        try:
            # Create a single partition using the entire disk
            subprocess.run([
                'parted', device, '--script', 'mklabel', 'gpt'
            ], check=True)
            
            subprocess.run([
                'parted', device, '--script', 'mkpart', 'primary', '0%', '100%'
            ], check=True)
            
            # Wait for kernel to recognize the partition
            subprocess.run(['partprobe', device], check=True)
            
            return {
                'status': 'success',
                'message': f'Device {device} partitioned successfully'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to partition device: {e}'
            }
    
    def _format_partition(self, partition: str, filesystem: str) -> Dict[str, Any]:
        """Format the partition with the specified filesystem."""
        try:
            if filesystem.lower() in ['ext4', 'ext3', 'ext2']:
                subprocess.run(['mkfs.ext4', '-F', partition], check=True)
            elif filesystem.lower() == 'xfs':
                subprocess.run(['mkfs.xfs', '-f', partition], check=True)
            elif filesystem.lower() in ['fat32', 'vfat']:
                subprocess.run(['mkfs.vfat', partition], check=True)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported filesystem: {filesystem}'
                }
            
            return {
                'status': 'success',
                'message': f'Partition {partition} formatted as {filesystem}'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to format partition: {e}'
            }
    
    def _mount_partition(self, partition: str, mount_point: str) -> Dict[str, Any]:
        """Mount the partition at the specified mount point."""
        try:
            mount_point_path = Path(mount_point)
            
            # Create mount point directory
            mount_point_path.mkdir(parents=True, exist_ok=True)
            
            # Mount the partition
            subprocess.run(['mount', partition, mount_point], check=True)
            
            return {
                'status': 'success',
                'message': f'Partition {partition} mounted at {mount_point}'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to mount partition: {e}'
            }
    
    def _add_nvme_to_fstab(self, partition: str, mount_point: str, 
                          filesystem: str) -> Dict[str, Any]:
        """Add NVMe partition to /etc/fstab for persistent mounting."""
        try:
            # Get UUID of the partition
            result = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', partition],
                                 capture_output=True, text=True, check=True)
            uuid = result.stdout.strip()
            
            if not uuid:
                return {
                    'status': 'error',
                    'message': f'Could not get UUID for partition {partition}'
                }
            
            fstab_path = Path('/etc/fstab')
            fstab_line = f"UUID={uuid} {mount_point} {filesystem} defaults 0 2\n"
            
            # Check if already in fstab
            if fstab_path.exists():
                with open(fstab_path, 'r') as f:
                    content = f.read()
                    if uuid in content or mount_point in content:
                        return {
                            'status': 'info',
                            'message': 'Entry already exists in /etc/fstab'
                        }
            
            # Add to fstab
            with open(fstab_path, 'a') as f:
                f.write(fstab_line)
            
            return {
                'status': 'success',
                'message': f'Added {partition} to /etc/fstab'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'message': f'Failed to add to fstab: {e}'
            }