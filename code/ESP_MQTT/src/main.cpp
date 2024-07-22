#include <ESP8266WiFi.h> // WLAN-Verbindung
#include <Arduino.h>
// #include <MQTTClient.h>
#include <Wire.h>         // UART-Verbindung mit Arduino
#include <PubSubClient.h> // MQTT-Verbindung
#include <ArduinoJson.h>  // Erstellung JSON-Objekt

#define PUBLISH_TOPIC "send"
#define SUBSCRIBE_TOPIC "esp/command"
#define PUBLISH_INTERVAL 5000
unsigned long lastPublishtime = 0;

const char *CLIENT_ID = "ESP8266";
// const char MQTT_USER = '';
// const char MQTT_PAS = '';

const char WIFI_SSID[] = "UPC91DEE22";
const char WIFI_PASSWORD[] = "SilverBestCat6";
const char MQTT_BROKER_ADRRESS[] = "192.168.0.206";
const int MQTT_PORT = 1883;
const int buss_serial = 50; // Buffer Groesse fuer UAR-Verbindung

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

void connect_mqtt()
{
  Serial.print("\nConnecting ESP to MQTT Broker with IP: ");
  Serial.print(MQTT_BROKER_ADRRESS);
  while (!mqttClient.connected())
  {
    if (mqttClient.connect(CLIENT_ID))
    {
      Serial.print("\nConnected to MQTT Broker. ");
      mqttClient.subscribe(SUBSCRIBE_TOPIC);
      Serial.print("\nSubscribed to topic: ");
      Serial.print(SUBSCRIBE_TOPIC);
    }
    else
    {
      int16_t retry = 1000;
      Serial.print("\nFailed. State = ");
      Serial.print(mqttClient.state());
      Serial.print(" --- Retry in ");
      Serial.print(retry / 1000);
      Serial.print(" seconds");
      delay(retry);
    }
  }
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

/* Verbindung mit WLAN
@param WIFI_SSID
@param WIFI_PASSWORD
 */
void connect_wifi()
{
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("\nConnecting ESP to WIFI ");
  Serial.print(WIFI_SSID);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(200);
    Serial.print(".");
  }

  Serial.print("\nESP connected to WIFI with IP Address: ");
  Serial.print(WiFi.localIP());
}

// Liest Data aus Serial ab und schickt diese als MQTT-Nachricht
// Format topic:message
void readSerialData()
{
  if (Serial.available() > 0)
  {
    String readString = "";
    static char readSerialChar[buss_serial] = "";
    // Lese Daten aus Serial als String ab
    readString = Serial.readStringUntil('\n');

    // String in char-Filed konvertieren
    for (unsigned int i = 0; i < sizeof(readString); i++)
    {
      readSerialChar[i] = readString[i];
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
      Serial.printf("Message %s", message);
      // MQTT-Nachricht senden
      mqttClient.publish(topic, message);
    }
    else
    {
      Serial.print("FALSCHES FORMAT");
    }
  }
}

void setup()
{
  Serial.begin(9600);
  connect_wifi();
  mqttClient.setServer(MQTT_BROKER_ADRRESS, MQTT_PORT);
  mqttClient.setCallback(callback);
  connect_mqtt();
}

void loop()
{
  if (!mqttClient.connected())
  {
    connect_mqtt();
  }
  delay(500);
  readSerialData();
  mqttClient.loop();
}
