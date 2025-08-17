// Telemetry counters and helpers (stub)

export class Telemetry {
  constructor() {
    this.counters = {
      framesTx: 0,
      framesRx: 0,
      acksTx: 0,
      acksRx: 0,
      crcErr: 0,
      timeouts: 0,
    };
  }
  reset() { Object.keys(this.counters).forEach(k => this.counters[k] = 0); }
}
