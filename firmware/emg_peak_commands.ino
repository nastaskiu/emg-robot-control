const int EMG_PIN = 36;

// Пороги для сигнала относительно baseline
const int PEAK_ON     = 28;
const int REARM_LEVEL = 12;
const int MIN_GAP_MS  = 280;

// Окно команд
const unsigned long WINDOW_MS = 6000;
const unsigned long PAUSE_MS  = 1200;

// Фильтрация
float fastFiltered = 0;
float baseline = 0;
float emgSignal = 0;

// Состояния
bool armed = true;
int peakCount = 0;

unsigned long lastTriggerTime = 0;
unsigned long windowStart = 0;
bool windowActive = false;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetPinAttenuation(EMG_PIN, ADC_11db);

  delay(1000);

  long sum = 0;
  for (int i = 0; i < 100; i++) {
    sum += analogRead(EMG_PIN);
    delay(5);
  }
  baseline = sum / 100.0;
  fastFiltered = baseline;

  Serial.print("INITIAL BASELINE = ");
  Serial.println(baseline);

  startNewWindow();
}

void loop() {
  int raw = analogRead(EMG_PIN);

  fastFiltered = 0.7 * fastFiltered + 0.3 * raw;

  if (armed) {
    baseline = 0.995 * baseline + 0.005 * fastFiltered;
  }

  emgSignal = fastFiltered - baseline;
  if (emgSignal < 0) emgSignal = 0;

  unsigned long now = millis();

  if (armed && emgSignal > PEAK_ON && (now - lastTriggerTime >= MIN_GAP_MS)) {
    peakCount++;
    lastTriggerTime = now;
    armed = false;

    Serial.print("PEAK #");
    Serial.print(peakCount);
    Serial.print(" | val=");
    Serial.println((int)emgSignal);
  }

  if (!armed && emgSignal < REARM_LEVEL) {
    armed = true;
  }

  if (windowActive && (now - windowStart >= WINDOW_MS)) {
    String cmd = decodeCommand(peakCount);

    Serial.print("RESULT: peaks=");
    Serial.print(peakCount);
    Serial.print(" -> COMMAND: ");
    Serial.println(cmd);

    windowActive = false;
    delay(PAUSE_MS);
    startNewWindow();
  }

  Serial.print("filtered:");
  Serial.print((int)emgSignal);
  Serial.print(",");

  Serial.print("baseline:");
  Serial.print((int)baseline);
  Serial.print(",");

  Serial.print("peak_on:");
  Serial.print(PEAK_ON);
  Serial.print(",");

  Serial.print("peak_off:");
  Serial.print(REARM_LEVEL);
  Serial.print(",");

  Serial.print("inPeak:");
  Serial.println(armed ? 0 : 100);

  delay(10);
}

void startNewWindow() {
  peakCount = 0;
  armed = true;
  windowStart = millis();
  windowActive = true;

  Serial.println("---- NEW WINDOW ----");
}

String decodeCommand(int count) {
  if (count == 0) return "STOP";
  if (count == 1) return "FORWARD";
  if (count == 2) return "BACKWARD";
  if (count == 3) return "LEFT";
  return "RIGHT";
}