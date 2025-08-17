#pragma once

#include <stdint.h>

namespace DM {

struct TelemetryCounters {
  uint32_t framesTx = 0;
  uint32_t framesRx = 0;
  uint32_t acksTx = 0;
  uint32_t acksRx = 0;
  uint32_t crcErr = 0;
  uint32_t timeouts = 0;
};

class Telemetry {
 public:
  static TelemetryCounters& counters();
};

} // namespace DM
