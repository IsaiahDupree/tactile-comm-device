#pragma once

// Data Mode Protocol - framing and message definitions (stubs)
// NOTE: This is scaffolding only; not compiled by Arduino sketch yet.

#include <stdint.h>
#include <stddef.h>

namespace DM {

// Protocol version
static const uint8_t kProtoVer = 1;

// Frame types (subset, expand as needed)
enum class MsgType : uint8_t {
  CTRL_GET_INFO = 0x01,
  AUTH_INIT     = 0x02,
  AUTH_PROVE    = 0x03,
  FS_BEGIN      = 0x10,
  FS_PUT        = 0x11,
  FS_DATA       = 0x12,
  FS_RESUME     = 0x13,
  FS_DONE       = 0x14,
  FS_COMMIT     = 0x15,
  FS_ABORT      = 0x16,
  ROLLBACK_LAST = 0x17,
  DIAG_SD_FREE  = 0x20,
  DIAG_I2C_SCAN = 0x21,
  DIAG_READ_BTNS= 0x22,
  SET_VOLUME    = 0x30,
  BEEP          = 0x31,
  LED           = 0x32,
  LOG_START     = 0x40,
  LOG_STOP      = 0x41,
  LOG_CHUNK     = 0x42,
};

// Frame header (little-endian)
#pragma pack(push,1)
struct FrameHeader {
  uint8_t  ver;    // kProtoVer
  uint8_t  flags;  // bit flags (e.g., HAS_ACK, MORE, etc.)
  uint16_t seq;    // sender sequence
  uint16_t ack;    // cumulative ACK
  uint8_t  type;   // MsgType
  uint8_t  win;    // advertised window
  uint16_t len;    // payload length (bytes)
};
#pragma pack(pop)

// CRC32 API
uint32_t crc32(const uint8_t* data, size_t len, uint32_t seed = 0xFFFFFFFFu);

// Encode/decode stubs
// Returns number of bytes written/consumed or negative on error.
int encodeFrame(const FrameHeader& hdr, const uint8_t* payload, size_t payloadLen,
                uint8_t* outBuf, size_t outCap);
int decodeFrame(const uint8_t* inBuf, size_t inLen,
                FrameHeader* outHdr, const uint8_t** outPayload, size_t* outPayloadLen);

} // namespace DM
