const unsigned long intervalo_us = 500; // 1 ms = 1000 Hz
unsigned long t0 = 0;

void setup() {
  Serial.begin(115200); // Baud rate elevado
}

void loop() {
  if (micros() - t0 >= intervalo_us) {
    int val = analogRead(A5);
    Serial.println(val);
    t0 += intervalo_us;
  }
}
