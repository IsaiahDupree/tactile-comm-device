#!/usr/bin/env python3
import os
import sys
import subprocess

def create_sample_mp3():
    """Create a minimal sample MP3 file for testing"""
    data = b'ID3\x03\x00\x00\x00\x00\x00\x00' + b'\xff\xfb\x90\x00' * 100
    with open('sample.mp3', 'wb') as f:
        f.write(data)
    print(f"Created sample.mp3: {len(data)} bytes")

def run_pytest():
    """Run pytest with proper Python path"""
    create_sample_mp3()
    
    # Ensure test_results directory exists
    os.makedirs('test_results', exist_ok=True)
    
    # Add current directory to Python path
    env = os.environ.copy()
    current_dir = os.getcwd()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = current_dir
    
    # Run pytest with verbose output
    cmd = [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=long', '-s']
    
    try:
        print(f"Running: {' '.join(cmd)}")
        print(f"PYTHONPATH: {env.get('PYTHONPATH', 'Not set')}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        
        # Write results to file
        with open('test_results/pytest_output_fixed.txt', 'w') as f:
            f.write("PYTEST OUTPUT (FIXED)\n")
            f.write("=" * 50 + "\n")
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"PYTHONPATH: {env.get('PYTHONPATH')}\n")
            f.write(f"Return code: {result.returncode}\n\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)
        
        print("Test results written to test_results/pytest_output_fixed.txt")
        print(f"Return code: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("Tests timed out after 120 seconds")
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    run_pytest()
