/*
  Web client

 This sketch connects to a website 
 using Wi-Fi functionality on MediaTek LinkIt platform.

 Change the macro WIFI_AP, WIFI_PASSWORD, WIFI_AUTH and SITE_URL accordingly.

 created 13 July 2010
 by dlf (Metodo2 srl)
 modified 31 May 2012
 by Tom Igoe
 modified 20 Aug 2014
 by MediaTek Inc.
 */

#include <LWiFi.h>
#include <LWiFiClient.h>

#define WIFI_AP "Hack The Midlands 1"
#define WIFI_PASSWORD "learn-build-share"
#define WIFI_AUTH LWIFI_WPA  // choose from LWIFI_OPEN, LWIFI_WPA, or LWIFI_WEP.
#define SITE_URL "lumi-htm-best.herokuapp.com"

LWiFiClient c;
int redPin = 11;
int greenPin = 10;
int bluePin = 9;
int inputPin = 2;
char ch;
int count = 0;

void setup()
{
  Serial.begin(115200);
  Serial.println("Starting");
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  pinMode(inputPin, INPUT);
  LWiFi.begin();

  // keep retrying until connected to AP
  Serial.println("Connecting to AP");
  while (0 == LWiFi.connect(WIFI_AP, LWiFiLoginInfo(WIFI_AUTH, WIFI_PASSWORD)))
  {
    delay(1000);
  }

  // keep retrying until connected to website
  Serial.println("Connecting to WebSite");
  while (0 == c.connect(SITE_URL, 80))
  {
    Serial.println("Re-Connecting to WebSite");
    delay(1000);
  }

  // send HTTP request, ends with 2 CR/LF
  Serial.println("send HTTP GET request");
  c.println("GET /colour HTTP/1.1");
  c.println("Host: " SITE_URL);
  c.println("Connection: close");
  c.println();

  // waiting for server response
  Serial.println("waiting HTTP response:");
  while (!c.available())
  {
    delay(100);
  }
}

boolean disconnectedMsg = false;

void loop()
{
  // Make sure we are connected, and dump the response content to Serial
  while (c)
  {
    int v = c.read();
    if (v != -1)
    {
      Serial.print((char)v);
      ch = v;
    }
    else
    {
      Serial.println("no more content, disconnect");
      c.stop();
      while (1)
      {
        delay(1);
      }
    }

//    Serial.println("Checking for motion");
//    int val = digitalRead(inputPin);  // read input value
//    if (val == HIGH) {            // check if the input is HIGH
//      Serial.println("Detected motion");
//      c.println("GET /dismiss HTTP/1.1");
//      c.println("Host: " SITE_URL);
//      c.println("Connection: close");
//      c.println();
//    }
  }

  if (!disconnectedMsg)
  {
    Serial.println("Update LED");
    if (ch == 'a') {
      Serial.println("Flashing red");
      setColor(255, 0, 0);
      delay(500);
      setColor(0, 0, 0);
      delay(500);
      setColor(255, 0, 0);
      delay(500);
      setColor(0, 0, 0);
      delay(500);
    } else if (ch == 'c') {
      Serial.println("Flashing blue");
      setColor(0, 0, 255);
      delay(500);
      setColor(0, 0, 0);
      delay(500);
      setColor(0, 0, 255);
      delay(500);
      setColor(0, 0, 0);
      delay(500);
    } else if (ch == 'd') {
      Serial.println("Flashing green");
      setColor(0, 255, 0);
      delay(500);
      setColor(0, 0, 0);
      delay(500);
      setColor(0, 255, 0);
      delay(500);
      setColor(0, 0, 0);
      delay(500);
    } else if (ch == 'r') {
      Serial.println("Red");
      setColor(255, 0, 0);
      delay(2000);
    } else if (ch == 'g') {
      Serial.println("Green");
      setColor(0, 255, 0);
      delay(2000);
    } else {
      Serial.println("Blue");
      setColor(0, 0, 255);
      delay(2000);
    }
    Serial.println("disconnected by server");
  }
  delay(500);

  if (count >= 10) {
    // keep retrying until connected to website
    Serial.println("Connecting to WebSite");
    while (0 == c.connect(SITE_URL, 80))
    {
      Serial.println("Re-Connecting to WebSite");
      delay(1000);
    }
    
    // send HTTP request, ends with 2 CR/LF
    Serial.println("send HTTP GET request");
    c.println("GET /colour HTTP/1.1");
    c.println("Host: " SITE_URL);
    c.println("Connection: close");
    c.println();
  
    // waiting for server response
    Serial.println("waiting HTTP response:");
    while (!c.available())
    {
      delay(100);
    }
    count = 0;
  }

  count++;
}

void setColor(int red, int green, int blue)
{
  #ifdef COMMON_ANODE
    red = 255 - red;
    green = 255 - green;
    blue = 255 - blue;
  #endif
  analogWrite(redPin, red);
  analogWrite(greenPin, green);
  analogWrite(bluePin, blue);  
}
