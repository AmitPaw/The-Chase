import socket

HEADER = 64
PORT = 5060
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.1.26"
SERVER = "10.0.0.6"
ADDR = (SERVER, PORT)
INPUT_REQ = "!INPUT"
END_GAME = "!ENDGAME"

print("Do you wanna connect to server?\n1.\t\t Yes\nOther.\t No")
resp = input()
if resp == '1':
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    # send message
    def send(msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)


    while True:
        # blocking call, until message is received
        # first message will tell us how long the message will be, maybe not needed
        msg = ''
        msg_length = client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            # next receive will be the actual message, with a length of msg_length
            msg = client.recv(msg_length).decode(FORMAT)
            #if msg == DISCONNECT_MESSAGE:
            #connected = False

            if msg != '':
                if msg == INPUT_REQ:
                    send(input())
                elif msg == END_GAME:
                    break
                else:
                    print(msg)
    client.close()
