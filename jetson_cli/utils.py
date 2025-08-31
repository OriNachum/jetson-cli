#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
from pathlib import Path

def get_package_root():
    """Get the root directory of the jetson-cli package."""
    return Path(__file__).parent

def get_script_path(script_name):
    """Get the full path to a script file."""
    # First try the package scripts directory
    package_script = get_package_root() / 'scripts' / script_name
    if package_script.exists():
        return str(package_script)
    
    # Then try the repository scripts directory
    repo_script = get_package_root().parent / 'scripts' / script_name
    if repo_script.exists():
        return str(repo_script)
    
    raise FileNotFoundError(f"Script {script_name} not found in expected locations")

def run_script(script_path, env=None, verbose=False):
    """Run a shell script and return the result."""
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    # Prepare environment
    script_env = os.environ.copy()
    if env:
        script_env.update(env)
    
    if verbose:
        print(f"Running script: {script_path}")
        if env:
            print(f"Environment variables: {env}")
    
    # Run the script
    result = subprocess.run(
        ['bash', script_path],
        env=script_env,
        capture_output=True,
        text=True,
        check=True
    )
    
    return result

def check_jetson_platform():
    """Check if running on a Jetson platform."""
    try:
        # Check for common Jetson indicators
        jetson_indicators = [
            '/proc/device-tree/model',
            '/etc/nv_tegra_release',
            '/sys/firmware/devicetree/base/model'
        ]
        
        for indicator in jetson_indicators:
            if os.path.exists(indicator):
                try:
                    with open(indicator, 'r') as f:
                        content = f.read().lower()
                        if 'jetson' in content or 'tegra' in content or 'nvidia' in content:
                            return True
                except:
                    continue
        
        # Check architecture
        if platform.machine() == 'aarch64':
            # Additional check for NVIDIA GPU
            try:
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                if result.returncode == 0 and 'jetson' in result.stdout.lower():
                    return True
            except:
                pass
        
        return False
        
    except Exception:
        return False

def get_jetson_info():
    """Get detailed Jetson platform information."""
    info = {
        'platform': 'Unknown',
        'l4t_version': 'Unknown',
        'jetpack_version': 'Unknown',
        'cuda_version': 'Unknown',
        'architecture': platform.machine()
    }
    
    try:
        # Get model information
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                info['platform'] = f.read().strip().replace('\x00', '')
        
        # Get L4T version
        if os.path.exists('/etc/nv_tegra_release'):
            with open('/etc/nv_tegra_release', 'r') as f:
                content = f.read()
                # Parse version from content like "R35 (release), REVISION: 4.1"
                import re
                match = re.search(r'R(\d+)\s+\(release\),\s+REVISION:\s+([\d.]+)', content)
                if match:
                    info['l4t_version'] = f"{match.group(1)}.{match.group(2)}"
        
        # Get CUDA version
        try:
            result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                import re
                match = re.search(r'release (\d+\.\d+)', result.stdout)
                if match:
                    info['cuda_version'] = match.group(1)
        except:
            pass
    
    except Exception:
        pass
    
    return info

def ensure_root():
    """Ensure the script is running with root privileges."""
    if os.geteuid() != 0:
        raise PermissionError("This command requires root privileges. Please run with sudo.")

def ensure_root():
    """Ensure the script is running with root privileges."""
    if os.geteuid() != 0:
        raise PermissionError("This command requires root privileges. Please run with sudo.")

def format_size(bytes_value):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"