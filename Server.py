mport socket
import threading
from Game import Game

HEADER = 64
PORT = 5060
MAX_CONNECTIONS = 3
SERVER = socket.gethostbyname(socket.gethostname()) # get local ip address
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
INPUT_REQ = "!INPUT"
END_GAME = "!ENDGAME"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 1st argument is family, 2nd is protocol
server.bind(ADDR)

def startGame(sendCb,recCb):
    testGame = Game(sendCb,recCb)
    testGame.initialRound()
    testGame.actualGame()

def handle_client(conn, addr):
    # send message
    def sendToClient(msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        conn.send(send_length)
        conn.send(message)

    # receive message
    def recFromClient():
        sendToClient(INPUT_REQ)
        # blocking call, until message is received
        # first message will tell us how long the message will be, maybe not needed
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            # next receive will be the actual message, with a length of msg_length
            msg = conn.recv(msg_length).decode(FORMAT)
        return msg

    def introScreen():
        sendToClient("Do you want to play the game?\n1.\t\t Yes\nOther.\t No")
        response = recFromClient()
        if response == '1':
            startGame(sendToClient, recFromClient)
        return response

    def disconnect(limit=0):
        if limit:
            print(f"[ATTEMPTED CONNECTION] {addr} Server limit reached. Kicking client.")
        else:
            print(f"[CONNECTION LOST] {addr} disconnected.")
        sendToClient(END_GAME)
        conn.close()

    def limitConnections(connections):
        if connections > MAX_CONNECTIONS:
            sendToClient("SERVER BUSY")
        return connections > MAX_CONNECTIONS

    limitReached = limitConnections(threading.activeCount() - 1)
    if limitReached:
        disconnect(limitReached)
    else:
        print(f"[NEW CONNECTION] {addr} connected.")
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

        while True:
            restart = introScreen()
            if restart != '1':
                disconnect()
                break

# start server
def start():
    # listen for connections and pass them for further handling
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    while True:
        # blocking call, will wait for a new connection to the server, store it in conn (obj), and addr
        conn, addr = server.accept()
        # start a new thread to handle a client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

print("[STARTING] server is starting...")
start()
