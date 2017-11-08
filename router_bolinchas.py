import threading
from time import sleep
import socket
import sys

# Current node's IP
ROUTER_IP = '10.1.130.166' #''192.168.0.105'  # '140.90.0.30'
LOCALHOST = '127.0.0.1'

#puertos locales del router
BOLINCHAS_PORT = 2424
PALETAS_PORT = 10004

IP_PALETAS = '10.1.130.1'
NODE_PALETAS_PORT = 10003

DIR_FISICA = 'Bolinchas.Daniel'

#Socket buffer
BUFFER_SIZE = 1024

# Dispatcher's IP
DISPATCHER_IP_BOLINCHAS = '10.1.131.18'
DISPATCHER_PORT_BOLINCHAS = 1024

# Array of other computers on net
ARP_TABLE = []

ROUTING_TABLE = ["Paletas;200.5.0.0;Directo;0","Bolinchas;140.90.0.0;Directo;0",
                 "Legos;201.6.0.0;KevinL;1","Luces;25.0.0.0;KevinL;2",
                 "Banderas;12.0.0.0;KevinM;1","Carritos;165.8.0.0;KevinM;2"]


CACHE_BOLINCHAS = []

# Inicializa el socket servidor que envia a paletas
socket_paletas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_paletas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Pallets server loop created')

try:
    #socket_paletas.bind((ROUTER_IP, BOLINCHAS_PORT))
    socket_paletas.bind(('', BOLINCHAS_PORT))
    print('Pallets Socket bind complete')

except socket.error as msg:
    print('Pallets bind failed. Error : ' + str(sys.exc_info()))
    sys.exit()

# Start listening on socket
socket_paletas.listen(10)
print('Pallets interface now listening')

# Inicializa el socket recibe de paletas y envia a bolinchas
socket_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Bolinchas server loop created')

try:
    socket_bolinchas.bind(('', PALETAS_PORT))
    print('Bolinchas bind complete')

except socket.error as msg:
    print('Bolinchas bind failed. Error : ' + str(sys.exc_info()))
    sys.exit()

# Start listening on socket
socket_bolinchas.listen(10)
print('Bolinchas interface now listening')


def main():
    router = Router()
    router.start()
    try:
        join_threads(router.threads)
    except KeyboardInterrupt:
        print ("\nKeyboardInterrupt catched.")
        print ("Terminate main thread.")
        print ("If only daemonic threads are left, terminate whole program.")


