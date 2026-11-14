const int emgPin = 36;

float baseline = 0;
float envelope = 0;

const float baselineAlpha = 0.001;
const float envelopeAlpha = 0.03;

const int threshold = 70;
const int activationCountNeeded = 8;

const int artifactThreshold = 250; // выше - считаем артефактом движения

const int artifactCooldown = 80; // сколько циклов игнорировать сигнал после артефакта

const int plotDelay = 20;

int activationCounter = 0;
int artifactCounter = 0;

void setup() {
  Serial.begin(115200);

  long sum = 0;
  for (int i = 0; i < 1000; i++) 
  {
    sum += analogRead(emgPin);
    delay(2);
  }

  baseline = sum / 1000.0;
}

void loop() 
{
  int raw = analogRead(emgPin);
  baseline = (1 - baselineAlpha) * baseline + baselineAlpha * raw;
  float rectified = abs(raw - baseline);
  envelope = (1 - envelopeAlpha) * envelope + envelopeAlpha * rectified;
  float output = envelope - threshold;
  if (output < 0) output = 0;
  if (output > artifactThreshold) 
  {
    artifactCounter = artifactCooldown;
    activationCounter = 0;
  }
  if (artifactCounter > 0) 
  {
  artifactCounter--;
  Serial.print(envelope);
  Serial.print(",");
  Serial.println(0);
  delay(plotDelay);
  return;
  }

  if (output > 0) {
    activationCounter++;
  } else {
    activationCounter = 0;
  }

  if (activationCounter >= activationCountNeeded) 
  {
  Serial.print(envelope);
  Serial.print(",");
  Serial.println(output);
  } else 
  {
  Serial.print(envelope);
  Serial.print(",");
  Serial.println(0);
  }

  delay(plotDelay);
}