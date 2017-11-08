# Import socket module
import socket 
import sys

# Create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the port on which you want to connect
port = 1234

host = socket.gethostname()
# connect to the server on local computer
#s.connect(('192.168.0.109', port))
s.connect((host, port))
while True:
	try:
		msg = raw_input("Enter message: ")
		s.send(msg)
	except (EOFError):
		break
	#while msg != 'exit':
	
	print >>sys.stderr, 'Sent "%s"' % msg
	#data = c.recv(BUFFER_SIZE)
	#time.sleep(3)
# close the connection
s.close()
