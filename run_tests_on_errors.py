import sys
import subprocess
import os
import glob
import atexit
import shutil
import json


def check_trio_dev_repo():
    """
    Checks if the ../Trio-dev directory is a git repository,
    is on the 'oref-swift' branch, and has no pending changes.
    """
    trio_dev_path = '../Trio-dev'
    if not os.path.isdir(os.path.join(trio_dev_path, '.git')):
        print(f"Error: {trio_dev_path} is not a git repository.")
        sys.exit(1)

    # Check branch
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=trio_dev_path, capture_output=True, text=True, check=True
    )
    branch = result.stdout.strip()
    if branch != 'oref-swift':
        print(f"Error: {trio_dev_path} is not on the 'oref-swift' branch (current branch: {branch}).")
        sys.exit(1)

    # Check for pending changes
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=trio_dev_path, capture_output=True, text=True, check=True
    )
    if result.stdout:
        print(f"Error: {trio_dev_path} has pending changes.")
        print(result.stdout)
        sys.exit(1)
    
    print("../Trio-dev repo is clean and on the correct branch.")


def get_simulator_id():
    """
    Finds a suitable iOS simulator ID.
    """
    try:
        # Get the list of available simulators in JSON format
        result = subprocess.run(
            ['xcrun', 'simctl', 'list', 'devices', 'available', '-j'],
            capture_output=True, text=True, check=True
        )
        simulators = json.loads(result.stdout)
        
        # Find the latest available iPhone simulator
        best_simulator = None
        latest_ios_version = "0.0"
        
        for runtime_id, devices in simulators['devices'].items():
            if 'com.apple.CoreSimulator.SimRuntime.iOS' not in runtime_id:
                continue
            
            version_str = runtime_id.split('iOS-')[-1].replace('-', '.')

            for device in devices:
                if device.get('isAvailable') and 'com.apple.CoreSimulator.SimDeviceType.iPhone' in device.get('deviceTypeIdentifier', ''):
                    if version_str > latest_ios_version:
                        latest_ios_version = version_str
                        best_simulator = device
                            
        if best_simulator:
            print(f"Found simulator: {best_simulator['name']} ({best_simulator['udid']})")
            return best_simulator['udid']
        else:
            print("Warning: Could not find an available iPhone simulator.")
            return None
            
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not get simulator ID: {e}")
        return None


def extract_timezones_from_errors():
    """
    Scans the 'errors' directory for JSON files and extracts the 'timezone'
    field from each file.

    Returns:
        A set of unique timezone strings.
    """
    timezones = set()
    error_files = glob.glob(os.path.join('errors', '*.json'))
    for error_file in error_files:
        with open(error_file, 'r') as f:
            try:
                data = json.load(f)
                if 'timezone' in data:
                    timezones.add(data['timezone'])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {error_file}")
    return timezones


def run_xcode_test(func, simulator_id):
    if not simulator_id:
        print("Skipping Xcode test due to missing simulator ID.")
        return

    command = None
    destination = f'platform=iOS Simulator,id={simulator_id}'

    if func == 'meal':
        command = [
            'xcodebuild', 'test',
            '-workspace', '../Trio-dev/Trio.xcworkspace',
            '-scheme', 'Trio Tests',
            '-destination', destination,
            '-only-testing', 'TrioTests/MealJsonTests'
        ]
    elif func == 'autosens':
        command = [
            'xcodebuild', 'test',
            '-workspace', '../Trio-dev/Trio.xcworkspace',
            '-scheme', 'Trio Tests',
            '-destination', destination,
            '-only-testing', 'TrioTests/AutosensJsonTests'
        ]
    elif func == 'iob':
        command = [
            'xcodebuild', 'test',
            '-workspace', '../Trio-dev/Trio.xcworkspace',
            '-scheme', 'Trio Tests',
            '-destination', destination,
            '-only-testing', 'TrioTests/IobJsonTests'
        ]
    
    if command:
        subprocess.run(command, check=True)


