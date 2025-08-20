// Minimal Blink for Arduino Uno WiFi Rev2
// Board FQBN: arduino:megaavr:uno2018

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
}
