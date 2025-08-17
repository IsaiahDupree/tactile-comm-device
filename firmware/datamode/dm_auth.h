#pragma once

#include <stdint.h>
#include <stddef.h>

namespace DM {

struct AuthState {
  bool authed = false;
  uint8_t nonce[16] = {0};
};

class Auth {
 public:
  // Generate a random nonce (stub)
  static void genNonce(AuthState& st);
  // Verify token+nonce response (stub)
  static bool verify(AuthState& st, const uint8_t* token, size_t tokenLen,
                     const uint8_t* proof, size_t proofLen);
};

} // namespace DM
