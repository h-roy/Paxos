import sys
import socket
print("Hello from {} with id {}".format(sys.argv[1], sys.argv[2]))
print("Running on host:", socket.gethostname())