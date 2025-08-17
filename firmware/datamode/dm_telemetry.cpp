#include "dm_telemetry.h"

namespace DM {

static TelemetryCounters g_counters;

TelemetryCounters& Telemetry::counters() { return g_counters; }

} // namespace DM