class Router(object):
    def __init__(self):
        self.running = True
        self.threads = []

    def start(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS)
        print('Connecting to {} port {}'.format(*server_address))

        try:
            sock.connect(server_address)
            # Send data
            addr_info = DIR_FISICA + ';' + ROUTER_IP + ';' + str(BOLINCHAS_PORT)
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

        # Thread que escucha las solicitudess
        t1 = threading.Thread(target=self.receive_data)

        # Thread que manda los datos
        t2 = threading.Thread(target=self.send_data)

        # Thread que revisa el dispatcher
        t3 = threading.Thread(target=self.call_dispatcher)

        # Make threads daemonic, i.e. terminate them when main thread
        # terminates. From: http://stackoverflow.com/a/3788243/145400
        t1.daemon = True
        t2.daemon = True
        t3.daemon = True

        self.threads.append(t1)
        self.threads.append(t2)
        self.threads.append(t3)

        t1.start()
        sleep(1)
        t2.start()
        sleep(1)
        t3.start()
        sleep(1)
        # self.send_to_george('165.8.2.0','hola')
        # self.send_to_george('200.5.0.2', 'bebe')
        # self.send_to_george('201.6.0.2', 'adios')
        # self.send_to_george('12.0.0.8', 'juju')
        prueba = '165;8;2;0;200;5;0;2;0;0;0;0;0;Hola paletas'
        self.send_to_paletas(prueba.encode())


    # Consulta al dispatcher por las conexiones de la red
    def call_dispatcher(self):
        while self.running and len(CACHE_BOLINCHAS) < 2:
            self.check_dispatcher("Bolinchas.Kevin")
            self.check_dispatcher("Bolinchas.Jorge")
            sleep(30)

    # Loop que recibe los datos y los manda a la red local de bolinchas
    def receive_data(self):

        # this will make an infinite loop needed for
        # not reseting server for every client
        while (self.running):

            # Wait for a connection
            print('Bolinchas interface waiting for connection with paletas')
            connection, client_address = socket_bolinchas.accept()

            try:
                print('Bolinchas received connection from', client_address)

                # Receive the packet and send it to the next network
                while True:

                    data = connection.recv(BUFFER_SIZE)
                    if data:
                        print(data.decode())
                        params = data.decode().split(';')
                        if len(params):
                            ip_inicio = params[0]
                            ip_final = params[1]
                            mensaje = params[4]
                            # TODO enviar a la red local
                            #Revisar si va para la red o si lo envia al otro router
                            if self.msg_to_network(ip_final):
                                dir_fisica_dest = "Bolinchas.Jorge"
                            else:
                                dir_fisica_dest = "Bolinchas.Kevin"

                            dir_bolincha = self.check_cache_bolinchas(dir_fisica_dest)
                            if dir_bolincha:
                                ip_bolincha = dir_bolincha[1]
                                port = int(dir_bolincha[2])

                                # formato de mensaje =
                                # dir_fisica_fuente ; dir_fisica_dest ; ip_inicio ; ip_final ; msg
                                msg_final = DIR_FISICA + ";" + dir_fisica_dest + ";"\
                                            + ip_inicio + ";" + ip_final + ";" + mensaje
                                print("El msj en bolinchas seria:")
                                print(msg_final)
                                self.send_to_bolinchas(msg_final, ip_bolincha, port)

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
                # Clean up the connection
                print ("\n")

        print('Closing socket')
        socket_bolinchas.close()

    # Loop que recibe de la red local y envia las solicitudes al socket que habla paletas
    # o envia de vuelta la informacion requerida si es broadcast
    def send_data(self):

        # this will make an infinite loop needed for
        # not reseting server for every client
        while (self.running):

            # Wait for a connection
            print('Waiting for connection with Bolinchas')
            connection, client_address = socket_paletas.accept()

            try:
                print('Connection from', client_address)

                # Receive the packet and send it to the next network
                while True:

                    data = connection.recv(BUFFER_SIZE)
                    if data:
                        print("Mensaje recibido: " + data.decode())
                        params = data.decode().split(';')
                        if len(params):

                            broadcast = self.isBroadcast(params[1])

                            if broadcast:
                                print 'Entro broadcast'
                                # dir fisica sender = params[0]
                                # dir broadcast * = params[1]
                                # IP solicitada = params[2]
                                network = self.check_Network(params[2])
                                print network
                                distance = -1
                                for x in ROUTING_TABLE:
                                    elements = x.split(';')
                                    if network in elements:
                                        distance = elements[3]
                                        break
                                dir_bolincha = self.check_cache_bolinchas(params[0])
                                if dir_bolincha:
                                    ip_bolincha = dir_bolincha[1]
                                    port = int(dir_bolincha[2])
                                    msg_bc = DIR_FISICA + ';*;' + params[2] + ';' + str(distance)
                                    self.send_to_bolinchas(msg_bc,ip_bolincha,port)
                            else:
                                if len(params) == 3:
                                    addr = params[0] + ';' + params[1] + ';' + params[2]
                                    exists = addr in CACHE_BOLINCHAS
                                    if not exists:
                                        CACHE_BOLINCHAS.append(addr)
                                    # for x in CACHE_BOLINCHAS:
                                    #     red_local = x.split(';')
                                    #     print red_local[0] + red_local[1] + red_local[2]
                                elif len(params) == 2:
                                    sleep(1)
                                else:
                                    # dir fisica sender = params[0]
                                    # dir fisica reciever = params[1]
                                    # IP inicio = params[2]
                                    # IP final = params[3]
                                    # Mensaje = params[4]
                                    # TODO transformar msj bolincha en msj paleta
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

                                    # TODO terminar de armar el string del puerto + ip
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
                # Clean up the connection
                print ("\n")

        print('Closing socket??')
        socket_paletas.close()

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

    def send_to_paletas(self, msg):
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            client_bolinchas.connect((IP_PALETAS, NODE_PALETAS_PORT))
            client_bolinchas.send(msg.encode())
        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % (IP_PALETAS, NODE_PALETAS_PORT, e))
        finally:
            print 'Mensaje enviado'
            client_bolinchas.close()


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

    def send_to_george(self,stringip,msj):
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            client_bolinchas.connect(('192.168.0.109', 2015))
            solicitud = "Bolinchas.Daniel;Bolinchas.Jorge;" + stringip+";140.90.0.20;"+msj
            client_bolinchas.send(solicitud)
        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % ('192.168.0.109', 2015, e))
        finally:
            client_bolinchas.close()

    def check_cache_bolinchas(self, dir_fisica):
        found = False
        if CACHE_BOLINCHAS:
            print 'Buscando en cache local'
            for x in CACHE_BOLINCHAS:
                item = x.split(';')
                if item[0] == dir_fisica:
                    found = True
                    break
            if found:
                return item
        else:
            return -1

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

    def isBroadcast(self,tipo):
        broadcast = False
        if tipo == '*':
            broadcast = True
        else:
            broadcast = False
        return broadcast

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

def join_threads(threads):
    for t in threads:
        while t.isAlive():
            t.join(5)


if __name__ == "__main__":
    main()