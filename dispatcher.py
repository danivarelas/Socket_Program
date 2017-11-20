import threading
from time import sleep
import socket
import sys

# IP actual del dispatcher
DISPATCHER_IP = '10.1.0.4'
DISPATCHER_PORT = 5454
LOCALHOST = '127.0.0.1'

#Mantiene una lista local de las conexiones conocidas
KNOWN_NETWORKS = []

# Socket buffer para almacenar el mensaje
BUFFER_SIZE = 1024

# Cache local de las conexiones dentro de la red
CACHE_BOLINCHAS = []

# Inicializa el socket recibe de paletas y envia a bolinchas
socket_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Bolinchas server dispatcher created')

try:
    socket_bolinchas.bind(('', DISPATCHER_PORT))
    print('Dispatcher socket bind complete')

except socket.error as msg:
    print('Dispatcher bind failed. Error : ' + str(sys.exc_info()))
    sys.exit()

socket_bolinchas.listen(10)
print('Dispatcher now listening')

# Metodo main del programa
def main():
    dispatcher = Dispatcher()
    dispatcher.start()

    try:
        join_threads(dispatcher.threads)

    except KeyboardInterrupt:
        print ("\nKeyboardInterrupt catched.")
        print ("Terminate main thread.")
        print ("If only daemonic threads are left, terminate whole program.")

# Clase Dispatcher que maneja la estructura del dispatcher
class Dispatcher(object):
    def __init__(self):
        self.running = True
        self.threads = []

    def start(self):

        # Thread que escucha las conexiones de paletas
        t1 = threading.Thread(target=self.receive_data)

        # Make threads daemonic, i.e. terminate them when main thread
        # terminates. From: http://stackoverflow.com/a/3788243/145400
        t1.daemon = True

        self.threads.append(t1)

        t1.start()
        sleep(1)

    # Ciclo que recibe los datos de paletas y los manda a la red local de bolinchas
    def receive_data(self):

        # Ciclo infinito para no reiniciarse con cada conexion de un cliente
        while (self.running):

            # Se espera por una conexion
            print('Dispatcher waiting for connection')
            connection, client_address = socket_bolinchas.accept()

            try:
                print('Dispatcher received connection from', client_address)

                # Recibe el paquete y lo envia a la red interna
                while True:
                    data = connection.recv(BUFFER_SIZE)

                    if data:
                        print(data.decode())
                        params = data.decode().split(';')

                        #Arma el mensaje recibido de paletas en lenguaje bolinchas
                        if len(params):
                            dir_fisica = params[0]
                            ip = params[1]
                            puerto = params[2]
                            local_network = dir_fisica + ';' + ip + ';' + puerto
                            found = False
                            for x in KNOWN_NETWORKS:
                                elems = x.split(';')
                                if elems[0] == dir_fisica:
                                    elems[1] = ip
                                    elems[2] = puerto
                                    KNOWN_NETWORKS[x] = elems[0] + ';' + elems[1] + ';' + elems[2]
                                    found = True
                            if not found:
                                KNOWN_NETWORKS.append(local_network)
                            for x in KNOWN_NETWORKS:
                                elems = x.split(';')
                                for y in KNOWN_NETWORKS:
                                    elems2 = y.split(';')
                                    if elems[0] != elems2[0]:
                                        self.send_to_bolinchas(local_network, elems2[1], elems2[1])

                        else:
                            print('no data from', client_address)

                    else:
                        print('no data from', client_address)

                    break

            except:
                print("Terible error!")
                import traceback
                traceback.print_exc()

            finally:
                print ("\n")

        print('Closing socket')
        socket_bolinchas.close()

    # Metodo para crear socket cliente a la red local y enviar el mensaje
    def send_to_bolinchas(self, msg, ip, port):
        mensaje = ''
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            print 'Enviando mensaje a bolinchas'
            client_bolinchas.connect((ip, port))
            mensaje = msg.encode()
            client_bolinchas.send(mensaje)

        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % (ip, port, e))

        finally:
            print 'Mensaje enviado: ' + mensaje
            client_bolinchas.close()

# Metodo para unir los threads del programa
def join_threads(threads):
    for t in threads:
        while t.isAlive():
            t.join(5)


if __name__ == "__main__":
    main()