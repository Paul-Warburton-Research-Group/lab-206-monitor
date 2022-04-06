#include <Wire.h>
#include "HX711.h"

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 3;
const int M32JM_ADDR = byte(0x28);
const int delay_base = 4;
const int delay_x = 250;
const float scale_unit = 8000.0;

HX711 scale;
int i = 0;
float trap_adc = 0;
unsigned int status_byte = 0;
unsigned int pres_curr = 0;
unsigned int temp_curr = 0;
unsigned int sdata[3];
byte *bdata;

void setup() {
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(scale_unit);
  
  Wire.begin();
  Serial.begin(115200);
  //analogReference(INTERNAL);
}

void loop() {
  // wait > 2x longer than response time
  delay(delay_base*delay_x);
 
  // Read Trap sensor voltage
  trap_adc = scale.get_units();
  //Serial.println("Got Value:");
  //Serial.println(trap_adc);

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
    //unsigned long fdata = (unsigned long)trap_adc;
    //sdata[3] = 0;
    //sdata[4] = 0;
    //sdata[3] = fdata;
    bdata = (byte*)&sdata;
    Serial.write(bdata, 6);

    bdata = (byte*)&trap_adc;
    Serial.write(bdata, 4);
  }
}