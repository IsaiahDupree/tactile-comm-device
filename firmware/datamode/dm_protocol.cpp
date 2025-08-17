#include "dm_protocol.h"

namespace DM {

// Simple CRC32 (polynomial 0xEDB88320) — reference implementation (stub-friendly)
static uint32_t crc32_update(uint32_t crc, uint8_t byte) {
  crc ^= byte;
  for (int i = 0; i < 8; ++i) {
    uint32_t mask = -(crc & 1u);
    crc = (crc >> 1) ^ (0xEDB88320u & mask);
  }
  return crc;
}

uint32_t crc32(const uint8_t* data, size_t len, uint32_t seed) {
  uint32_t crc = seed;
  for (size_t i = 0; i < len; ++i) crc = crc32_update(crc, data[i]);
  return ~crc;
}

int encodeFrame(const FrameHeader& hdr, const uint8_t* payload, size_t payloadLen,
                uint8_t* outBuf, size_t outCap) {
  if (!outBuf) return -1;
  if (payloadLen > 0 && !payload) return -2;

  const size_t headerLen = sizeof(FrameHeader);
  const size_t totalNoCrc = headerLen + payloadLen;
  const size_t totalWithCrc = totalNoCrc + 4;
  if (outCap < totalWithCrc) return -3;

  // Copy header
  FrameHeader* outHdr = reinterpret_cast<FrameHeader*>(outBuf);
  *outHdr = hdr;

  // Copy payload
  if (payloadLen) {
    uint8_t* dst = outBuf + headerLen;
    for (size_t i = 0; i < payloadLen; ++i) dst[i] = payload[i];
  }

  // CRC over header+payload
  uint32_t crc = crc32(outBuf, totalNoCrc);
  outBuf[totalNoCrc + 0] = static_cast<uint8_t>(crc);
  outBuf[totalNoCrc + 1] = static_cast<uint8_t>(crc >> 8);
  outBuf[totalNoCrc + 2] = static_cast<uint8_t>(crc >> 16);
  outBuf[totalNoCrc + 3] = static_cast<uint8_t>(crc >> 24);

  return static_cast<int>(totalWithCrc);
}

int decodeFrame(const uint8_t* inBuf, size_t inLen,
                FrameHeader* outHdr, const uint8_t** outPayload, size_t* outPayloadLen) {
  if (!inBuf || inLen < sizeof(FrameHeader) + 4) return -1;

  const FrameHeader* hdr = reinterpret_cast<const FrameHeader*>(inBuf);
  size_t payloadLen = hdr->len;
  size_t totalNoCrc = sizeof(FrameHeader) + payloadLen;
  size_t totalWithCrc = totalNoCrc + 4;
  if (inLen < totalWithCrc) return -2;

  // Verify CRC
  uint32_t expect = (static_cast<uint32_t>(inBuf[totalNoCrc + 0])      ) |
                    (static_cast<uint32_t>(inBuf[totalNoCrc + 1]) << 8 ) |
                    (static_cast<uint32_t>(inBuf[totalNoCrc + 2]) << 16) |
                    (static_cast<uint32_t>(inBuf[totalNoCrc + 3]) << 24);
  uint32_t actual = crc32(inBuf, totalNoCrc);
  if (expect != actual) return -3;

  if (outHdr) *outHdr = *hdr;
  if (outPayload) *outPayload = inBuf + sizeof(FrameHeader);
  if (outPayloadLen) *outPayloadLen = payloadLen;
  return static_cast<int>(totalWithCrc);
}

} // namespace DM
