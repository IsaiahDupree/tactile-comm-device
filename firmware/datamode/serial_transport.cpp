#include "dm_transport.h"

namespace DM {

// Placeholder Serial transport (no Arduino deps here to keep it portable for now)
class SerialTransport : public ITransport {
 public:
  bool begin() override { return true; }
  void end() override {}
  int send(const uint8_t* data, size_t len) override { (void)data; (void)len; return 0; }
  RecvResult recv(uint8_t* buf, size_t cap) override { (void)buf; (void)cap; return {0, 0}; }
};

} // namespace DM
