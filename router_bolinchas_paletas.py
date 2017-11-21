import threading
from time import sleep
import socket
import sys

# IP actual del enrutador
ROUTER_IP = '' #
FAKE_IP = '140.90.0.30'
LOCALHOST = '127.0.0.1'
# Puerto con el que se comunican los nodos de la red
BOLINCHAS_PORT = 0
# Puerto con el que se comunica el enrutador paletas
PALETAS_PORT = 10004
# IP y puerto del enrutador paletas para conectarse
IP_PALETAS = '10.1.0.3'
NODE_PALETAS_PORT = 10003
# Direccion fisica dentro de la red
DIR_FISICA = 'Bolinchas.Daniel'
# Socket buffer para almacenar el mensaje
BUFFER_SIZE = 1024
# IP y puerto del dispatcher
DISPATCHER_IP_BOLINCHAS = ''
DISPATCHER_PORT_BOLINCHAS = 0
# Tabla de enrutamiento
ROUTING_TABLE = ["Paletas;200.5.0.0;Directo;0","Bolinchas;140.90.0.0;Directo;0",
                 "Legos;201.6.0.0;KevinL;1","Luces;25.0.0.0;KevinL;2",
                 "Banderas;12.0.0.0;KevinM;1","Carritos;165.8.0.0;KevinM;2"]
# Cache local de las conexiones dentro de la red
CACHE_BOLINCHAS = []
# Cola de mensajes recibidos desde bolinchas
MENSAJES_BOLINCHAS = []
# Cola de mensajes recibidos desde paletas
MENSAJES_PALETAS = []

ROUTER_IP = raw_input('Digite su direccion IP: ')
BOLINCHAS_PORT = int(raw_input('Digite el puerto para conexiones de su red: '))
DISPATCHER_IP_BOLINCHAS = raw_input('Digite la direccion IP del dispatcher: ')
DISPATCHER_PORT_BOLINCHAS = int(raw_input('Digite el puerto del dispatcher: '))

# Inicializa el socket servidor que envia a paletas
socket_paletas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_paletas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Paletas server loop created')

try:
    socket_paletas.bind(('', BOLINCHAS_PORT))
    print('Socket paletas bind complete')

except socket.error as msg:
    print('Paletas bind failed. Error : ' + str(sys.exc_info()))
    sys.exit()

socket_paletas.listen(10)
print('Paletas interface now listening')

# Inicializa el socket recibe de paletas y envia a bolinchas
socket_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Bolinchas server loop created')

try:
    socket_bolinchas.bind(('', PALETAS_PORT))
    print('Bolinchas socket bind complete')

except socket.error as msg:
    print('Bolinchas bind failed. Error : ' + str(sys.exc_info()))
    sys.exit()

socket_bolinchas.listen(10)
print('Bolinchas interface now listening')

# Metodo main del programa
def main():
    router = Router()
    router.start()

    try:
        join_threads(router.threads)

    except KeyboardInterrupt:
        print ("\nKeyboardInterrupt catched.")
        print ("Terminate main thread.")
        print ("If only daemonic threads are left, terminate whole program.")

