#!/usr/bin/env python3

import click
import os
import sys
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from . import __version__
from .utils import check_jetson_platform
from .sdk import SystemManager, DockerManager, StorageManager, PowerManager, GUIManager

console = Console()

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'jetson-jolt version {__version__}')
    ctx.exit()

@click.group()
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help='Show version and exit')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Jetson Jolt - Command-line interface for NVIDIA Jetson setup and configuration"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Check if running on Jetson platform
    if not check_jetson_platform() and not os.environ.get('JETSON_JOLT_SKIP_PLATFORM_CHECK'):
        console.print("[yellow]Warning: Not running on detected Jetson platform. Some features may not work correctly.[/yellow]")

@cli.command()
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='Output format')
@click.option('--save', '-s', type=click.Path(), help='Save probe results to file')
@click.option('--tests', help='Comma-separated list of specific tests to run')
@click.pass_context
def probe(ctx, output, save, tests):
    """Probe and analyze the Jetson system configuration."""
    console.print(Panel("[bold blue]Probing Jetson System[/bold blue]", expand=False))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing system...", total=None)
        
        try:
            # Initialize system manager
            system_manager = SystemManager()
            
            # Parse tests if provided
            test_list = None
            if tests:
                test_list = [t.strip() for t in tests.split(',')]
            
            # Run probe
            results = system_manager.probe_system(tests=test_list)
            
            # Format output
            if output == 'json':
                formatted_output = json.dumps(results, indent=2)
            elif output == 'yaml':
                formatted_output = yaml.dump(results, default_flow_style=False, indent=2)
            else:
                formatted_output = system_manager.format_probe_results(results, output_format='table')
            
            console.print("\n[bold green]System Probe Results:[/bold green]")
            console.print(formatted_output)
            
            if save:
                with open(save, 'w') as f:
                    f.write(formatted_output)
                console.print(f"\n[green]Results saved to {save}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error running probe: {e}[/red]")
            if ctx.obj['verbose']:
                import traceback
                console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            sys.exit(1)

@cli.command()
@click.option('--profile-name', '-n', default='jetson-dev',
              help='Name for the environment profile')
@click.option('--force', '-f', is_flag=True, help='Force recreate existing profile')
@click.pass_context
def init(ctx, profile_name, force):
    """Initialize and create environment profile for Jetson development."""
    console.print(Panel(f"[bold blue]Initializing Environment Profile: {profile_name}[/bold blue]", expand=False))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating environment profile...", total=None)
        
        try:
            # Initialize system manager
            system_manager = SystemManager()
            
            # Create environment profile
            result = system_manager.create_env_profile(profile_name=profile_name, force=force)
            
            if result['status'] == 'success':
                console.print("\n[bold green]Environment Profile Created Successfully![/bold green]")
                console.print(f"Profile: {profile_name}")
                console.print(f"Location: {result.get('profile_path', '.env')}")
            elif result['status'] == 'warning':
                console.print(f"\n[yellow]{result['message']}[/yellow]")
            else:
                console.print(f"\n[red]{result['message']}[/red]")
                sys.exit(1)
            
        except Exception as e:
            console.print(f"[red]Error creating profile: {e}[/red]")
            if ctx.obj['verbose']:
                import traceback
                console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            sys.exit(1)

@cli.command()
@click.option('--skip-docker', is_flag=True, help='Skip Docker configuration')
@click.option('--skip-swap', is_flag=True, help='Skip swap configuration')
@click.option('--skip-ssd', is_flag=True, help='Skip SSD configuration')
@click.option('--interactive/--non-interactive', default=True,
              help='Run in interactive or non-interactive mode')
@click.pass_context
def setup(ctx, skip_docker, skip_swap, skip_ssd, interactive):
    """Run complete Jetson system setup and configuration."""
    console.print(Panel("[bold blue]Jetson System Setup[/bold blue]", expand=False))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up system...", total=None)
        
        try:
            setup_results = []
            
            # Initialize managers
            system_manager = SystemManager()
            docker_manager = DockerManager()
            storage_manager = StorageManager()
            
            # Docker setup
            if not skip_docker:
                progress.update(task, description="Configuring Docker...")
                docker_result = docker_manager.setup_docker(
                    no_migrate=skip_ssd, 
                    interactive=interactive
                )
                setup_results.append(('Docker', docker_result))
            
            # Swap setup
            if not skip_swap:
                progress.update(task, description="Configuring swap...")
                swap_result = storage_manager.setup_swap_file(
                    disable_zram=True
                )
                setup_results.append(('Swap', swap_result))
            
            # SSD setup (if available and not skipped)
            if not skip_ssd:
                progress.update(task, description="Checking NVMe SSD...")
                # Only configure if NVMe device is available
                if Path('/dev/nvme0n1').exists():
                    ssd_result = storage_manager.configure_nvme_ssd(
                        interactive=interactive
                    )
                    setup_results.append(('NVMe SSD', ssd_result))
                else:
                    setup_results.append(('NVMe SSD', {
                        'status': 'info',
                        'message': 'No NVMe SSD detected, skipping configuration'
                    }))
            
            # Display results
            console.print("\n[bold green]System Setup Results:[/bold green]")
            for component, result in setup_results:
                status = result.get('status', 'unknown')
                message = result.get('message', 'No message')
                
                if status == 'success':
                    console.print(f"✅ {component}: {message}")
                elif status == 'warning':
                    console.print(f"⚠️ {component}: {message}")
                elif status == 'error':
                    console.print(f"❌ {component}: {message}")
                else:
                    console.print(f"ℹ️ {component}: {message}")
            
            # Check for any errors
            error_results = [r for _, r in setup_results if r.get('status') == 'error']
            if error_results:
                console.print(f"\n[red]Setup completed with {len(error_results)} errors[/red]")
                sys.exit(1)
            else:
                console.print("\n[bold green]System Setup Completed Successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[red]Error during setup: {e}[/red]")
            if ctx.obj['verbose']:
                import traceback
                console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            sys.exit(1)

