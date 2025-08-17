#pragma once

#include <stdint.h>
#include <stddef.h>

namespace DM {

struct RecvResult {
  int n;     // bytes read, 0 = no data, <0 error
  int err;   // optional platform error code
};

class ITransport {
 public:
  virtual ~ITransport() {}
  virtual bool begin() = 0;
  virtual void end() = 0;
  virtual int send(const uint8_t* data, size_t len) = 0; // returns bytes sent or <0
  virtual RecvResult recv(uint8_t* buf, size_t cap) = 0;  // non-blocking preferred
};

} // namespace DM
