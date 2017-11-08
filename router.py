import threading
from time import sleep

import socket
import sys
import re

#Socket buffer
BUFFER_SIZE = 1024

# Current node's IP
ROUTER_IP = '127.0.0.1'  # '200.0.2.4'
ROUTER_PORT = 10001

# Dispatcher's IP
DISPATCHER_IP = '127.0.0.1'
DISPATCHER_PORT = 10000

# Bolinchas's IP
NODE_BOLINCHAS_IP = '127.0.0.1'
NODE_BOLINCHAS_PORT = 10002

# Paletas's IP
NODE_PALETAS_IP = '127.0.0.1'
NODE_PALETAS_PORT = 10003

DISPATCHER_IP_BOLINCHAS = '127.0.0.1'
DISPATCHER_PORT_BOLINCHAS = 10000

# Array of other computers on net
ARP_TABLE = {}

#
#   "192.168.0.2:3000":{"2" : "192.135.0.2:4000"}
#


# Inicializa el socket que se pega a las paletas
socket_paletas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_paletas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Pallets server loop created')

try:
    socket_paletas.bind((NODE_BOLINCHAS_IP, NODE_BOLINCHAS_PORT))
    print('Pallets Socket bind complete')

except socket.error as msg:
    import sys

    print('Pallets bind failed. Error : ' + str(sys.exc_info()))
    sys.exit()

# Start listening on socket
socket_paletas.listen(10)
print('Pallets interface now listening')

# Inicializa el socket que se pega a las bolinchas
socket_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Bolinchas server loop created')

try:
    socket_bolinchas.bind((NODE_PALETAS_IP, NODE_PALETAS_PORT))
    print('Bolinchas bind complete')

except socket.error as msg:
    import sys

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

        ARP_TABLE['test'] = 'okok'
        ARP_TABLE['tes2t'] = 'okok'
        for key, value in ARP_TABLE.items():
            print (key + ' : ' + value + '\n')

            # Thread para la red de paletas
        t1 = threading.Thread(target=self.pallets_loop)

        # Thread para la red de bolinchas
        t2 = threading.Thread(target=self.ball_loop)

        # Make threads daemonic, i.e. terminate them when main thread
        # terminates. From: http://stackoverflow.com/a/3788243/145400
        t1.daemon = True
        t2.daemon = True

        self.threads.append(t1)
        # self.threads.append(t2)

        t1.start()
        sleep(1)
        t2.start()

    # Loop para esperar por requests de los servers auxiliares de los paleteros
    def ball_loop(self):
        self.report_to_dispatcher_bolinchas()
        # this will make an infinite loop needed for
        # not reseting server for every client
        while (self.running):
            # conn, addr = soc.accept()
            # ip, port = str(addr[0]), str(addr[1])
            # print('Accepting connection from ' + ip + ':' + port)

            # Wait for a connection
            print('Bolinchas interface waiting for a connection')
            connection, client_address = socket_bolinchas.accept()

            try:
                print('Bolinchas received connection from', client_address)

                # # Receive the packet and send it to the next network
                while True:

                    data = connection.recv(500)
                    if data:
                        print(data.decode())
                        params = data.decode().split(';')
                        if len(params):
                            print("IP inicio = " + params[2])
                            print("IP final = " + params[3])
                            print("Mensaje = " + params[4])

                            # TODO transformar msj bolincha en msj paleta
                            msg_paleta = params[0] + "%" + params[1] + "%" + params[2]
                            print("El msj en paletas seria:")
                            print(msg_paleta)

                            # socket_paletas.send(msg_bolincha.encode())
                            #Abrir socket cliente para paletas

                        else:
                            print('No data from', client_address)


                    # print('sending data back to the client')
                    # connection.send(b'Recibi la vara malparido')

                    else:
                        print('no data from', client_address)
                        # 	break
                        # else:
                        # 	print('no data from', client_address)
                    break


            except:
                print("Terible error!")
                import traceback
                traceback.print_exc()

            finally:
                # Clean up the connection
                print ("Test \n")

        print('Closing socket??')
        socket_bolinchas.close()

    # Loop para esperar por requests de los servers auxiliares de los paleteros
    def pallets_loop(self):

        cache_bolinchas = []
        dir_fisica_fuente = 'B.D'
        ip_final = '140.90.0.1'

        # this will make an infinite loop needed for
        # not reseting server for every client
        while (self.running):
            # conn, addr = soc.accept()
            # ip, port = str(addr[0]), str(addr[1])
            # print('Accepting connection from ' + ip + ':' + port)

            # Wait for a connection
            print('Palets interface waiting for a connection')
            connection, client_address = socket_paletas.accept()

            try:
                print('Palets connection from', client_address)

                # # Receive the packet and send it to the next network
                while True:

                    data = connection.recv(500)
                    if data:
                        print(data.decode())
                        params = data.decode().split(';')
                        if len(params):
                            print("la ip es " + params[0]) # recibir la ip que envio el mensaje
                            print("el puerto es " + params[1]) # recibir la ip que recibira el mensaje
                            print("el msj es " + params[2]) # recibir el mensaje enviado

                            # TODO transformar msj paleta en msj bolincha

                            if self.msgToNetwork(ip_final):
                                dir_fisica_dest = "B.J"
                            else:
                                dir_fisica_dest = "B.K"

                            ip_bolincha = self.check_dispatcher_bolinchas(cache_bolinchas,dir_fisica_dest)
                            port = 8080

                            # formato de mensaje =
                            # dir_fisica_fuente ; dir_fisica_dest ; ip_inicio ; ip_final ; msg
                            msg_bolincha = dir_fisica_fuente + ";" + dir_fisica_dest + ";"\
                                           + params[0] + ";" + params[1] + ";" + params[2]
                            print "El msj en bolinchas seria: ", msg_bolincha

                            # TODO terminar de armar el string del puerto + ip
                            # socket_bolinchas.send(msg_bolincha.encode())
                            self.send_to_bolinchas(msg_bolincha,ip_bolincha,port)

                        else:
                            print('no data from', client_address)


                    # print('sending data back to the client')
                    # connection.send(b'Recibi la vara malparido')

                    else:
                        print('no data from', client_address)
                        # 	break
                        # else:
                        # 	print('no data from', client_address)

                    break


            except:
                print("Terible error!")
                import traceback
                traceback.print_exc()

            finally:
                # Clean up the connection
                print ("Test \n")

        print('Closing socket??')
        socket_paletas.close()

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

    def check_dispatcher_bolinchas(self, cache_table, dir_fisica):
        found = False
        for x in cache_table:
            item = x.split(';')
            if item[0] == dir_fisica:
                found = True
                break
        if found:
            return item[1]
        else:
            client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_bolinchas.connect((DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS))
            addr = client_bolinchas.recv(BUFFER_SIZE)
            cache_table.append(addr)
            ip = addr.split(";")
            client_bolinchas.close()
            return ip[1]

    def report_to_dispatcher_bolinchas(self):
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_bolinchas.connect((DISPATCHER_IP_BOLINCHAS, DISPATCHER_PORT_BOLINCHAS))
        ip_info = 'B.D;' + NODE_BOLINCHAS_IP
        client_bolinchas.send(ip_info.encode())

    def send_to_bolinchas(self, msg, ip, port):
        client_bolinchas = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_bolinchas.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_bolinchas.connect((ip, port))
        client_bolinchas.send(msg.encode())
        client_bolinchas.close()


def join_threads(threads):
    for t in threads:
        while t.isAlive():
            t.join(5)


if __name__ == "__main__":
    main()
