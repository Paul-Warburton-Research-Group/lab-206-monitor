#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(115200);
  analogReference(INTERNAL);
}

int i = 0;
int M32JM_ADDR = byte(0x28);
int delay_base = 4;
int delay_x = 250;
unsigned int trap_adc = 0;
unsigned int status_byte = 0;
unsigned int pres_curr = 0;
unsigned int temp_curr = 0;
unsigned int sdata[4];
byte *bdata;

void loop() {
  // wait > 2x longer than response time
  delay(delay_base*delay_x);
 
  // Read Trap sensor voltage
  trap_adc = analogRead(A0);

  // Send measure all request
  Wire.requestFrom(M32JM_ADDR, 4); // Read_DF4 command
  if (4 <= Wire.available()) {
    pres_curr = Wire.read();
    pres_curr = pres_curr << 8;
    pres_curr |= Wire.read();
    status_byte = (pres_curr & 0xC000) >> 14;
    pres_curr = pres_curr & 0x3FFF;

    temp_curr = Wire.read();
    temp_curr = temp_curr << 8;
    temp_curr |= Wire.read();
    temp_curr = temp_curr >> 5;

    sdata[0] = status_byte;
    sdata[1] = pres_curr;
    sdata[2] = temp_curr;
    sdata[3] = trap_adc;
    bdata = (byte*)&sdata;
    Serial.write(bdata, 8);
  }
}