@cli.command()
@click.argument('component', type=click.Choice(['docker', 'swap', 'ssd', 'power', 'gui']))
@click.option('--interactive/--non-interactive', default=True,
              help='Run in interactive or non-interactive mode')
@click.pass_context
def configure(ctx, component, interactive):
    """Configure specific system components."""
    console.print(Panel(f"[bold blue]Configuring {component.upper()}[/bold blue]", expand=False))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Configuring {component}...", total=None)
        
        try:
            result = None
            
            if component == 'docker':
                docker_manager = DockerManager()
                result = docker_manager.setup_docker(interactive=interactive)
            
            elif component == 'swap':
                storage_manager = StorageManager()
                # Check if zRAM should be disabled from config
                system_manager = SystemManager()
                config = system_manager.load_config()
                disable_zram = config.get('SWAP_OPTIONS_DISABLE_ZRAM', '').lower() == 'true'
                result = storage_manager.setup_swap_file(disable_zram=disable_zram)
            
            elif component == 'ssd':
                storage_manager = StorageManager()
                result = storage_manager.configure_nvme_ssd(interactive=interactive)
            
            elif component == 'power':
                power_manager = PowerManager()
                # For power, we need to ask for the mode
                if interactive:
                    modes_info = power_manager.get_available_power_modes()
                    if modes_info['status'] == 'success':
                        console.print("\nAvailable power modes:")
                        for mode in modes_info['available_modes']:
                            status = " (current)" if mode['active'] else ""
                            console.print(f"  {mode['id']}: {mode['name']}{status}")
                        
                        mode = click.prompt("\nEnter power mode ID", type=str)
                        result = power_manager.configure_power_mode(mode, interactive=True)
                    else:
                        result = modes_info
                else:
                    # Non-interactive mode - use mode 0 as default
                    result = power_manager.set_power_mode('0')
            
            elif component == 'gui':
                gui_manager = GUIManager()
                if interactive:
                    current_status = gui_manager.get_gui_status()
                    if current_status['status'] == 'success':
                        console.print(f"\nCurrent status: {current_status['message']}")
                        enable = click.confirm("Enable GUI on boot?", default=True)
                        result = gui_manager.configure_gui(enable, interactive=True)
                    else:
                        result = current_status
                else:
                    # Non-interactive mode - enable GUI by default
                    result = gui_manager.configure_gui(True, interactive=False)
            
            # Display results
            if result:
                status = result.get('status', 'unknown')
                message = result.get('message', 'No message')
                
                if status == 'success':
                    console.print(f"\n[bold green]✅ {component.upper()} Configuration Completed![/bold green]")
                    console.print(f"[green]{message}[/green]")
                elif status == 'warning':
                    console.print(f"\n[yellow]⚠️ {component.upper()} Configuration Warning[/yellow]")
                    console.print(f"[yellow]{message}[/yellow]")
                elif status == 'error':
                    console.print(f"\n[red]❌ {component.upper()} Configuration Failed[/red]")
                    console.print(f"[red]{message}[/red]")
                    sys.exit(1)
                elif status == 'cancelled':
                    console.print(f"\n[yellow]Configuration cancelled[/yellow]")
                else:
                    console.print(f"\n[blue]ℹ️ {message}[/blue]")
                
                # Show additional details if available
                if result.get('details'):
                    details = result['details']
                    if isinstance(details, list):
                        for detail in details:
                            if isinstance(detail, tuple) and len(detail) == 2:
                                component_name, component_result = detail
                                console.print(f"  {component_name}: {component_result.get('message', 'N/A')}")
                            else:
                                console.print(f"  {detail}")
                    else:
                        console.print(f"  {details}")
            
        except Exception as e:
            console.print(f"[red]Error configuring {component}: {e}[/red]")
            if ctx.obj['verbose']:
                import traceback
                console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            sys.exit(1)

