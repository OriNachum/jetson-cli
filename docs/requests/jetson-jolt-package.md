# Request: Jetson Jolt Package Development

**Date**: 2025-07-26  
**Status**: In Progress  
**Priority**: High  

## Overview

Create a `jetson-jolt` pip package that provides a command-line interface for NVIDIA Jetson setup and configuration, with automated GitHub pipelines for deployment and release management.

## Requirements

### Core CLI Commands

1. **`jetson-jolt probe`** - System probing and analysis
   - Maps to: `scripts/probe-system.sh`
   - Output formats: table, JSON, YAML
   - Save results to file option

2. **`jetson-jolt init`** - Environment profile creation
   - Maps to: `scripts/create-env-profile.sh`
   - Custom profile naming
   - Force recreate option

3. **`jetson-jolt setup`** - Complete system setup
   - Maps to: `scripts/setup-system.sh`
   - Interactive/non-interactive modes
   - Skip individual components (docker, swap, ssd)

4. **`jetson-jolt configure <component>`** - Individual component configuration
   - Components: docker, swap, ssd, power, gui
   - Maps to respective `configure-*.sh` scripts

5. **`jetson-jolt status`** - System status overview
   - Show current configuration state
   - Multiple output formats

### Package Structure

```
jetson-jolt/
├── setup.py                    # Package configuration
├── jetson_jolt/
│   ├── __init__.py             # Version and package info
│   ├── cli.py                  # Main CLI interface using Click
│   ├── utils.py                # Utility functions
│   ├── scripts/                # Embedded scripts (if needed)
│   └── config/                 # Configuration files
├── tests/                      # Unit tests
├── docs/                       # Documentation
└── .github/workflows/          # CI/CD pipelines
```

### GitHub Actions Pipelines

#### 1. CI Pipeline (`.github/workflows/ci.yml`)
- **Triggers**: Push to main/develop, Pull requests
- **Jobs**:
  - Test across Python 3.8-3.12
  - Code linting (flake8, black, isort)
  - Shell script linting (shellcheck)
  - Security scanning (bandit)
  - CLI functionality testing

#### 2. Release Pipeline (`.github/workflows/release.yml`)
- **Triggers**: Push to main branch, Manual workflow dispatch
- **Features**:
  - Automated version bumping (minor on merge to main)
  - Smart version detection from commit messages
  - PyPI package publishing
  - GitHub release creation
  - Release notes generation

#### 3. Installation Testing (`.github/workflows/test-install.yml`)
- **Triggers**: New releases
- **Tests**:
  - PyPI installation across Python versions
  - Docker-based installation testing
  - CLI functionality verification

### Version Management

- **Automatic Minor Bump**: On merge to main branch
- **Manual Version Control**: Workflow dispatch with patch/minor/major options
- **Semantic Versioning**: Based on commit message analysis
- **Release Assets**: Wheel files, release notes, changelog

### Dependencies

- **Runtime**: click, pyyaml, tabulate, packaging, psutil, rich
- **Development**: pytest, flake8, black, isort, bump2version
- **CI/CD**: GitHub Actions, PyPI publishing, automated testing

## Implementation Status

### ✅ Completed
- [x] Package structure (`setup.py`, `__init__.py`)
- [x] CLI interface with Click framework
- [x] Core command implementations (probe, init, setup, configure, status)
- [x] Utility functions for script execution and platform detection
- [x] GitHub Actions CI pipeline
- [x] Automated release pipeline with version management
- [x] Installation testing workflow

### 🔄 In Progress
- [ ] Integration with existing shell scripts
- [ ] Comprehensive testing suite
- [ ] Documentation and usage examples

### ⏳ Pending
- [ ] PyPI account setup and API token configuration
- [ ] Repository secrets configuration (PYPI_API_TOKEN)
- [ ] Beta testing and feedback integration
- [ ] Production deployment

## Technical Considerations

### Platform Detection
- Jetson platform detection via device tree and hardware indicators
- Graceful fallback for non-Jetson environments
- Environment variable override for testing

### Script Integration
- Scripts embedded in package or referenced from repository
- Proper error handling and user feedback
- Progress indicators for long-running operations

### User Experience
- Rich CLI output with colors and progress bars
- Comprehensive help text and examples
- Consistent command patterns and options

## Success Criteria

1. **Functional**: All CLI commands work correctly on Jetson platforms
2. **Installable**: `pip install jetson-jolt` works globally
3. **Automated**: Releases happen automatically on main branch merges
4. **Tested**: Comprehensive test coverage and CI validation
5. **Documented**: Clear usage instructions and API documentation

## Next Steps

1. Configure PyPI account and repository secrets
2. Test the complete CI/CD pipeline
3. Create comprehensive test suite
4. Beta release for community feedback
5. Documentation and tutorial creation
6. Production release announcement