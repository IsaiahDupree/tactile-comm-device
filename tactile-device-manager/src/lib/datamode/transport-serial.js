// Serial transport adapter (CommonJS stub)
// Integrates with existing SerialPort usage in main process

class SerialTransport {
  constructor(port) {
    this.port = port; // expected to look like a SerialPort instance
  }
  async begin() { return true; }
  async end() {}
  async send(buf) {
    return new Promise((resolve, reject) => {
      this.port.write(Buffer.from(buf), (err) => {
        if (err) return reject(err);
        resolve(buf.length);
      });
    });
  }
  onData(cb) {
    this.port.on('data', (chunk) => cb(new Uint8Array(chunk)));
  }
}

module.exports = { SerialTransport };
