#!/usr/bin/env python3
"""
Test script for the migrated jetson-jolt SDK modules
"""

import sys
import os
from pathlib import Path

# Add the jetson_jolt package to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all SDK modules can be imported."""
    print("Testing imports...")
    
    try:
        from jetson_jolt.sdk import SystemManager, DockerManager, StorageManager, PowerManager, GUIManager
        print("✅ All SDK modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_system_manager():
    """Test SystemManager functionality."""
    print("\nTesting SystemManager...")
    
    try:
        from jetson_jolt.sdk import SystemManager
        
        system_manager = SystemManager()
        
        # Test getting platform info
        platform_info = system_manager._get_platform_info()
        print(f"✅ Platform info: {platform_info['system']} {platform_info['machine']}")
        
        # Test getting system info
        system_info = system_manager._get_system_info()
        print(f"✅ System info: {system_info['cpu_count']} CPUs, {system_info['memory']['total_formatted']} memory")
        
        # Test environment profile creation (dry run)
        result = system_manager.create_env_profile(profile_name="test-profile", force=True)
        print(f"✅ Env profile test: {result['status']} - {result['message']}")
        
        return True
    except Exception as e:
        print(f"❌ SystemManager error: {e}")
        return False

def test_docker_manager():
    """Test DockerManager functionality."""
    print("\nTesting DockerManager...")
    
    try:
        from jetson_jolt.sdk import DockerManager
        
        docker_manager = DockerManager()
        
        # Test Docker installation check
        is_installed = docker_manager.is_docker_installed()
        print(f"✅ Docker installed: {is_installed}")
        
        # Test runtime configuration check
        is_configured = docker_manager._is_nvidia_runtime_configured()
        print(f"✅ NVIDIA runtime configured: {is_configured}")
        
        return True
    except Exception as e:
        print(f"❌ DockerManager error: {e}")
        return False

def test_storage_manager():
    """Test StorageManager functionality."""
    print("\nTesting StorageManager...")
    
    try:
        from jetson_jolt.sdk import StorageManager
        
        storage_manager = StorageManager()
        
        # Test getting storage info
        storage_info = storage_manager.get_storage_info()
        print(f"✅ Storage info: {len(storage_info['mounts'])} mounts, {len(storage_info['nvme_devices'])} NVMe devices")
        
        # Test size parsing
        size_bytes = storage_manager._parse_size_to_bytes("8G")
        print(f"✅ Size parsing: 8G = {size_bytes} bytes")
        
        return True
    except Exception as e:
        print(f"❌ StorageManager error: {e}")
        return False

def test_power_manager():
    """Test PowerManager functionality."""
    print("\nTesting PowerManager...")
    
    try:
        from jetson_jolt.sdk import PowerManager
        
        power_manager = PowerManager()
        
        # Test getting current power mode
        current_mode = power_manager.get_current_power_mode()
        print(f"✅ Current power mode: {current_mode['status']}")
        
        # Test getting thermal info
        thermal_info = power_manager.get_thermal_info()
        print(f"✅ Thermal info: {len(thermal_info.get('zones', []))} thermal zones")
        
        return True
    except Exception as e:
        print(f"❌ PowerManager error: {e}")
        return False

def test_gui_manager():
    """Test GUIManager functionality."""
    print("\nTesting GUIManager...")
    
    try:
        from jetson_jolt.sdk import GUIManager
        
        gui_manager = GUIManager()
        
        # Test getting GUI status
        gui_status = gui_manager.get_gui_status()
        print(f"✅ GUI status: {gui_status['status']}")
        
        # Test getting display info
        display_info = gui_manager.get_display_info()
        print(f"✅ Display info: X server running = {display_info['x_server_running']}")
        
        return True
    except Exception as e:
        print(f"❌ GUIManager error: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Jetson Jolt SDK Migration Test ===\n")
    
    tests = [
        test_imports,
        test_system_manager,
        test_docker_manager,
        test_storage_manager,
        test_power_manager,
        test_gui_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Migration successful.")
        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())