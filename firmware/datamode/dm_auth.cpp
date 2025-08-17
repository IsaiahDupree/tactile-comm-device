#include "dm_auth.h"

namespace DM {

void Auth::genNonce(AuthState& st) {
  // TODO: replace with real RNG
  for (int i = 0; i < 16; ++i) st.nonce[i] = static_cast<uint8_t>(i * 13 + 7);
}

bool Auth::verify(AuthState& st, const uint8_t* token, size_t tokenLen,
                  const uint8_t* proof, size_t proofLen) {
  (void)st; (void)token; (void)tokenLen; (void)proof; (void)proofLen;
  // TODO: implement HMAC(token, nonce) or similar
  return false;
}

} // namespace DM
