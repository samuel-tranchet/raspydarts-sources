
"""
Manage events
Send data on approriate topic, wait for ack, ...
"""

import random
# String to dict
import ast
# Regexp
import re
# time
import time

import paho.mqtt.client as mqtt

class Event:
    """
    Main events class
    """
    def __init__(self, logs, preferences, broker=None, port=None, topic=None, subscribers=None):
        if broker is None:
            broker = 'localhost'
        if port is None:
            port = 1883
        if topic is None:
            topic = 'raspydarts'

        client_id = f'pydarts-mqtt-{random.randint(0,1000)}'
        self.broker = broker
        self.port = port
        self.target_topic = f'{topic}/targetLeds'
        self.strip_topic = f'{topic}/stripLeds'
        self.dmd_topic = f'{topic}/dmd'
        self.matrix_topic = f'{topic}/matrix'
        self.other_topic = f'{topic}/other'
        self.continue_list = []

        self.target_leds = False
        self.strip_leds = False
        self.dmd = False
        self.matrix = False
        self.other = False

        for subscriber in subscribers:
            if subscriber == 'Target':
                self.target_leds = True
            elif subscriber == 'Strip':
                self.strip_leds = True
            elif subscriber == 'Dmd':
                self.dmd = True
            elif subscriber == 'Matrix':
                self.matrix = True
            elif subscriber == 'Other':
                self.other = True

        self.dispatcher = preferences
        self.logs = logs

        self.logs.log("DEBUG", f"self.dispatcher={self.dispatcher}")
        self.logs.log("DEBUG", f"broker={broker}")
        try:
            self.mqtt_client = mqtt.Client(client_id)
            self.mqtt_client.connect(broker, port)
        except: # pylint: disable=bare-except
            self.mqtt_client = None

    def get_events(self):
        """
        returns list of available events
        """
        return ['launch', 'menu', 'newgame', 'wait', 'SB', 'DB', 'pressure', \
                'release', 'nextplayer', 'touch', 'miss', 'setwinner', 'winner', \
                'gameover', 'interrupt', 'quit']

    def get_strip(self):
        """
        return list of animations available for strip leds
        """
        liste = []
        with open("addons/CStrip.py", "r", encoding="utf-8") as file:
            for line in file:
                if re.search("def SA_", line):
                    liste.append(line.split("_")[1].split("(")[0])
        return liste

    def get_target(self):
        """
        return list of animations available for target leds
        """
        liste = []
        with open("addons/CStrip.py", "r", encoding="utf-8") as file:
            for line in file:
                if re.search("def TA_", line):
                    liste.append(line.split("_")[1].split("(")[0])
        liste.sort()
        return liste

    def get_colors(self):
        """
        return a list of colors
        """
        liste = []
        liste.append('random')
        with open("addons/Colors.py", "r", encoding="utf-8") as file:
            for line in file:
                if re.search("'[a-z][a-z]*[^1-9]'", line):
                    liste.append(line.split("'")[1])

        return liste

    def __message_is_ack(self, client, userdata, msg):
        """
        Function to execute on ack
        """
        if msg.payload.decode() == 'ack':
            i = 0
            for i in range(0, len(self.continue_list)):
                if self.continue_list[i] == msg.topic:
                    del self.continue_list[i]
                    break
            self.logs.log("DEBUG", f"Wait for ack on {self.continue_list}")

    def wait_acks(self, topics, timeout):
        """
        Wait for ack from various servers
        Very usefull for shutdown
        """
        topic_list = []
        for topic in topics:
            if topic is not None:
                topic_list.append((topic + '-ack',0))
                self.continue_list.append(topic + '-ack')
        if len(topic_list) == 0:
            return

        self.mqtt_client.on_message = self.__message_is_ack
        self.mqtt_client.subscribe(topic_list)
        self.logs.log("DEBUG", f"Wait for ack on {self.continue_list}")

        i = 0
        while i <= timeout and len(self.continue_list) > 0:
            self.mqtt_client.loop()
            i += 1
            time.sleep(0.5)
        if i == timeout:
            self.logs.log("DEBUG", f"Timeout reached on {topic}")
        if len(self.continue_list) == 0:
            self.logs.log("DEBUG", "Ack received")
        else:
            self.logs.log("DEBUG", f"Missing acks : {self.continue_list}")

    def mqtt_publish(self, topic, message):
        """
        Mqtt publish function
        Retry on error, 50 times max
        """
        if len(message) < 1:
            self.logs.log("WARNING", f"Cannot publish on 0 length message")
            return
        self.logs.log("DEBUG", f"Publish on {topic} : {message}")
        ret = self.mqtt_client.publish(topic, message)
        if ret[0] != 0 :
            self.logs.log("DEBUG", f"publish ret={ret}")
        i = 0
        while ret[0] != 0 and i < 50 :
            time.sleep(0.01)
            self.mqtt_client.disconnect()
            ret = self.mqtt_client.connect(self.broker, self.port)
            if ret == 0 :
                ret = self.mqtt_client.publish(topic, message)
                self.logs.log("DEBUG", f"Send {message} on {topic}")
            else :
                self.logs.log("DEBUG", f"Cannot reconnect to {self.broker}:{self.port}")

            i += 1
        if i == 50 :
            self.logs.log("ERROR", "Mqtt Send error")


    def send(self, device, topic, available, event, data, ack=False):
        """
        Sent a message on a topic
        """
        self.continue_list = []

        if event == 'wait':
            thread = True
        else:
            thread = False

        if available:
            shutdown = False

            if event == 'quit':
                shutdown = True
            elif event == 'stroke':
                if data in ('SB', 'DB'):
                    event = data
                else:
                    event = 'touch'
            try:
                messages = self.dispatcher[event][device][::]
                #if event in ('SB','DB','touch') and device == 'TARGET':
                if event == 'touch' and device == 'TARGET':
                    raise Exception     # Overide animation definition in configuration file
                if event == 'wait' and len(messages) > 1:
                    # Keep one message
                    # I hope the animation will change at every execution
                    for x in range(0, len(messages) - 1):
                        event_to_remove = random.randint(0, len(messages) - 1)
                        messages.pop(event_to_remove)

                if messages == [''] or len(messages) == 0:
                    if event == 'DB':
                        messages = ['stroke:DB']
                    elif event == 'SB':
                        messages = ['stroke:SB']
                    elif event == 'quit' and device == 'DMD':
                        messages = ['shutdwn|']
                        ack = False
                    elif event == 'quit':
                        messages = ['quit']

            except: # pylint: disable=bare-except
                if event in ('SB','DB','touch'):
                    event = 'stroke'

                # Not found, send as receveid
                messages = []
                if data:
                    messages.append(f"{event}:{data}")
                else:
                    messages.append(event)

            # ICI pour envoyer plusieurs animations en une fois
            for message in messages:
                if message != '' :
                    if thread:
                        message = f'thread:{message}'
                    elif ack:
                        message = f'ack:{message}'
                    self.mqtt_publish(topic, message)

            if shutdown:
                time.sleep(0.5)
                self.mqtt_client.publish(topic, 'quit')

            if ack:
                return topic

        return None

    def publish(self, event, data=None, ack=False, limit=None):
        """
        Used by other modules
        Send data on various topics
        """
        if self.mqtt_client is not None:
            if event == 'leds':
                self.mqtt_publish(self.target_topic, f"leds|{data}")

            elif event == 'special':
                for element in data.split('-'):
                    if len(element) == 0:
                        continue
                    destination = element.split(':')[0]
                    anims = element.split(':')[1].split(';')

                    for anim in anims:
                        if self.target_leds and destination == 'TARGET':
                            self.mqtt_publish(self.target_topic, f'thread:{anim}')
                        elif self.strip_leds and destination == 'STRIP':
                            self.mqtt_publish(self.strip_topic, f'thread:{anim}')
                        elif self.dmd and destination == 'DMD':
                            self.mqtt_publish(self.dmd_topic, anim)
                        elif self.matrix and destination == 'MATRIX':
                            self.mqtt_publish(self.matrix_topic, anim)
                        elif self.matrix and destination == 'OTHER':
                            self.mqtt_publish(self.other_topic, anim)
                        time.sleep(0.001)
            else:
                ack_list = []
                if limit is None or 'TARGET' in limit:
                    # Target Leds
                    ack_list.append(self.send('TARGET', self.target_topic, self.target_leds, \
                            event, data, ack))
                if limit is None or 'STRIP' in limit:
                    # Strip Leds
                    ack_list.append(self.send('STRIP', self.strip_topic, self.strip_leds, \
                            event, data, ack))
                if limit is None or 'DMD' in limit:
                    # Dmd
                    ack_list.append(self.send('DMD', self.dmd_topic, self.dmd, \
                            event, data, ack))
                if limit is None or 'MATRIX' in limit:
                    # Matrix Leds
                    ack_list.append(self.send('MATRIX', self.matrix_topic, self.matrix, \
                            event, data, ack))
                if limit is None or 'OTHER' in limit:
                    # Other device
                    ack_list.append(self.send('OTHER', self.other_topic, self.other, \
                            event, data, ack))

                self.wait_acks(ack_list, 60)

                if event == 'quit':
                    self.mqtt_client.disconnect()
        else:
            self.logs.log("ERROR", "Mqtt client not initialized")


    def string_to_pref(self, prefs):
        """
        Return dict from string
        """

        return ast.literal_eval(prefs)
