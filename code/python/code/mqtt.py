from paho.mqtt import client as mqtt_client
import threading
from queue import Queue
class MqttBroker:

    def __init__(self,queue, broker, port, topic, client_id):
        threading.Thread.__init__(self)
        self.queue = queue
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt_client.Client(client_id=client_id)  
        self.client.on_connect = self.on_connect 
        self.client.on_message = self.on_message
        self.client.on_disconnect= self.on_disconnect
        self.client.connect(self.broker,self.port)
        
    # Rueckmeldung fuer die Verbindung mit dem Broker
    def on_connect(self, client,userdata,falgs,rc):
        if rc==0:
            print("Verbunden mit MQTT-Broker")
        else:
            print("Keine Verbindung mit MQTT-Broker.\n Fehler: %d",rc)

    # Reaktion auf erhaltene Nachricht
    def on_message(self, client,userdata,msg):
        mes=str(msg.payload.decode('utf-8'))
        message = {'topic' : msg.topic, 'text' : mes}  
        print(f"MQTT-BROKER: Erhalten mqtt-message: Topic: {message['topic']}, text: {message['text']}")
        
        self.queue.put(message)


    # Reaktion auf Verbindungsausfahl
    def on_disconnect(client,userdata):
        print("Disconnected from broker")

    def publish(self, msg):
        result = self.client.publish(self.topic,msg)
        if result[0] == 0:
            print(f'GESENDET in Topic {self.topic} Nachricht {msg}')
        else:
            print(f'FEHLER {result[0]}')

    def run(self):
        # Mehrere Topics abonnieren
        for t in self.topic:
            self.client.subscribe(t)

        self.client.loop_start()