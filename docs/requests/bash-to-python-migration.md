Here is a thorough plan to migrate the `jetson-cli` repository to a pure Python project.

### **1. Project Structure Analysis**

First, let's analyze the current project structure to identify all shell scripts and their functionalities.

  * **`scripts/` directory**: This directory contains all the shell scripts responsible for system configuration and setup.
      * **`setup-system.sh`**: The main script that orchestrates the entire setup process by calling other configuration scripts.
      * **`probe-system.sh`**: Probes the system to gather information about the current configuration.
      * **`create-env-profile.sh`**: Creates an environment profile for Jetson development.
      * **`configure-docker.sh`**: Configures the Docker daemon and NVIDIA container runtime.
      * **`configure-swap.sh`**: Sets up a swap file and configures zRAM.
      * **`configure-ssd.sh`**: Configures NVMe SSD storage.
      * **`configure-power-mode.sh`**: Configures the Jetson power mode.
      * **`configure-system-gui.sh`**: Enables or disables the desktop GUI.
  * **`jetson_cli/` directory**: This is the main Python package for the CLI.
      * **`cli.py`**: The main CLI interface using Click.
      * **`utils.py`**: Utility functions for running scripts and checking the platform.
  * **`jetson-containers/` directory**: This is a Git submodule that contains the `jetson-containers` framework.

### **2. Python Equivalents for Shell Commands**

Next, let's determine the Python equivalents for the shell commands used in these scripts. We can use Python's standard library and third-party packages to achieve the same functionality.

  * **`os` module**: For interacting with the operating system, such as checking for file existence, creating directories, and changing file permissions.
  * **`subprocess` module**: For running external commands and capturing their output.
  * **`sys` module**: For accessing system-specific parameters and functions.
  * **`pathlib` module**: For working with filesystem paths in an object-oriented way.
  * **`psutil` module**: For retrieving information on running processes and system utilization.
  * **`py-yaml` module**: For parsing and generating YAML files.
  * **`rich` module**: For creating rich and beautiful command-line interfaces.
  * **`click` module**: For creating command-line interfaces with a clean and composable API.

### **3. New Project Structure**

Now, let's outline a new project structure that replaces the `scripts` directory with a Python module, say `jetson_cli.sdk`. This will make the project more modular and easier to maintain.

```
jetson-cli/
├── jetson_cli/
│   ├── __init__.py
│   ├── cli.py
│   ├── utils.py
│   └── sdk/
│       ├── __init__.py
│       ├── system.py
│       ├── docker.py
│       ├── storage.py
│       ├── power.py
│       └── gui.py
├── tests/
├── docs/
├── .github/
└── setup.py
```

  * **`jetson_cli/sdk/` directory**: This new directory will contain the Python modules that replace the shell scripts.
      * **`system.py`**: This module will contain functions for system-wide operations, such as probing the system and creating environment profiles.
      * **`docker.py`**: This module will handle Docker-related tasks, such as configuring the Docker daemon and managing containers.
      * **`storage.py`**: This module will be responsible for storage-related operations, such as configuring NVMe SSDs and setting up swap files.
      * **`power.py`**: This module will contain functions for managing the Jetson power modes.
      * **`gui.py`**: This module will handle GUI-related configurations, such as enabling or disabling the desktop GUI.

### **4. Migration Plan**

With the new project structure in place, let's detail the migration plan for each script.

#### **`probe-system.sh` -\> `jetson_cli/sdk/system.py`**

The `probe-system.sh` script is responsible for gathering system information. We can replicate this functionality in Python using the `psutil` and `subprocess` modules.

  * **`get_system_info()`**: This function will return a dictionary containing system information, such as the CPU, memory, and disk usage.
  * **`get_jetson_info()`**: This function will retrieve Jetson-specific information, such as the Jetson model, JetPack version, and CUDA version.

#### **`create-env-profile.sh` -\> `jetson_cli/sdk/system.py`**

The `create-env-profile.sh` script creates an environment profile for Jetson development. We can implement this in Python using the `pathlib` and `os` modules.

  * **`create_env_profile()`**: This function will create a `.env` file with the necessary environment variables for Jetson development.

#### **`configure-docker.sh` -\> `jetson_cli/sdk/docker.py`**

The `configure-docker.sh` script configures the Docker daemon and NVIDIA container runtime. We can use the `subprocess` and `os` modules to achieve this in Python.

  * **`configure_docker()`**: This function will configure the Docker daemon by modifying the `/etc/docker/daemon.json` file.
  * **`install_nvidia_docker()`**: This function will install the NVIDIA container runtime by running the necessary shell commands.

#### **`configure-swap.sh` -\> `jetson_cli/sdk/storage.py`**

The `configure-swap.sh` script sets up a swap file and configures zRAM. We can use the `subprocess` and `os` modules to implement this in Python.

  * **`setup_swap_file()`**: This function will create and enable a swap file.
  * **`configure_zram()`**: This function will configure zRAM by creating the necessary configuration files and services.

#### **`configure-ssd.sh` -\> `jetson_cli/sdk/storage.py`**

The `configure-ssd.sh` script configures NVMe SSD storage. We can use the `subprocess` and `os` modules to achieve this in Python.

  * **`format_and_mount_nvme()`**: This function will format and mount an NVMe SSD.
  * **`add_nvme_to_fstab()`**: This function will add the NVMe SSD to the `/etc/fstab` file to ensure it's mounted on boot.

#### **`configure-power-mode.sh` -\> `jetson_cli/sdk/power.py`**

The `configure-power-mode.sh` script configures the Jetson power mode. We can use the `subprocess` module to run the `nvpmodel` command and set the power mode.

  * **`set_power_mode()`**: This function will set the Jetson power mode by running the `nvpmodel` command with the desired mode.

#### **`configure-system-gui.sh` -\> `jetson_cli/sdk/gui.py`**

The `configure-system-gui.sh` script enables or disables the desktop GUI. We can use the `subprocess` module to run the `systemctl` command and set the default target.

  * **`set_gui_state()`**: This function will enable or disable the desktop GUI by setting the default systemd target to either `graphical.target` or `multi-user.target`.

### **5. Testing Strategy**

After migrating all the shell scripts to Python, it's crucial to test the new implementation to ensure everything works as expected.

  * **Unit tests**: Write unit tests for each function in the `jetson_cli.sdk` module to verify their functionality in isolation.
  * **Integration tests**: Create integration tests that simulate the entire setup process to ensure all the modules work together correctly.
  * **End-to-end tests**: Run end-to-end tests on a real Jetson device to verify that the CLI can successfully configure the system.

By following this plan, you can migrate the `jetson-cli` repository to a pure Python project, making it more modular, maintainable, and easier to extend in the future.