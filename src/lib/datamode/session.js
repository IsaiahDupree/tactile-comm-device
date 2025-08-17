// Data Mode session orchestrator (stub)
// Handles handshake, windowed ACKs, retries/backoff, and resumable transfers

import { Proto, MsgType, encodeFrame, decodeFrame } from './protocol';

export class DMSession {
  constructor(transport, opts = {}) {
    this.t = transport;
    this.seq = 1;
    this.ack = 0;
    this.win = opts.window || 4;
    this.pending = new Map(); // seq -> {buf, ts}
    this.onFrame = opts.onFrame || (() => {});
    this.onError = opts.onError || ((e) => console.error('[DM]', e));
  }

  async begin() {
    await this.t.begin();
    this.t.onData((chunk) => this._ingest(chunk));
  }

  async end() { await this.t.end(); }

  _send(type, payload = new Uint8Array(), flags = 0) {
    const hdr = { ver: Proto.ver, flags, seq: this.seq, ack: this.ack, type, win: this.win };
    hdr.len = payload.length; // only used in JS encoder; fw packs len separately
    const frame = encodeFrame(hdr, payload);
    // Track for potential retransmit
    this.pending.set(this.seq, { buf: frame, ts: Date.now() });
    this.seq = (this.seq + 1) & 0xFFFF;
    return this.t.send(frame);
  }

  _ingest(buf) {
    try {
      const { header, payload } = decodeFrame(buf);
      // Update cumulative ack from peer
      this.ack = header.ack;
      // Drop acknowledged frames
      for (const [k, v] of this.pending) {
        if (((k - this.ack) & 0xFFFF) <= 0x7FFF) this.pending.delete(k);
      }
      this.onFrame(header, payload);
    } catch (e) {
      this.onError(e);
    }
  }

  // Example verbs
  async getInfo() { return this._send(MsgType.CTRL_GET_INFO); }
  async authInit() { return this._send(MsgType.AUTH_INIT); }
  async authProve(proof) { return this._send(MsgType.AUTH_PROVE, proof); }
}
