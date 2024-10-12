#include <ESP8266WiFi.h> // WLAN-Verbindung
// #include <Arduino.h>
// #include <MQTTClient.h>
// #include <Wire.h>         // UART-Verbindung mit Arduino
#include <PubSubClient.h> // MQTT-Verbindung
// #include <ArduinoJson.h>  // Erstellung JSON-Objekt

#define PUBLISH_TOPIC "send"
#define SUBSCRIBE_TOPIC "esp/command"
#define PUBLISH_INTERVAL 5000
unsigned long lastPublishtime = 0;

const char *CLIENT_ID = "ESP8266";

// Hotspot ist Raspberry PI
const char WIFI_SSID[] = "RaspEsp";
const char WIFI_PASSWORD[] = "mqtt1234";
const char MQTT_BROKER_ADRRESS[] = "192.168.1.10"; // IP von Raspberry
const int MQTT_PORT = 1883;
const int buss_serial = 50; // Buffer Groesse fuer UAR-Verbindung

WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

void connect_wifi();                                            // Erstellung der WLAN-Verbindung
void connect_mqtt();                                            // Erstellung der Verbindung mit MQTT-Server
void callback(char *topic, byte *payload, unsigned int length); // Antwort auf die erhaltene MQTT-Nachricht
void readSerialData();                                          // Liest Data aus Serial ab und schickt diese als MQTT-Nachricht

void setup()
{

  Serial.begin(9600);
  connect_wifi();
  connect_mqtt();
}

void loop()
{
  // Ausfall der WLAN-Verbindung
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_wifi();
  }

  // Ausfall der MQTT-Verbindung
  if (!mqttClient.connected())
  {
    connect_mqtt();
  }
  // delay(500);
  readSerialData();
  mqttClient.loop();
}

/*
Serial.print("\nConnecting ESP to MQTT Broker with IP: ");
  Serial.print(MQTT_BROKER_ADRRESS);

Serial.print("\nConnected to MQTT Broker. ");

      Serial.print("\nSubscribed to topic: ");
      Serial.print(SUBSCRIBE_TOPIC);

            int16_t retry = 1000;
      Serial.print("\nMQTT Failed. State = ");
      Serial.print(mqttClient.state());
      Serial.print(" --- Retry in ");
      Serial.print(retry / 1000);
      Serial.print(" seconds");
*/

void connect_mqtt()
{
  Serial.print("\nESP---Verbinden mit dem Broker: ");
  Serial.print(MQTT_BROKER_ADRRESS);

  mqttClient.setServer(MQTT_BROKER_ADRRESS, MQTT_PORT);
  mqttClient.setCallback(callback);
  while (!mqttClient.connected())
  {
    mqttClient.connect(CLIENT_ID);
    Serial.print("\nState: ");
    Serial.print(mqttClient.state());
    delay(500);
  }
  mqttClient.subscribe(SUBSCRIBE_TOPIC);
  Serial.print("\nESP---Topic abonniert: ");
  Serial.print(SUBSCRIBE_TOPIC);
  // while (!mqttClient.connected() && (WiFi.status() == WL_CONNECTED))
  // {
  //   if (mqttClient.connect(CLIENT_ID))
  //   {
  //     mqttClient.subscribe(SUBSCRIBE_TOPIC);
  //     Serial.print("\nESP---Topic abonniert: ");
  //     Serial.print(SUBSCRIBE_TOPIC);
  //   }
  //   else
  //   {
  //     Serial.print("\nMQTT_Broker not connected. State: ");
  //     Serial.print(mqttClient.state());
  //   }
  // }
}

void callback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("\nReceived message on topic: ");
  Serial.print(topic);
  Serial.print(". Payload: ");
  String callbackMessage = "Received message:  ";
  for (unsigned int i = 0; i < length; i++)
  {
    Serial.print((char)payload[i]);
    callbackMessage += (char)payload[i];
  }
  mqttClient.publish(PUBLISH_TOPIC, callbackMessage.c_str());
}

// Verbindung mit WLAN
void connect_wifi()
{
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("\nConnecting ESP to WIFI ");
  Serial.print(WIFI_SSID);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nConnected to Raspi with IP: ");
  Serial.print(WiFi.localIP());
}

// Format topic:message
void readSerialData()
{
  if (Serial.available() > 0)
  {
    String readString = "";
    // Lese Daten aus Serial als String ab
    readString = Serial.readStringUntil('\n');
    Serial.print("\nReceived SERIAL: ");
    Serial.print(readString);
    if (sizeof(readString) > buss_serial)
    {
      Serial.print("Message too long!");
      return;
    }
    Serial.print("\nConvert String to char: ");
    // String in char - Feld konvertieren
    char readSerialChar[readString.length() + 1];
    readString.toCharArray(readSerialChar, readString.length() + 1);
    for (unsigned int i = 0; i < sizeof readSerialChar; i++)
    {
      Serial.print(readSerialChar[i]);
    }

    // Suche Position von ':'
    char *delim_pos = strchr(readSerialChar, ':');
    if (delim_pos != NULL)
    {
      size_t topic_length = delim_pos - readSerialChar;
      char topic[topic_length + 1];
      strncpy(topic, readSerialChar, topic_length);
      topic[topic_length] = '\0';
      char *message = delim_pos + 1;
      Serial.printf("\nMessage %s", message);
      // MQTT-Nachricht senden
      mqttClient.publish(topic, message);
    }
    else // kein : gefunden
    {
      Serial.print("FALSCHES FORMAT");
      return;
    }
  }
}