def main():
    """
    This script performs the same actions as the run_tests_on_errors.sh script.
    It checks for a date argument, starts serve_errors.py in the background,
    cleans the errors/ directory, and then runs extract_errors.sh.
    The serve_errors.py process is terminated automatically on script exit.
    """
    # Check if an argument was provided
    if len(sys.argv) != 2:
        print("Usage: python run_tests_on_errors.py YYYY-MM-DD")
        print("Example: python run_tests_on_errors.py 2025-03-15")
        sys.exit(1)

    check_trio_dev_repo()
    simulator_id = get_simulator_id()

    # Store the command line argument
    input_date = sys.argv[1]

    # Start serve_errors.py in the background
    # Use preexec_fn=os.setsid to create a new process group.
    # This allows us to kill the entire process group, including any children.
    serve_process = subprocess.Popen(['python', 'serve_errors.py'], preexec_fn=os.setsid)

    config_override_path = '../Trio-dev/ConfigOverride.xcconfig'
    config_override_backup_path = config_override_path + '.bak'
    if os.path.exists(config_override_path):
        shutil.copy(config_override_path, config_override_backup_path)
    
    def cleanup():
        """
        This function is registered to run at script exit.
        It terminates the serve_errors.py process group.
        """
        if os.path.exists(config_override_backup_path):
            shutil.move(config_override_backup_path, config_override_path)
        os.killpg(os.getpgid(serve_process.pid), 15) # 15 is the SIGTERM signal
        serve_process.wait()

    atexit.register(cleanup)

    # Initialize a dictionary to store the results
    results = {}

    # Run extract_errors.sh on each function then run the tests if there are any
    for func in ['autosens', 'determineBasal', 'iob', 'profile', 'meal']:
        print(f"Checking {func}")
        # Clean the errors directory
        errors_dir = 'errors'
        if os.path.exists(errors_dir):
            shutil.rmtree(errors_dir)
        os.makedirs(errors_dir)
        
        try:
            subprocess.run(['./extract_errors.sh', func, input_date], check=True)
        except subprocess.CalledProcessError as e:
            print(f"extract_errors.sh failed with exit code {e.returncode}")
            sys.exit(1)

        # Check for files in the errors directory
        error_files = os.listdir(errors_dir)
        results[func] = {'errors': len(error_files), 'xcode_pass': None}
        if not error_files:
            print("  - No errors found in the 'errors' directory.")
        else:
            print(f"  - {len(error_files)} errors found. Running Xcode tests...")
            if func in ['meal', 'autosens', 'iob']:
                if not simulator_id:
                    print("  - No simulator found. Skipping tests.")
                    continue

                timezones = extract_timezones_from_errors()
                if not timezones:
                    print("  - No timezones found in error files. Skipping Xcode tests.")
                    results[func]['xcode_pass'] = None
                else:
                    print(f"  - Found timezones: {', '.join(timezones)}")
                    all_passed = True
                    for timezone in timezones:
                        print(f"  - Testing with timezone: {timezone}")
                        try:
                            # Update config file
                            config_content = f"ENABLE_REPLAY_TESTS = YES\nREPLAY_TEST_TIMEZONE = {timezone}\n"
                            with open(config_override_path, 'w') as f:
                                f.write(config_content)
                            
                            run_xcode_test(func, simulator_id)
                            print(f"    - Xcode tests passed for timezone: {timezone}")
                        except subprocess.CalledProcessError:
                            print(f"    - Xcode tests failed for timezone: {timezone}")
                            all_passed = False
                    
                    results[func]['xcode_pass'] = all_passed
                    if all_passed:
                        print("  - All Xcode tests passed.")
                    else:
                        print("  - Some Xcode tests failed.")
            else:
                print("  - No Xcode tests defined for this function.")


    # Print the summary
    print("\n--- Summary---")
    for func, result in results.items():
        error_count = result['errors']
        xcode_status = "N/A"
        if result['xcode_pass'] is True:
            xcode_status = "✅"
        elif result['xcode_pass'] is False:
            xcode_status = "❌"
        
        print(f"- {func}: {error_count} errors, Xcode tests: {xcode_status}")


if __name__ == "__main__":
    main()