@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), 
              default='table', help='Output format')
@click.pass_context
def status(ctx, output_format):
    """Show current Jetson system status and configuration."""
    console.print(Panel("[bold blue]Jetson System Status[/bold blue]", expand=False))
    
    try:
        # Initialize managers
        system_manager = SystemManager()
        docker_manager = DockerManager()
        storage_manager = StorageManager()
        power_manager = PowerManager()
        gui_manager = GUIManager()
        
        # Gather status information
        status_info = {
            'platform': system_manager._get_platform_info(),
            'jetson': system_manager._get_jetson_specific_info(),
            'docker_installed': docker_manager.is_docker_installed(),
            'storage': storage_manager.get_storage_info(),
            'power': power_manager.get_current_power_mode(),
            'gui': gui_manager.get_gui_status()
        }
        
        if output_format == 'json':
            console.print(json.dumps(status_info, indent=2))
        else:
            # Table format
            table = Table()
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="magenta")
            table.add_column("Details", style="green")
            
            # Platform status
            platform_info = status_info['platform']
            jetson_status = "✅ Jetson Detected" if platform_info['is_jetson'] else "❌ Not Jetson"
            jetson_details = f"{platform_info['machine']} - {platform_info['system']}"
            table.add_row("Platform", jetson_status, jetson_details)
            
            # Jetson-specific info
            jetson_info = status_info['jetson']
            if jetson_info.get('available'):
                jetson_model = jetson_info.get('platform', 'Unknown Model')
                l4t_version = jetson_info.get('l4t_version', 'Unknown')
                table.add_row("Jetson Model", "✅ Available", f"{jetson_model} (L4T: {l4t_version})")
            
            # Docker status
            docker_status = "✅ Installed" if status_info['docker_installed'] else "❌ Not Installed"
            table.add_row("Docker", docker_status, "")
            
            # Storage info
            storage_info = status_info['storage']
            nvme_devices = storage_info.get('nvme_devices', [])
            if nvme_devices:
                nvme_status = f"✅ {len(nvme_devices)} device(s)"
                nvme_details = ", ".join([dev['name'] for dev in nvme_devices])
            else:
                nvme_status = "❌ No NVMe"
                nvme_details = ""
            table.add_row("NVMe Storage", nvme_status, nvme_details)
            
            # Swap info
            swap_info = storage_info.get('swap', {})
            swap_total = swap_info.get('total_formatted', '0 B')
            if swap_info.get('total', 0) > 0:
                swap_status = f"✅ {swap_total}"
                swap_used = swap_info.get('used_formatted', '0 B')
                swap_details = f"Used: {swap_used} ({swap_info.get('percent', 0):.1f}%)"
            else:
                swap_status = "❌ No Swap"
                swap_details = ""
            table.add_row("Swap", swap_status, swap_details)
            
            # Power status
            power_info = status_info['power']
            if power_info.get('status') == 'success':
                power_mode = power_info['mode_info'].get('name', 'Unknown')
                table.add_row("Power Mode", "✅ Available", power_mode)
            else:
                table.add_row("Power Mode", "❌ Unavailable", power_info.get('message', ''))
            
            # GUI status
            gui_info = status_info['gui']
            if gui_info.get('status') == 'success':
                gui_enabled = gui_info.get('gui_enabled_on_boot')
                gui_running = gui_info.get('gui_currently_running')
                
                if gui_enabled:
                    gui_status = "✅ Enabled on boot"
                else:
                    gui_status = "❌ Disabled on boot"
                
                gui_details = f"Currently running: {'Yes' if gui_running else 'No'}"
                table.add_row("GUI", gui_status, gui_details)
            else:
                table.add_row("GUI", "❌ Error", gui_info.get('message', ''))
            
            console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error getting system status: {e}[/red]")
        if ctx.obj['verbose']:
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        sys.exit(1)


@cli.command('disable-zram')
@click.pass_context
def disable_zram_cmd(ctx):
    """Disable zRAM and nvzramconfig service.
    
    This command will:
    - Stop and disable the nvzramconfig service
    - Disable all active zRAM swap devices
    - This change will persist across reboots
    
    Note: This command will use sudo internally for operations requiring root access.
    """
    try:
        console.print("🔧 Disabling zRAM...")
        
        from .sdk.storage import StorageManager
        storage_manager = StorageManager()
        
        with console.status("[bold yellow]Disabling zRAM devices and service..."):
            result = storage_manager.disable_zram()
        
        if result['status'] == 'success':
            console.print(f"[green]✅ {result['message']}[/green]")
            if 'details' in result:
                console.print("\nDetails:")
                for detail in result['details']:
                    console.print(f"  • {detail}")
        else:
            console.print(f"[red]❌ {result['message']}[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]Error disabling zRAM: {e}[/red]")
        verbose = ctx.obj.get('verbose') if ctx.obj else False
        if verbose:
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main()