import sys
import subprocess
import os
import glob
import atexit
import shutil

# FIXME: Still need to add the following
#  - Update ConfigOverride.xcconfig to set the timezone
#    (currently hardcoded to America/Los_Angeles)
#  - Lookup the simulator ID (currently hardcoded to my iPhone 16
#    running iOS 18.4)
#  - Do some checks for ../Trio-dev to make sure that it's on the
#    oref-swift branch and doesn't have pending changes

def run_xcode_test(func):
    command = None
    if func == 'meal':
        command = [
            'xcodebuild', 'test',
            '-workspace', '../Trio-dev/Trio.xcworkspace',
            '-scheme', 'Trio Tests',
            '-destination', 'platform=iOS Simulator,id=6ED95A27-FD5A-41D9-A44E-213787DBB319',
            '-only-testing', 'TrioTests/MealJsonTests'
        ]
    elif func == 'autosens':
        command = [
            'xcodebuild', 'test',
            '-workspace', '../Trio-dev/Trio.xcworkspace',
            '-scheme', 'Trio Tests',
            '-destination', 'platform=iOS Simulator,id=6ED95A27-FD5A-41D9-A44E-213787DBB319',
            '-only-testing', 'TrioTests/AutosensJsonTests'
        ]
    elif func == 'iob':
        command = [
            'xcodebuild', 'test',
            '-workspace', '../Trio-dev/Trio.xcworkspace',
            '-scheme', 'Trio Tests',
            '-destination', 'platform=iOS Simulator,id=6ED95A27-FD5A-41D9-A44E-213787DBB319',
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

    # Store the command line argument
    input_date = sys.argv[1]

    # Start serve_errors.py in the background
    # Use preexec_fn=os.setsid to create a new process group.
    # This allows us to kill the entire process group, including any children.
    serve_process = subprocess.Popen(['python', 'serve_errors.py'], preexec_fn=os.setsid)

    def cleanup():
        """
        This function is registered to run at script exit.
        It terminates the serve_errors.py process group.
        """
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
                try:
                    run_xcode_test(func)
                    results[func]['xcode_pass'] = True
                    print("  - Xcode tests passed.")
                except subprocess.CalledProcessError:
                    results[func]['xcode_pass'] = False
                    print("  - Xcode tests failed.")
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

