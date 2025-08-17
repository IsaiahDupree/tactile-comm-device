#pragma once

#include <stdint.h>
#include <stddef.h>

namespace DM {

struct JournalEntry {
  uint32_t ts;
  uint8_t  op;     // begin/put/data/done/commit/abort
  uint8_t  flags;
  uint16_t len;    // payload length
  // payload follows (path, offsets, crc, etc.)
};

class Journal {
 public:
  static bool append(const uint8_t* data, size_t len);   // stub
  static bool replay();                                  // stub
  static bool clear();                                   // stub
};

} // namespace DM
