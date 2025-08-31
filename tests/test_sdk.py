#!/usr/bin/env python3
"""
Unit tests for the Jetson CLI SDK modules
"""

import unittest
import sys
from pathlib import Path

# Add the jetson_cli package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jetson_cli.sdk import SystemManager, DockerManager, StorageManager, PowerManager, GUIManager


class TestSystemManager(unittest.TestCase):
    """Test SystemManager functionality."""
    
    def setUp(self):
        self.system_manager = SystemManager()
    
    def test_get_platform_info(self):
        """Test getting platform information."""
        platform_info = self.system_manager._get_platform_info()
        self.assertIsInstance(platform_info, dict)
        self.assertIn('system', platform_info)
        self.assertIn('machine', platform_info)
        self.assertIn('is_jetson', platform_info)
    
    def test_get_system_info(self):
        """Test getting system information."""
        system_info = self.system_manager._get_system_info()
        self.assertIsInstance(system_info, dict)
        self.assertIn('cpu_count', system_info)
        self.assertIn('memory', system_info)
        self.assertIn('disk', system_info)
        self.assertGreater(system_info['cpu_count'], 0)
    
    def test_format_probe_results(self):
        """Test formatting probe results."""
        mock_results = {
            'platform': {'system': 'Linux', 'is_jetson': True},
            'system': {'cpu_count': 4},
            'checks': {}
        }
        
        # Test table format
        table_output = self.system_manager.format_probe_results(mock_results, 'table')
        self.assertIsInstance(table_output, str)
        self.assertIn('Platform Information', table_output)
        
        # Test JSON format
        json_output = self.system_manager.format_probe_results(mock_results, 'json')
        self.assertIsInstance(json_output, str)
        self.assertIn('"platform"', json_output)


class TestDockerManager(unittest.TestCase):
    """Test DockerManager functionality."""
    
    def setUp(self):
        self.docker_manager = DockerManager()
    
    def test_is_docker_installed(self):
        """Test Docker installation check."""
        is_installed = self.docker_manager.is_docker_installed()
        self.assertIsInstance(is_installed, bool)
    
    def test_is_nvidia_runtime_configured(self):
        """Test NVIDIA runtime configuration check."""
        is_configured = self.docker_manager._is_nvidia_runtime_configured()
        self.assertIsInstance(is_configured, bool)
    
    def test_get_nvme_mount_points(self):
        """Test getting NVMe mount points."""
        mount_points = self.docker_manager._get_nvme_mount_points()
        self.assertIsInstance(mount_points, list)


class TestStorageManager(unittest.TestCase):
    """Test StorageManager functionality."""
    
    def setUp(self):
        self.storage_manager = StorageManager()
    
    def test_parse_size_to_bytes(self):
        """Test size string parsing."""
        # Test various size formats
        self.assertEqual(self.storage_manager._parse_size_to_bytes('1024'), 1024)
        self.assertEqual(self.storage_manager._parse_size_to_bytes('1K'), 1024)
        self.assertEqual(self.storage_manager._parse_size_to_bytes('1M'), 1024*1024)
        self.assertEqual(self.storage_manager._parse_size_to_bytes('1G'), 1024*1024*1024)
        
        # Test case insensitive
        self.assertEqual(self.storage_manager._parse_size_to_bytes('1g'), 1024*1024*1024)
        
        # Test invalid format
        with self.assertRaises(ValueError):
            self.storage_manager._parse_size_to_bytes('invalid')
    
    def test_get_storage_info(self):
        """Test getting storage information."""
        storage_info = self.storage_manager.get_storage_info()
        self.assertIsInstance(storage_info, dict)
        self.assertIn('mounts', storage_info)
        self.assertIn('swap', storage_info)
        self.assertIn('nvme_devices', storage_info)
    
    def test_is_swap_active(self):
        """Test swap active check."""
        is_active = self.storage_manager._is_swap_active('/nonexistent')
        self.assertIsInstance(is_active, bool)


class TestPowerManager(unittest.TestCase):
    """Test PowerManager functionality."""
    
    def setUp(self):
        self.power_manager = PowerManager()
    
    def test_get_current_power_mode(self):
        """Test getting current power mode."""
        result = self.power_manager.get_current_power_mode()
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
    
    def test_get_thermal_info(self):
        """Test getting thermal information."""
        thermal_info = self.power_manager.get_thermal_info()
        self.assertIsInstance(thermal_info, dict)
        self.assertIn('available', thermal_info)
        self.assertIn('zones', thermal_info)
    
    def test_get_power_consumption_info(self):
        """Test getting power consumption information."""
        power_info = self.power_manager.get_power_consumption_info()
        self.assertIsInstance(power_info, dict)
        self.assertIn('available', power_info)


class TestGUIManager(unittest.TestCase):
    """Test GUIManager functionality."""
    
    def setUp(self):
        self.gui_manager = GUIManager()
    
    def test_get_gui_status(self):
        """Test getting GUI status."""
        status = self.gui_manager.get_gui_status()
        self.assertIsInstance(status, dict)
        self.assertIn('status', status)
    
    def test_get_display_info(self):
        """Test getting display information."""
        display_info = self.gui_manager.get_display_info()
        self.assertIsInstance(display_info, dict)
        self.assertIn('display_available', display_info)
        self.assertIn('x_server_running', display_info)
    
    def test_is_gui_currently_running(self):
        """Test GUI running check."""
        is_running = self.gui_manager._is_gui_currently_running()
        self.assertIsInstance(is_running, bool)
    
    def test_get_desktop_environment_info(self):
        """Test getting desktop environment information."""
        de_info = self.gui_manager.get_desktop_environment_info()
        self.assertIsInstance(de_info, dict)
        self.assertIn('desktop_session', de_info)
        self.assertIn('available_sessions', de_info)


if __name__ == '__main__':
    unittest.main(verbosity=2)