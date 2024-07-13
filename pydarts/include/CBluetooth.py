import bluetooth
import subprocess

server_sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
port = 1
server_sock.bind(("",port))
server_sock.listen(1)

isConnected = False
bluetoothAddress = ""

class CBluetooth():

    def __init__(self):
        self.level=1

    def IsConnected(self):
        return bool(isConnected)

    def Connexion(self):
        global isConnected
        global client_sock
        global server_sock
        client_sock,address = server_sock.accept()
        server_sock.setblocking(0)
        client_sock.send("Vous êtes connecté au Raspberry ! \r\n")
        print ("Accepted connection from ", address[0])
        bluetoothAddress = address[0]
        isConnected = True
        return bluetoothAddress

    def Deconnexion(self):
        client_sock.close()
        server_sock.close()

    def SendMessage(self, message):
        client_sock.send(message + "\r\n")

    def ReceiveMessage(self):
        server_sock.setblocking(0)
        return client_sock.recv(4096).decode()
