#include <SPI.h>
#include <SD.h>

// Adjust chip select pin as needed for your shield
#ifndef SD_CS_PIN
#define SD_CS_PIN 10
#endif

// Simple line-based protocol over Serial at 115200
// Commands:
//   PING -> OK
//   MKDIR <path>
//   LIST <path>
//   EXISTS <path>
//   DEL <path>
//   GET <path>
//   PUT <path> <size> (then raw <size> bytes)
// Responses are text lines terminated with \n. Binary follows only for GET.

static String readLine() {
  static String line;
  line = "";
  while (true) {
    while (Serial.available()) {
      char c = (char)Serial.read();
      if (c == '\n') return line;
      if (c != '\r') line += c;
    }
  }
}

void printlnOK() { Serial.println(F("OK")); }
void printlnERR(const __FlashStringHelper* msg) { Serial.print(F("ERR ")); Serial.println(msg); }
void printlnERRS(const String &msg) { Serial.print(F("ERR ")); Serial.println(msg); }

bool writeFile(const String &path, size_t size) {
  File f = SD.open(path.c_str(), FILE_WRITE);
  if (!f) return false;
  size_t remaining = size;
  uint8_t buf[64];
  while (remaining > 0) {
    size_t chunk = remaining > sizeof(buf) ? sizeof(buf) : remaining;
    size_t got = 0;
    while (got < chunk) {
      if (Serial.available()) {
        buf[got++] = (uint8_t)Serial.read();
      }
    }
    size_t written = f.write(buf, chunk);
    if (written != chunk) { f.close(); return false; }
    remaining -= chunk;
  }
  f.flush();
  f.close();
  return true;
}

bool sendFile(const String &path) {
  File f = SD.open(path.c_str(), FILE_READ);
  if (!f) return false;
  // Send size first
  Serial.println(f.size());
  uint8_t buf[64];
  while (true) {
    int n = f.read(buf, sizeof(buf));
    if (n <= 0) break;
    Serial.write(buf, n);
  }
  f.close();
  return true;
}

void listDir(const String &path) {
  File dir = SD.open(path.c_str());
  if (!dir || !dir.isDirectory()) { printlnERR(F("NOT_DIR")); return; }
  printlnOK();
  File entry;
  while ((entry = dir.openNextFile())) {
    Serial.print(entry.name());
    Serial.print(',');
    Serial.print(entry.isDirectory() ? F("D") : F("F"));
    Serial.print(',');
    Serial.println(entry.size());
    entry.close();
  }
  Serial.println(F("END"));
  dir.close();
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println(F("ERR SD_INIT"));
  } else {
    Serial.println(F("OK SD_READY"));
  }
}

void loop() {
  if (!Serial.available()) return;
  String line = readLine();
  if (line.length() == 0) return;

  int sp1 = line.indexOf(' ');
  String cmd = (sp1 < 0) ? line : line.substring(0, sp1);
  String rest = (sp1 < 0) ? String("") : line.substring(sp1 + 1);

  if (cmd == "PING") {
    printlnOK();
  } else if (cmd == "MKDIR") {
    if (rest.length() == 0) { printlnERR(F("ARG")); return; }
    if (SD.mkdir(rest.c_str())) printlnOK(); else printlnERR(F("MKDIR"));
  } else if (cmd == "LIST") {
    if (rest.length() == 0) { printlnERR(F("ARG")); return; }
    listDir(rest);
  } else if (cmd == "EXISTS") {
    if (rest.length() == 0) { printlnERR(F("ARG")); return; }
    if (SD.exists(rest.c_str())) printlnOK(); else printlnERR(F("NO"));
  } else if (cmd == "DEL") {
    if (rest.length() == 0) { printlnERR(F("ARG")); return; }
    if (SD.remove(rest.c_str())) printlnOK(); else printlnERR(F("DEL"));
  } else if (cmd == "GET") {
    if (rest.length() == 0) { printlnERR(F("ARG")); return; }
    if (sendFile(rest)) printlnOK(); else printlnERR(F("GET"));
  } else if (cmd == "PUT") {
    // rest: "<path> <size>"
    int sp = rest.indexOf(' ');
    if (sp < 0) { printlnERR(F("ARG")); return; }
    String path = rest.substring(0, sp);
    String sizeStr = rest.substring(sp + 1);
    size_t size = sizeStr.toInt();
    if (size == 0) { printlnERR(F("SIZE")); return; }
    if (writeFile(path, size)) printlnOK(); else printlnERR(F("PUT"));
  } else {
    printlnERR(F("CMD"));
  }
}
