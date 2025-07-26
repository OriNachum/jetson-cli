# jetson-cli

A comprehensive CLI tool for setting up NVIDIA Jetson devices and building containerized AI/ML applications using the jetson-containers framework.

## Overview

jetson-cli provides a streamlined interface for:
- Analyzing and configuring Jetson hardware
- Setting up development environments
- Building and running containerized AI/ML applications
- Managing the jetson-containers ecosystem

## Installation

### From PyPI (Recommended)
```bash
pip install jetson-cli
```

### From Source
```bash
git clone https://github.com/your-org/jetson-cli.git
cd jetson-cli
pip install -e .
```

## Quick Start

1. **Analyze your system**:
   ```bash
   jetson-cli probe
   ```

2. **Initialize environment**:
   ```bash
   jetson-cli init
   ```

3. **Complete setup**:
   ```bash
   jetson-cli setup
   ```

## Commands

### System Analysis
```bash
jetson-cli probe                        # Show system configuration
jetson-cli probe --output json          # Output as JSON
jetson-cli probe --save config.yaml     # Save to file
```

### Environment Setup
```bash
jetson-cli init                         # Create environment profile
jetson-cli init --profile-name dev      # Custom profile name
jetson-cli init --force                 # Overwrite existing profile
```

### System Configuration
```bash
jetson-cli setup                        # Complete system setup
jetson-cli setup --skip-docker          # Skip Docker configuration
jetson-cli setup --interactive          # Interactive mode
```

### Component Management
```bash
jetson-cli configure docker             # Configure Docker daemon
jetson-cli configure swap               # Setup swap file
jetson-cli configure ssd                # Configure SSD storage
jetson-cli configure power              # Power management settings
jetson-cli configure gui                # GUI environment setup
```

### Status Monitoring
```bash
jetson-cli status                       # Show system status
jetson-cli status --format json         # JSON output format
```

## jetson-containers Integration

This tool integrates with the [jetson-containers](https://github.com/dusty-nv/jetson-containers) framework to provide containerized AI/ML packages:

### Container Building
```bash
# After jetson-cli setup, use jetson-containers directly
jetson-containers build pytorch                    # Build PyTorch container
jetson-containers build pytorch jupyterlab         # Chain multiple packages
jetson-containers build --name=my_app pytorch      # Custom container name
```

### Available Packages
- **ML/AI**: PyTorch, TensorFlow, ONNX Runtime, transformers
- **LLM**: SGLang, vLLM, MLC, text-generation-webui, ollama
- **VLM**: LLaVA, VILA, NanoLLM (vision-language models)
- **Robotics**: ROS, Genesis, OpenVLA, LeRobot
- **Computer Vision**: NanoOWL, SAM, CLIP, DeepStream
- **Graphics**: Stable Diffusion, ComfyUI, NeRF Studio

### Running Containers
```bash
jetson-containers run $(autotag l4t-pytorch)
```

## Examples

### Complete Jetson Setup Workflow
```bash
# 1. Analyze hardware and software configuration
jetson-cli probe --save system-info.yaml

# 2. Create development environment profile
jetson-cli init --profile-name ml-dev

# 3. Configure the system for AI/ML development
jetson-cli setup

# 4. Verify everything is working
jetson-cli status

# 5. Build and run your first container
jetson-containers build pytorch
jetson-containers run $(autotag l4t-pytorch)
```

### Selective Component Configuration
```bash
# Configure only Docker (skip other components)
jetson-cli configure docker

# Setup additional swap space
jetson-cli configure swap

# Configure external SSD storage
jetson-cli configure ssd
```

## Architecture

- **CLI Interface** (`jetson_cli/`): User-friendly Click-based commands
- **System Scripts** (`scripts/`): Low-level system configuration scripts
- **Container Framework** (`jetson-containers/`): Modular container build system
- **Package Ecosystem**: 100+ pre-built AI/ML container packages

## Requirements

- NVIDIA Jetson device (Nano, Xavier, Orin series)
- JetPack 4.6+ or L4T R32.7+
- Python 3.6+
- Docker support

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.