# Clase Router que maneja la estructura del enrutador
class Router(object):
    def __init__(self):
        self.running = True
        self.threads = []

    def start(self):
        # Crear el socket para conectarse con el dispatcher
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS)
        print('Connecting to {} port {}'.format(*server_address))

        try:
            sock.connect(server_address)
            # Envia la direccion IP, fisica y el puerto para que las demas
            # conexiones lo conozcan
            addr_info = DIR_FISICA + ';' + ROUTER_IP + ';' + str(BOLINCHAS_PORT) + ';' + FAKE_IP
            print (addr_info)
            message = addr_info.encode()
            print('Sending {!r}'.format(message))
            sock.sendall(message)

        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % (DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS, e))

        finally:
            print('Closing socket\n')
            sock.close()

        # Thread que escucha las conexiones de paletas
        t1 = threading.Thread(target=self.receive_data)
        # Thread que manda los a paletas desde bolinchas o maneja los broadcasts
        t2 = threading.Thread(target=self.send_data)
        # Thread que revisa el dispatcher por nuevas conexiones
        # t3 = threading.Thread(target=self.call_dispatcher)

        # Make threads daemonic, i.e. terminate them when main thread
        # terminates. From: http://stackoverflow.com/a/3788243/145400
        t1.daemon = True
        t2.daemon = True
        # t3.daemon = True

        self.threads.append(t1)
        self.threads.append(t2)
        # self.threads.append(t3)

        t1.start()
        sleep(1)
        t2.start()
        sleep(1)
        # t3.start()
        # sleep(1)

    # Consulta al dispatcher por las conexiones de la red
    # def call_dispatcher(self):
    #     while self.running and len(CACHE_BOLINCHAS) < 2:
    #         self.check_dispatcher("Bolinchas.Kevin")
    #         self.check_dispatcher("Bolinchas.Jorge")
    #         sleep(30)

    # Ciclo que recibe los datos de paletas y los manda a la red local de bolinchas
    def receive_data(self):

        # Ciclo infinito para no reiniciarse con cada conexion de un cliente
        while (self.running):

            # Se espera por una conexion
            print('Bolinchas interface waiting for connection with paletas')
            connection, client_address = socket_bolinchas.accept()

            try:
                print('Bolinchas received connection from', client_address)

                # Recibe el paquete y lo envia a la red interna
                while True:
                    data = connection.recv(BUFFER_SIZE)

                    if data:
                        print(data.decode())
                        msj_recibido = data.decode()
                        MENSAJES_PALETAS.append(msj_recibido)
                        msj_procesar = MENSAJES_PALETAS.pop(0)
                        params = msj_procesar.decode().split(';')

                        # Arma el mensaje recibido de paletas en lenguaje bolinchas
                        if len(params):
                            ip_inicio = params[0]
                            ip_final = params[1]
                            mensaje = params[4]

                            # Revisar si va para la red o si lo envia al otro router
                            if self.msg_to_network(ip_final):
                                # Busca los datos de la conexion en la cache local
                                dir_bolincha = self.check_cache_ip(ip_final)
                                dir_fisica_dest = dir_bolincha[3]
                            else:
                                dir_fisica_dest = "Bolinchas.Kevin"

                            # Busca los datos de la conexion en la cache local
                            dir_bolincha = self.check_cache_bolinchas(dir_fisica_dest)

                            if dir_bolincha != -1:
                                ip_bolincha = dir_bolincha[1]
                                port = int(dir_bolincha[2])

                                # Da formato de mensaje en bolinchas =
                                # dir_fisica_fuente ; dir_fisica_dest ; ip_inicio ; ip_final ; msg
                                msg_final = DIR_FISICA + ";" + dir_fisica_dest + ";"\
                                            + ip_inicio + ";" + ip_final + ";" + mensaje
                                print("El msj en bolinchas seria:")
                                print(msg_final)
                                self.send_to_bolinchas(msg_final, ip_bolincha, port)
                            else:
                                print 'No se pudo conectar al nodo'
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

    # Ciclo que recibe del dispatcher y de la red local y envia las solicitudes al socket
    # que habla paletas o envia de vuelta la informacion requerida si es broadcast
    def send_data(self):

        # Ciclo infinito para no reiniciarse con cada conexion de un cliente
        while (self.running):

            # Espera por una conexion con la red de bolinchas
            print('Waiting for connection with Bolinchas')
            connection, client_address = socket_paletas.accept()

            try:
                print('Connection from', client_address)

                # Recibe el paquete y decide que hacer con el
                while True:
                    data = connection.recv(BUFFER_SIZE)

                    if data:
                        print("Mensaje recibido: " + data.decode())
                        msj_recibido = data.decode()
                        MENSAJES_BOLINCHAS.append(msj_recibido)
                        msj_procesar = MENSAJES_BOLINCHAS.pop(0)
                        params = msj_procesar.decode().split(';')

                        if len(params):
                            broadcast = self.isBroadcast(params[1])

                            # Revisa si el paquete es un broadcast de la red o no
                            if broadcast:
                                print 'Entro broadcast, respondiendo...'
                                # dir fisica sender = params[0]
                                # dir broadcast * = params[1]
                                # IP solicitada = params[2]
                                network = self.check_Network(params[2])
                                print 'Red solicitada: ', network
                                distance = -1

                                # Busca la red solicitada en la tabla de enrutamiento
                                for x in ROUTING_TABLE:
                                    elements = x.split(';')

                                    if network in elements:
                                        distance = elements[3]
                                        break

                                # Busca la direccion de donde recibio el mensaje para
                                # dar la respuesta solicitada
                                dir_bolincha = self.check_cache_bolinchas(params[0])

                                # Envia la respuesta con el formato establecido
                                if dir_bolincha:
                                    ip_bolincha = dir_bolincha[1]
                                    port = int(dir_bolincha[2])
                                    msg_bc = DIR_FISICA + ';*;' + params[2] + ';' + str(distance)
                                    self.send_to_bolinchas(msg_bc,ip_bolincha,port)

                            else:
                                # Recibe un paquete del dispatcher con la direccion
                                # de una nueva conexion y la guarda si no existe
                                if len(params) == 4:
                                    addr = params[0] + ';' + params[1] + ';' + params[2] + ';' + params[3]
                                    found = False
                                    for x in CACHE_BOLINCHAS:
                                        elems = x.split(';')
                                        if elems[0] == params[0]:
                                            found = True
                                            CACHE_BOLINCHAS.remove(x)
                                            CACHE_BOLINCHAS.append(addr)
                                            break
                                    if not found:
                                        CACHE_BOLINCHAS.append(addr)

                                    print "Direccion Fisica - Direccion IP - Puerto - IP Falsa"
                                    for x in CACHE_BOLINCHAS:
                                        elems = x.split(';')
                                        print elems[0] + ' - ' + elems[1] + ' - ' + \
                                              elems[2] + ' - ' + elems[3]


                                # No recibe ninguna conexion del dispatcher
                                elif len(params) == 2:
                                    sleep(1)

                                # Recibe el mensaje para enviarlo a paletas
                                else:
                                    # dir fisica sender = params[0]
                                    # dir fisica reciever = params[1]
                                    # IP inicio = params[2]
                                    # IP final = params[3]
                                    # Mensaje = params[4]

                                    if self.msg_to_network(params[3]):
                                        if params[3] == FAKE_IP:
                                            print 'Mensaje recibido de ' + params[2] + \
                                                  ': ' + params[4]
                                        else:
                                            dir_bolincha = self.check_cache_ip(params[3])
                                            if dir_bolincha:
                                                ip_bolincha = dir_bolincha[1]
                                                port = int(dir_bolincha[2])
                                                dir_fisica_dest = dir_bolincha[0]

                                                # Da formato de mensaje en bolinchas =
                                                # dir_fisica_fuente ; dir_fisica_dest ; ip_inicio ; ip_final ; msg
                                                msg_final = DIR_FISICA + ";" + dir_fisica_dest + ";" \
                                                            + params[2] + ";" + params[3] + ";" + params[4]
                                                print("El msj en bolinchas seria:")
                                                print(msg_final)
                                                self.send_to_bolinchas(msg_final, ip_bolincha, port)

                                    else:
                                        # Construye el mensaje en un formato que pueda interpretar paletas
                                        action = 0
                                        ip_inicio = params[2].split('.')
                                        ip_final = params[3].split('.')
                                        ip_action = ["0","0","0","0"]
                                        msg_red = params[4]
                                        msg_paleta = ip_inicio[0] + ";" + ip_inicio[1] + ";" + ip_inicio[2] +\
                                                     ";" + ip_inicio[3] + ";" + ip_final[0] + ";" + \
                                                     ip_final[1] + ";" + ip_final[2] + ";" + ip_final[3] +\
                                                     ";" + str(action) + ";" + ip_action[0] + ";" + ip_action[1] +\
                                                     ";" + ip_action[2] + ";" + ip_action[3] + ";" + msg_red
                                        print("El msj en paleta seria:")
                                        print(msg_paleta)
                                        self.send_to_paletas(msg_paleta)

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

        print('Closing socket??')
        socket_paletas.close()

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

    # Metodo para crear socket cliente a la red de paletas y enviar el mensaje
    def send_to_paletas(self, msg):
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            client_bolinchas.connect((IP_PALETAS, NODE_PALETAS_PORT))
            client_bolinchas.send(msg.encode())
            print 'Mensaje enviado'
        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % (IP_PALETAS, NODE_PALETAS_PORT, e))
        finally:
            client_bolinchas.close()

    # Metodo para verificar si la red final es la local o no
    def msg_to_network(self, ip):
        decodedIP = ip.split('.')
        if len(decodedIP):
            if (int(decodedIP[0]) == 140) and ((int(decodedIP[1]) == 90)):
                print('Mensaje para la red local')
                return True
            else:
                print('Mensaje para red exterior')
                return False
        else:
            print('No data found')

    # Metodo para revisar la cache local y devuelve la conexion si la encontro
    def check_cache_bolinchas(self, dir_fisica):
        found = False

        if CACHE_BOLINCHAS:
            print 'Buscando en cache local'
            for x in CACHE_BOLINCHAS:
                item = x.split(';')
                if dir_fisica in item:
                    found = True
                    break
            if found:
                return item
        else:
            return -1

    def check_cache_ip(self, ip):
        found = False
        if CACHE_BOLINCHAS:
            print 'Buscando en cache local'
            for x in CACHE_BOLINCHAS:
                item = x.split(';')
                if ip in item:
                    found = True
                    break
            if found:
                return item
        else:
            return -1

    # Metodo para solicitar la tabla cache al dispatcher y obtener nuevas conexiones
    def check_dispatcher(self, dir_fisica):
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            client_bolinchas.connect((DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS))
            solicitud = dir_fisica + ';*'
            client_bolinchas.send(solicitud)
        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % (DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS, e))
        finally:
            client_bolinchas.close()

    # Metodo para consultar si el mensaje indicado es de broadcast o no
    def isBroadcast(self,tipo):
        broadcast = False
        if tipo == '*':
            broadcast = True
        else:
            broadcast = False
        return broadcast

    # Metodo para determinar a cual red va dirigido el mensaje
    def check_Network(self, ip):
        ip_numbers = ip.split('.')
        clase = ''
        network = ''
        network_type = int(ip_numbers[0])
        if network_type >= 0 and network_type < 128:
            clase = 'A'
        elif network_type >= 128 and network_type < 192:
            clase = 'B'
        elif network_type >= 192 and network_type < 224:
            clase = 'C'
        if clase == 'A':
            network = ip_numbers[0] +'.0.0.0'
        elif clase == 'B':
            network = ip_numbers[0] + '.' + ip_numbers[1] + '.0.0'
        elif clase == 'C':
            network = ip_numbers[0] + '.' + ip_numbers[1] + '.' + ip_numbers[2] + '.0'
        return network

# Metodo para unir los threads del programa
def join_threads(threads):
    for t in threads:
        while t.isAlive():
            t.join(5)


if __name__ == "__main__":
    main()