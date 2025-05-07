#!/usr/bin/env python3
"""
Deployment script for the Used Car Lead Generation Agent.
Handles environment setup, configuration validation, and scheduled job configuration.
"""

import os
import sys
import argparse
import subprocess
import json
from datetime import datetime

def check_environment():
    """
    Check the environment for required dependencies.
    
    Returns:
        bool: True if all checks pass, False otherwise
    """
    print("Checking environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"ERROR: Python 3.8+ is required. Found {python_version.major}.{python_version.minor}")
        return False
    print(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check for virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("WARNING: Not running in a virtual environment. It's recommended to use a virtual environment.")
    else:
        print("✓ Running in a virtual environment")
    
    # Check for required files
    required_files = [
        'main_agent.py',
        'requirements.txt',
        '.env'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"ERROR: Missing required files: {', '.join(missing_files)}")
        if '.env' in missing_files:
            print("  - Create .env file from .env.template")
        return False
    print("✓ All required files present")
    
    return True

def install_dependencies():
    """
    Install dependencies from requirements.txt.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False

def validate_configuration():
    """
    Validate the configuration in .env file.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    print("Validating configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("ERROR: .env file not found")
        return False
    
    # Import dotenv here to make sure it's installed
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("ERROR: python-dotenv package not installed")
        return False
    
    # Required environment variables
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER',
        'CLIENT_EMAIL',
        'CLIENT_PHONE_NUMBER',
        'GOOGLE_SHEET_ID'
    ]
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✓ Configuration validated successfully")
    
    # Warn about missing optional variables
    optional_vars = [
        'THRYV_API_KEY',
        'THRYV_ACCOUNT_ID',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD'
    ]
    
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    if missing_optional:
        print(f"WARNING: Missing optional environment variables: {', '.join(missing_optional)}")
        if 'THRYV_API_KEY' in missing_optional or 'THRYV_ACCOUNT_ID' in missing_optional:
            print("  - Thryv CRM integration will be skipped")
        if any(var in missing_optional for var in ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USERNAME', 'EMAIL_PASSWORD']):
            print("  - Email notifications will use alternative method or may not work")
    
    return True

def setup_scheduler():
    """
    Set up the scheduler for periodic runs.
    Creates a simple configuration file for the scheduler.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Setting up scheduler...")
    
    # Get scrape interval from environment
    from dotenv import load_dotenv
    load_dotenv()
    
    scrape_interval = int(os.getenv('SCRAPE_INTERVAL_HOURS', 4))
    
    # Create a scheduler configuration
    scheduler_config = {
        'jobs': [
            {
                'name': 'car_finder_agent',
                'command': f'{sys.executable} main_agent.py',
                'schedule': f'0 */{scrape_interval} * * *',  # Every N hours
                'enabled': True,
                'last_run': None
            }
        ],
        'configured_at': datetime.now().isoformat()
    }
    
    # Save the configuration
    try:
        with open('scheduler_config.json', 'w') as f:
            json.dump(scheduler_config, f, indent=2)
        print(f"✓ Scheduler configured to run every {scrape_interval} hours")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create scheduler configuration: {e}")
        return False

def run_test():
    """
    Run a test execution of the agent.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Running a test execution...")
    
    try:
        # Run with --mock and --dry-run flags
        result = subprocess.run(
            [sys.executable, 'main_agent.py', '--mock', '--dry-run'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Test execution successful")
            print("\nTest output (last 10 lines):")
            # Print the last 10 lines of output
            for line in result.stdout.strip().split('\n')[-10:]:
                print(f"  {line}")
            return True
        else:
            print(f"ERROR: Test execution failed with code {result.returncode}")
            print("\nError output:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"ERROR: Failed to run test: {e}")
        return False

def create_startup_scripts():
    """
    Create startup scripts for different platforms.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Creating startup scripts...")
    
    # Windows batch script
    try:
        with open('run_agent.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('echo Running Used Car Lead Generation Agent\n')
            f.write(f'"{sys.executable}" main_agent.py\n')
            f.write('if %ERRORLEVEL% NEQ 0 (\n')
            f.write('  echo Agent failed with error code %ERRORLEVEL%\n')
            f.write('  pause\n')
            f.write(')\n')
        
        # Unix shell script
        with open('run_agent.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Running Used Car Lead Generation Agent"\n')
            f.write(f'"{sys.executable}" main_agent.py\n')
            f.write('if [ $? -ne 0 ]; then\n')
            f.write('  echo "Agent failed with error code $?"\n')
            f.write('  read -p "Press enter to continue"\n')
            f.write('fi\n')
        
        # Make the shell script executable on Unix-like systems
        if os.name != 'nt':  # Not Windows
            os.chmod('run_agent.sh', 0o755)
        
        print("✓ Created startup scripts: run_agent.bat and run_agent.sh")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create startup scripts: {e}")
        return False

def main():
    """
    Main deployment function.
    """
    parser = argparse.ArgumentParser(description='Deploy the Used Car Lead Generation Agent')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation')
    parser.add_argument('--skip-test', action='store_true', help='Skip test execution')
    
    args = parser.parse_args()
    
    print("=== Used Car Lead Generation Agent Deployment ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment
    if not check_environment():
        print("\nEnvironment check failed. Please fix the issues and try again.")
        return 1
    
    # Install dependencies
    if not args.skip_deps:
        if not install_dependencies():
            print("\nDependency installation failed. Please fix the issues and try again.")
            return 1
    else:
        print("Skipping dependency installation (--skip-deps)")
    
    # Validate configuration
    if not validate_configuration():
        print("\nConfiguration validation failed. Please fix the issues and try again.")
        return 1
    
    # Set up scheduler
    if not setup_scheduler():
        print("\nScheduler setup failed. Please fix the issues and try again.")
        return 1
    
    # Create startup scripts
    if not create_startup_scripts():
        print("\nFailed to create startup scripts.")
        # Not critical, continue
    
    # Run test
    if not args.skip_test:
        if not run_test():
            print("\nTest execution failed. Please fix the issues before using in production.")
            print("You can run with --mock and --dry-run flags to troubleshoot without making API calls.")
            return 1
    else:
        print("Skipping test execution (--skip-test)")
    
    print("\n=== Deployment Summary ===")
    print("✓ Environment checked")
    if not args.skip_deps:
        print("✓ Dependencies installed")
    print("✓ Configuration validated")
    print("✓ Scheduler configured")
    print("✓ Startup scripts created")
    if not args.skip_test:
        print("✓ Test execution successful")
    
    print("\n=== Deployment Completed Successfully ===")
    print("To run the agent:")
    print("  - Windows: run_agent.bat")
    print("  - Unix/Linux/Mac: ./run_agent.sh")
    print("\nTo schedule periodic runs:")
    print("  - Use the system's scheduler (cron on Unix/Linux, Task Scheduler on Windows)")
    print("  - Sample crontab entry for Unix/Linux:")
    
    from dotenv import load_dotenv
    load_dotenv()
    scrape_interval = int(os.getenv('SCRAPE_INTERVAL_HOURS', 4))
    print(f"    0 */{scrape_interval} * * * cd {os.getcwd()} && ./run_agent.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 