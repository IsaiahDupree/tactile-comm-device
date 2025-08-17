// TCP/WebSocket transport adapter (CommonJS stub)

class TcpTransport {
  constructor(client) {
    this.client = client; // net.Socket or WebSocket-like
  }
  async begin() { return true; }
  async end() {}
  async send(buf) {
    if (this.client.send) {
      this.client.send(Buffer.from(buf));
      return buf.length;
    }
    if (this.client.write) {
      return new Promise((resolve, reject) => {
        this.client.write(Buffer.from(buf), (err) => err ? reject(err) : resolve(buf.length));
      });
    }
    throw new Error('unsupported client');
  }
  onData(cb) {
    if (this.client.on) this.client.on('data', (chunk) => cb(new Uint8Array(chunk)));
    if (this.client.addEventListener) this.client.addEventListener('message', (ev) => cb(new Uint8Array(ev.data)));
  }
}

module.exports = { TcpTransport };
