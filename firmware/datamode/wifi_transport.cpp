#include "dm_transport.h"

namespace DM {

// Placeholder WiFi/TCP transport (scaffold)
class WifiTransport : public ITransport {
 public:
  bool begin() override { return false; } // not implemented
  void end() override {}
  int send(const uint8_t* data, size_t len) override { (void)data; (void)len; return -1; }
  RecvResult recv(uint8_t* buf, size_t cap) override { (void)buf; (void)cap; return {-1, 0}; }
};

} // namespace DM
