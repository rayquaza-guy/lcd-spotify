#include <LiquidCrystal.h>
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

char title[80] = "Waiting for Spotify...";
int titleLen;
int scrollPos = 0;
unsigned long lastScroll = 0;

void makeChars() {
  for (int h = 1; h <= 7; h++) {
    byte c[8];
    for (int r = 0; r < 8; r++) c[r] = (r >= 8 - h) ? 0x1F : 0x00;
    lcd.createChar(h - 1, c);
  }
}

void setup() {
  Serial.begin(57600);
  lcd.begin(16, 2);
  makeChars();
  titleLen = strlen(title);
}

void drawTitle() {
  // title + 4 spaces gap, wrapped around
  for (int i = 0; i < 16; i++) {
    int idx = (scrollPos + i) % (titleLen + 4);
    lcd.setCursor(i, 0);
    lcd.print(idx < titleLen ? title[idx] : ' ');
  }
}

void handleLine(String s) {
  if (s.length() < 2) return;
  if (s[0] == 'T') {
    s.substring(1).toCharArray(title, sizeof(title));
    titleLen = strlen(title);
    scrollPos = 0;
  } else if (s[0] == 'B' && s.length() >= 17) {
    lcd.setCursor(0, 1);
    for (int i = 0; i < 16; i++) {
      int level = s[i + 1] - '0';           // 0..8
      if (level <= 0) lcd.print(' ');
      else if (level >= 8) lcd.write((uint8_t)255);
      else lcd.write((uint8_t)(level - 1));
    }
  }
}

void loop() {
  if (Serial.available()) handleLine(Serial.readStringUntil('\n'));

  if (millis() - lastScroll > 300) {
    lastScroll = millis();
    if (titleLen <= 16) { scrollPos = 0; }
    else scrollPos = (scrollPos + 1) % (titleLen + 4);
    drawTitle();
  }
}