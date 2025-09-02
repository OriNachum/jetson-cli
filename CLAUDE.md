# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a Jetson setup system that includes the `jetson-containers` framework - a modular container build system for AI/ML packages on NVIDIA Jetson devices. The repository provides system setup scripts and integrates the jetson-containers framework as a Git submodule.

## Common Commands

### Jetson Jolt (Recommended)
```bash
# Install the CLI package globally
pip install jetson-jolt

# System operations
jetson-jolt probe                        # analyze system configuration
jetson-jolt init                         # create environment profile
jetson-jolt setup                        # complete system setup
jetson-jolt configure docker             # configure specific components
jetson-jolt status                       # show system status
```

### Container Building
```bash
# Install the container tools
bash jetson-containers/install.sh

# Build a container with specific packages
jetson-containers build pytorch                    # single package
jetson-containers build pytorch jupyterlab         # multiple packages chained
jetson-containers build --multiple pytorch tensorflow  # separate containers
jetson-containers build --name=my_container pytorch    # custom name

# List available packages
jetson-containers build --list-packages
jetson-containers build --show-packages
```

### Running Containers
```bash
# Run a container (pulls/builds if needed)
jetson-containers run $(autotag l4t-pytorch)

# Manual docker run
sudo docker run --runtime nvidia -it --rm --network=host dustynv/l4t-pytorch:r36.2.0
```

### System Setup (Direct Scripts)
```bash
# Run system setup scripts directly
./scripts/setup-system.sh              # main system configuration
./scripts/configure-docker.sh          # Docker daemon setup
./scripts/configure-swap.sh            # memory/swap tuning
./scripts/configure-ssd.sh             # storage configuration
```

## Architecture

### Core Structure
- **`jetson-containers/`**: Git submodule containing the main container framework
  - `jetson_containers/`: Python modules for build system (`build.py`, `container.py`, `packages.py`)
  - `packages/`: Container package definitions organized by category (llm/, ml/, robotics/, etc.)
  - `build.sh`/`run.sh`: Wrapper scripts for container operations
  - `install.sh`: System installation script

- **`scripts/`**: System configuration scripts for Jetson devices
  - Environment setup, Docker configuration, hardware tuning

- **`jetson_jolt/`**: Python CLI package for system management
  - `cli.py`: Main Click-based command interface
  - `utils.py`: Platform detection and script execution utilities
  - Provides user-friendly interface to underlying scripts

### Package System
The container framework uses a modular package system where:
- Each package has a `Dockerfile` and optional `config.py` for dynamic configuration
- Packages specify dependencies, build requirements, and metadata via YAML headers or config files
- The build system resolves dependencies and chains Dockerfiles together
- Base images default to JetPack-compatible containers (l4t-base, l4t-jetpack, or ubuntu)

### Container Categories
- **ML/AI**: PyTorch, TensorFlow, ONNX Runtime, transformers
- **LLM**: SGLang, vLLM, MLC, text-generation-webui, ollama, llama.cpp
- **VLM**: LLaVA, VILA, NanoLLM (vision-language models)
- **Robotics**: ROS, Genesis, OpenVLA, LeRobot
- **Computer Vision**: NanoOWL, SAM, CLIP, DeepStream
- **Graphics**: Stable Diffusion, ComfyUI, NeRF Studio

### Build Process
1. Package scanning finds available packages under `jetson-containers/packages/`
2. Dependency resolution determines build order
3. Dockerfiles are chained together with intermediate images
4. Build commands and logs are saved under `jetson-containers/logs/`
5. Containers are tagged with L4T/JetPack version compatibility

## Testing
Test scripts are typically included with each package as `test.py` or `test.sh` files. The build system can run tests automatically during container builds.

## Version Management
- `CUDA_VERSION`: Can be overridden to rebuild stack for different CUDA versions
- `L4T_VERSION`: Automatically detected JetPack/L4T version for compatibility
- Package versions are managed through config files and can be pinned or dynamically selected

## CLI Package Development

### Installation
```bash
# Development installation
pip install -e .

# Production installation
pip install jetson-jolt
```

### GitHub Actions Pipelines
- **CI Pipeline**: Tests across Python versions, linting, security scans
- **Release Pipeline**: Automated version bumping and PyPI publishing on main branch merges
- **Installation Testing**: Validates package installation across environments

### CLI Commands Reference
- `jetson-jolt probe [--output table|json|yaml] [--save file]`: System analysis
- `jetson-jolt init [--profile-name name] [--force]`: Environment profile creation  
- `jetson-jolt setup [--skip-docker] [--skip-swap] [--interactive]`: Complete setup
- `jetson-jolt configure <docker|swap|ssd|power|gui>`: Component configuration
- `jetson-jolt status [--format table|json]`: System status overview