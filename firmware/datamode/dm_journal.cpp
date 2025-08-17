#include "dm_journal.h"

namespace DM {

bool Journal::append(const uint8_t* data, size_t len) {
  (void)data; (void)len; return false; // TODO
}

bool Journal::replay() {
  return true; // TODO: scan journal and roll-forward/abort
}

bool Journal::clear() {
  return true; // TODO: truncate journal safely
}

} // namespace DM
