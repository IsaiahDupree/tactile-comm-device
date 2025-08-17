param(
    [string]$ComPort = "COM6",
    [int]$BaudRate = 9600,
    [string]$Command = "?",
    [int]$Timeout = 2000
)

# Create serial port object
$port = New-Object System.IO.Ports.SerialPort
$port.PortName = $ComPort
$port.BaudRate = $BaudRate
$port.DataBits = 8
$port.Parity = "None"
$port.StopBits = 1
$port.Handshake = "None"
$port.ReadTimeout = $Timeout
$port.WriteTimeout = $Timeout

try {
    Write-Host "Opening port $ComPort at $BaudRate baud..."
    $port.Open()
    
    if ($port.IsOpen) {
        Write-Host "Port opened successfully."
        
        # Send command
        Write-Host "Sending command: $Command"
        $port.WriteLine($Command)
        
        # Wait a bit for response
        Start-Sleep -Milliseconds 500
        
        # Read response
        $response = ""
        while ($port.BytesToRead -gt 0) {
            $response += $port.ReadLine()
            Start-Sleep -Milliseconds 50
        }
        
        if ($response) {
            Write-Host "Response received:"
            Write-Host $response
        } else {
            Write-Host "No response received within timeout period."
        }
    }
}
catch {
    Write-Host "Error: $_"
}
finally {
    # Close the port
    if ($port.IsOpen) {
        Write-Host "Closing port..."
        $port.Close()
    }
    $port.Dispose()
}
