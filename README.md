# jetson-jolt

A comprehensive Python CLI tool for setting up NVIDIA Jetson devices and building containerized AI/ML applications.

## Overview

jetson-jolt provides a streamlined, pure-Python interface for:
- Analyzing and configuring Jetson hardware
- Setting up development environments  
- Managing Docker, storage, power, and GUI configurations
- Building and running containerized AI/ML applications

## Features

✅ **Pure Python Implementation**: No shell script dependencies  
✅ **Comprehensive System Analysis**: Hardware detection and configuration validation  
✅ **Modular Architecture**: Separate managers for different system components  
✅ **Rich CLI Interface**: Beautiful terminal output with progress indicators  
✅ **Multiple Output Formats**: Table, JSON, and YAML support  
✅ **Interactive & Non-Interactive Modes**: Flexible operation modes  
✅ **Extensive Testing**: Unit tests for all major functionality  

## Task list
- [ ] Best practices compliation for jetson for humans and AI
  - [ ] tools
  - [ ] commands
  - [ ] configurations 
- [ ] docker images backup and restore scripts
- [ ] GenAI integration on device, local or remote
- [ ] Model inference setup recommendations
- [ ] jetson-containers Package suite recommendations


## Installation

### From PyPI (Recommended)
```bash
pip install jetson-jolt
```

### From Source
```bash
git clone https://github.com/orinachum/jetson-jolt.git
cd jetson-jolt
pip install -e .
```

## Quick Start

1. **Analyze your system**:
   ```bash
   jetson-jolt probe
   ```

2. **Initialize environment**:
   ```bash
   jetson-jolt init
   ```

3. **Complete setup**:
   ```bash
   jetson-jolt setup
   ```

## Commands

### System Analysis
```bash
jetson-jolt probe                        # Show system configuration
jetson-jolt probe --output json          # Output as JSON
jetson-jolt probe --save config.yaml     # Save to file
jetson-jolt probe --tests docker,swap    # Run specific tests only
```

### Environment Setup
```bash
jetson-jolt init                         # Create environment profile
jetson-jolt init --profile-name dev      # Custom profile name
jetson-jolt init --force                 # Overwrite existing profile
```

### System Configuration
```bash
jetson-jolt setup                        # Complete system setup
jetson-jolt setup --skip-docker          # Skip Docker configuration
jetson-jolt setup --interactive          # Interactive mode
jetson-jolt setup --non-interactive      # Automated mode
```

### Component Management
```bash
jetson-jolt configure docker             # Configure Docker daemon
jetson-jolt configure swap               # Setup swap file
jetson-jolt configure ssd                # Configure SSD storage
jetson-jolt configure power              # Power management settings
jetson-jolt configure gui                # GUI environment setup
```

### Status Monitoring
```bash
jetson-jolt status                       # Show system status table
jetson-jolt status --format json         # JSON output format
```

## Configuration Components

### Docker Management
- Automatic Docker installation with NVIDIA runtime
- Data directory migration to NVMe storage
- User group configuration
- Runtime optimization

### Storage Management  
- NVMe SSD partitioning, formatting, and mounting
- Swap file creation and configuration
- zRAM management
- Automatic size detection and validation

### Power Management
- Jetson power mode configuration
- Thermal monitoring
- Power consumption analysis
- Interactive mode selection

### GUI Management
- Desktop environment enable/disable
- Display configuration detection
- Session management
- Boot configuration

## Python SDK

The CLI is built on a modular SDK that can be used programmatically:

```python
from jetson_jolt.sdk import SystemManager, DockerManager, StorageManager

# System analysis
system_manager = SystemManager()
results = system_manager.probe_system()
print(f"Platform: {results['platform']['machine']}")

# Docker configuration
docker_manager = DockerManager()
if not docker_manager.is_docker_installed():
    docker_manager.install_docker()

# Storage management
storage_manager = StorageManager()
storage_info = storage_manager.get_storage_info()
```

## Examples

### Complete Jetson Setup Workflow
```bash
# 1. Analyze hardware and software configuration
jetson-jolt probe --save system-info.json

# 2. Create development environment profile
jetson-jolt init --profile-name ml-dev

# 3. Configure the system for AI/ML development
jetson-jolt setup

# 4. Verify everything is working
jetson-jolt status

# 5. Configure specific components as needed
jetson-jolt configure power  # Set optimal power mode
jetson-jolt configure ssd    # Setup external storage
```

### Selective Component Configuration
```bash
# Configure only Docker (skip other components)
jetson-jolt configure docker

# Setup additional swap space
jetson-jolt configure swap

# Configure external SSD storage
jetson-jolt configure ssd --interactive

# Set power mode for maximum performance
jetson-jolt configure power
```

### System Analysis and Monitoring
```bash
# Comprehensive system probe
jetson-jolt probe --output json --save analysis.json

# Monitor specific components
jetson-jolt probe --tests docker_installed,nvme_mount,power_mode

# Check system status
jetson-jolt status --format table
```

## Architecture

```
jetson-jolt/
├── jetson_jolt/
│   ├── cli.py              # Click-based CLI interface
│   ├── utils.py            # Utility functions
│   └── sdk/                # Python SDK modules
│       ├── system.py       # System management
│       ├── docker.py       # Docker configuration
│       ├── storage.py      # Storage management
│       ├── power.py        # Power management
│       └── gui.py          # GUI configuration
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

### Key Components

- **CLI Interface**: Rich terminal interface with progress indicators
- **SDK Modules**: Modular Python classes for system management
- **Configuration Management**: Environment-based configuration
- **Error Handling**: Comprehensive error reporting and recovery
- **Testing Framework**: Unit tests for all major functionality

## Requirements

- NVIDIA Jetson device (Nano, Xavier, Orin series)
- JetPack 4.6+ or L4T R32.7+
- Python 3.8+
- Root privileges for system configuration

## Development

### Running Tests
```bash
# Run all tests
python -m unittest tests.test_sdk -v

# Run specific test
python -m unittest tests.test_sdk.TestSystemManager -v
```

### Adding New Features
1. Implement functionality in appropriate SDK module
2. Add CLI command in `cli.py`
3. Write unit tests in `tests/`
4. Update documentation

## Migrated from Shell Scripts

This version represents a complete migration from shell scripts to pure Python:

- ✅ `probe-system.sh` → `SystemManager.probe_system()`
- ✅ `configure-docker.sh` → `DockerManager.setup_docker()`
- ✅ `configure-swap.sh` → `StorageManager.setup_swap_file()`
- ✅ `configure-ssd.sh` → `StorageManager.configure_nvme_ssd()`
- ✅ `configure-power-mode.sh` → `PowerManager.set_power_mode()`
- ✅ `configure-system-gui.sh` → `GUIManager.configure_gui()`
- ✅ `create-env-profile.sh` → `SystemManager.create_env_profile()`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
