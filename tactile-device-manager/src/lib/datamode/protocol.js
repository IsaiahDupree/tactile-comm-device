// Data Mode Protocol (desktop) - CommonJS variant for Electron main process
// Frame layout: header {ver,flags,seq,ack,type,win,len} + CRC32

const Proto = { ver: 1 };

const MsgType = Object.freeze({
  CTRL_GET_INFO: 0x01,
  AUTH_INIT: 0x02,
  AUTH_PROVE: 0x03,
  FS_BEGIN: 0x10,
  FS_PUT: 0x11,
  FS_DATA: 0x12,
  FS_RESUME: 0x13,
  FS_DONE: 0x14,
  FS_COMMIT: 0x15,
  FS_ABORT: 0x16,
  ROLLBACK_LAST: 0x17,
  DIAG_SD_FREE: 0x20,
  DIAG_I2C_SCAN: 0x21,
  DIAG_READ_BTNS: 0x22,
  SET_VOLUME: 0x30,
  BEEP: 0x31,
  LED: 0x32,
  LOG_START: 0x40,
  LOG_STOP: 0x41,
  LOG_CHUNK: 0x42,
});

function crc32(buf) {
  let crc = 0xFFFFFFFF >>> 0;
  for (let i = 0; i < buf.length; i++) {
    crc ^= buf[i];
    for (let j = 0; j < 8; j++) {
      const mask = -(crc & 1);
      crc = (crc >>> 1) ^ (0xEDB88320 & mask);
    }
  }
  return (~crc) >>> 0;
}

function encodeFrame(hdr, payload = new Uint8Array()) {
  const header = new Uint8Array(8);
  header[0] = hdr.ver ?? Proto.ver;
  header[1] = hdr.flags ?? 0;
  header[2] = hdr.seq & 0xFF; header[3] = (hdr.seq >> 8) & 0xFF;
  header[4] = hdr.ack & 0xFF; header[5] = (hdr.ack >> 8) & 0xFF;
  header[6] = hdr.type & 0xFF;
  header[7] = hdr.win & 0xFF;

  const len = new Uint8Array(2);
  len[0] = payload.length & 0xFF; len[1] = (payload.length >> 8) & 0xFF;

  const noCrc = new Uint8Array(header.length + len.length + payload.length);
  noCrc.set(header, 0);
  noCrc.set(len, header.length);
  noCrc.set(payload, header.length + len.length);

  const c = crc32(noCrc);
  const crc = new Uint8Array([c & 0xFF, (c >>> 8) & 0xFF, (c >>> 16) & 0xFF, (c >>> 24) & 0xFF]);

  const out = new Uint8Array(noCrc.length + 4);
  out.set(noCrc, 0);
  out.set(crc, noCrc.length);
  return out;
}

function decodeFrame(buf) {
  if (buf.length < 8 + 2 + 4) throw new Error('short frame');
  const ver = buf[0], flags = buf[1];
  const seq = buf[2] | (buf[3] << 8);
  const ack = buf[4] | (buf[5] << 8);
  const type = buf[6], win = buf[7];
  const len = buf[8] | (buf[9] << 8);
  const totalNoCrc = 10 + len;
  if (buf.length < totalNoCrc + 4) throw new Error('incomplete frame');
  const expect = (buf[totalNoCrc]) | (buf[totalNoCrc+1] << 8) | (buf[totalNoCrc+2] << 16) | (buf[totalNoCrc+3] << 24);
  const actual = crc32(buf.subarray(0, totalNoCrc)) >>> 0;
  if ((expect >>> 0) !== actual) throw new Error('crc mismatch');
  return {
    header: { ver, flags, seq, ack, type, win, len },
    payload: buf.subarray(10, 10 + len)
  };
}

module.exports = { Proto, MsgType, crc32, encodeFrame, decodeFrame };
