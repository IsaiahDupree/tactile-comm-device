// Serial transport adapter (stub)
// Integrates with existing SerialPort usage in main process

export class SerialTransport {
  constructor(port) {
    this.port = port; // expected to look like a SerialPort instance
  }
  async begin() {
    // noop for now; assume port is already open
    return true;
  }
  async end() {
    // leave lifecycle to app for now
  }
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
