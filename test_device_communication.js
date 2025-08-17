const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');

// Test communication with the tactile device
async function testDeviceCommunication() {
    console.log('🔍 Scanning for Arduino devices...');
    
    try {
        const ports = await SerialPort.list();
        console.log('\n📋 Available serial ports:');
        ports.forEach(port => {
            console.log(`  ${port.path}: ${port.manufacturer || 'Unknown'} - ${port.productId || 'N/A'}`);
        });
        
        // Try to connect to COM6 (the device we detected)
        const devicePort = 'COM6';
        console.log(`\n🔌 Attempting to connect to ${devicePort}...`);
        
        const port = new SerialPort({
            path: devicePort,
            baudRate: 115200,
            autoOpen: false
        });
        
        const parser = port.pipe(new ReadlineParser({ delimiter: '\n' }));
        
        port.open((err) => {
            if (err) {
                console.error('❌ Failed to open port:', err.message);
                return;
            }
            
            console.log('✅ Connected successfully!');
            console.log('📡 Listening for device messages...');
            
            // Listen for data from device
            parser.on('data', (data) => {
                console.log(`📥 Device: ${data.trim()}`);
            });
            
            // Send test commands after a short delay
            setTimeout(() => {
                console.log('\n🧪 Sending test commands...');
                
                // Send info command
                console.log('📤 Sending: I (Get Info)');
                port.write('I\n');
                
                setTimeout(() => {
                    // Send status command
                    console.log('📤 Sending: S (Get Status)');
                    port.write('S\n');
                }, 1000);
                
                setTimeout(() => {
                    // Send help command
                    console.log('📤 Sending: H (Help)');
                    port.write('H\n');
                }, 2000);
                
                setTimeout(() => {
                    console.log('\n✋ Test complete. Press Ctrl+C to exit.');
                }, 3000);
                
            }, 1000);
        });
        
        // Handle errors
        port.on('error', (err) => {
            console.error('❌ Serial port error:', err.message);
        });
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

// Run the test
testDeviceCommunication();
