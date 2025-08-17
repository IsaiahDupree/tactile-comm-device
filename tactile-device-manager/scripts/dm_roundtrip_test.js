// Simple round-trip test for Data Mode framing/CRC (Node script)
// Usage: npm run dm:test

const { encodeFrame, decodeFrame, Proto } = require('../src/lib/datamode/protocol');

function hex(u8) { return Buffer.from(u8).toString('hex'); }

function testOne(name, hdr, payload) {
  const out = encodeFrame(hdr, payload);
  const parsed = decodeFrame(out);
  const ok = parsed.header.ver === (hdr.ver ?? Proto.ver)
    && parsed.header.flags === (hdr.flags ?? 0)
    && parsed.header.seq === hdr.seq
    && parsed.header.ack === hdr.ack
    && parsed.header.type === hdr.type
    && parsed.header.win === hdr.win
    && parsed.header.len === payload.length
    && Buffer.compare(Buffer.from(parsed.payload), Buffer.from(payload)) === 0;
  console.log(`[${ok ? 'OK' : 'FAIL'}] ${name}: frame=${hex(out)} len=${out.length}`);
  if (!ok) {
    console.log('Expected:', hdr, payload);
    console.log('Parsed:  ', parsed.header, Buffer.from(parsed.payload));
    process.exitCode = 1;
  }
}

function run() {
  const cases = [
    {
      name: 'empty payload',
      hdr: { ver: 1, flags: 0, seq: 1, ack: 0, type: 0x01, win: 4 },
      payload: new Uint8Array(),
    },
    {
      name: 'hello world',
      hdr: { ver: 1, flags: 0x02, seq: 2, ack: 1, type: 0x10, win: 3 },
      payload: new TextEncoder().encode('hello world'),
    },
    {
      name: 'binary bytes',
      hdr: { ver: 1, flags: 0, seq: 65535, ack: 1234, type: 0x31, win: 8 },
      payload: new Uint8Array([0,1,2,3,4,250,251,252,253,254,255]),
    },
  ];

  for (const c of cases) {
    testOne(c.name, c.hdr, c.payload);
  }

  // Negative test: flip a bit
  const good = encodeFrame({ ver: 1, flags: 0, seq: 10, ack: 5, type: 0x42, win: 2 }, new Uint8Array([1,2,3]));
  const bad = new Uint8Array(good);
  bad[0] ^= 0x01; // corrupt 1 bit
  let threw = false;
  try { decodeFrame(bad); } catch (e) { threw = true; console.log(`[OK] crc mismatch detected: ${e.message}`); }
  if (!threw) { console.log('[FAIL] expected CRC mismatch'); process.exitCode = 1; }
}

run();
