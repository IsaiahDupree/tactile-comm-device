# Device Protocol Testing Suite

This directory contains a comprehensive pytest test suite for validating the tactile communication device's serial protocol.

## Installation

```bash
pip install -r requirements.txt
```

## Test Suite Features

- **Protocol Handshake**: Validates `^DATA? v1` → `DATA:OK v1` entry
- **Flag Management**: Tests `FLAG ON/OFF` and write protection
- **SD Card Stats**: Verifies `STAT` command returns reasonable values
- **File Operations**: Complete PUT → LS → GET → DEL round-trip testing
- **8.3 Filename Compliance**: Tests various 8.3 format filenames
- **Space Tracking**: Validates SD card free space changes with file operations
- **Noise Tolerance**: Robust to extra console output like `[DATA] mode=ENTER`
- **CRC Validation**: End-to-end data integrity verification

## Running Tests

### Basic Usage
```bash
# Windows
pytest -q --port COM6 --bank GENERA~1 --key J

# Linux/macOS  
pytest -q --port /dev/ttyACM0 --bank HUMAN --key A
```

### Environment Variables
Set these to avoid passing flags every time:
```bash
export TACTILE_PORT=COM6
export TACTILE_BAUD=9600
export TACTILE_BANK=GENERA~1
export TACTILE_KEY=J

pytest -q
```

### Individual Tests
```bash
# Test only flag operations
pytest -q tests/test_device_io.py::test_flag_toggle --port COM6

# Test only file round-trip
pytest -q tests/test_device_io.py::test_put_ls_get_del_roundtrip --port COM6 --bank HUMAN --key A

# Test 8.3 filename compliance
pytest -q tests/test_device_io.py::test_8_3_filename_compliance --port COM6 --bank GENERA~1 --key J
```

## Test Parameters

- `--port`: Serial port (e.g., COM6, /dev/ttyACM0)
- `--baud`: Baud rate (default: 9600)
- `--bank`: Audio bank (HUMAN or GENERA~1)
- `--key`: Key folder (A, B, C, ..., SHIFT, PERIOD, etc.)

## What Gets Tested

1. **test_stat_basic**: SD card stats return reasonable values
2. **test_flag_toggle**: Write flag can be toggled ON/OFF
3. **test_put_ls_get_del_roundtrip**: Complete file lifecycle with CRC validation
4. **test_8_3_filename_compliance**: Various 8.3 format names work correctly
5. **test_sd_space_tracking**: Free space decreases/increases with file operations

## Expected Output

```
$ pytest -q --port COM6 --bank GENERA~1 --key J
.....                                                    [100%]
5 passed in 12.34s
```

## Troubleshooting

**No device response**: 
- Check port name and baud rate
- Ensure device is connected and powered
- Verify SD card is inserted

**Test failures**:
- Check SD card has free space
- Ensure target bank/key directory exists
- Verify device firmware matches expected protocol

**Timeout errors**:
- Increase timeout values in test file if needed
- Check for serial communication issues
- Ensure stable USB connection

## Integration with CI/CD

This test suite can be integrated into automated testing pipelines:

```yaml
# Example GitHub Actions
- name: Test Device Protocol
  run: |
    pip install -r requirements.txt
    pytest -q --port ${{ secrets.DEVICE_PORT }} --bank GENERA~1 --key J
```

The tests are designed to be robust and handle real-world serial communication issues while providing comprehensive validation of the device protocol.
