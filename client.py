import ast
import socket
from time import sleep, time
from threading import Thread
from config import cluster
from random import randint

prev_time = time()
count_tput = 1
count_lat = 0
BUFFER_SIZE = 1024
threads = []

class Client:
    def __init__(self):
        self.socket_setup()
        self.thread_setup()

    def socket_setup(self):
        # TODO: Print identifiers in the cluster
        self.identifier = input("Which datacenter do you want to connect to? (A, B, C, D or E) ")

        if self.identifier not in cluster:
            ip = input("IP: ")
            port = int(input("Port: "))
            self.server_addr = (ip, port)
        else:
            self.server_addr = cluster[self.identifier]

        self.client_addr = (self.server_addr[0], self.server_addr[1] + 10)

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock.bind(self.client_addr)

    def send_msg(self, data):
        msg = bytes(data, encoding="ascii")
        self.server_sock.sendto(msg, self.server_addr)
        print("Message sent to", self.server_addr)

    def process_user_input(self, user_input):
        words = user_input.split(" ")
        command = words[0]
        if len(words) > 1:
            arg = words[1]

        milliseconds = time() * 1000

        if command == "show" or command == "random":
            self.send_msg("{},{},{}".format(command, str(self.client_addr[1]), str(milliseconds)))
        elif command == "buy" and arg.isdigit():
            self.send_msg("{},{},{},{}".format(command, arg, self.client_addr[1], str(milliseconds)))
        elif command == "change":
            # Kill listen_thread before changing server_sock
            self.server_sock.close()
            self.client_sock.close()
            self.socket_setup()
        else:
            print("Couldn't recognize the command", user_input)
    
    def stats(self, t_send, t_rcvd):
        global tput_file
        global prev_time
        global count_tput
        global count_lat

        if t_send - prev_time > 1000:
            avg_lat = count_lat/float(count_tput)
            with open('tput.txt', 'a+') as tput_file:
                tput_file.write("Throughput (msgs per second):" + str(count_tput) + ", Avg Latency (ms):" + str(round(avg_lat, 1)) + "\n")
            prev_time = t_send
            count_lat = 0
            count_tput = 0

        count_tput += 1
        lat = abs(float(t_rcvd) - float(t_send))
        count_lat += lat
        with open('latency.txt', 'a+') as lat_file:
            lat_file.write(str(round(lat,1)) + "\n")

    def listen(self):
        while True:
            data, addr = self.client_sock.recvfrom(BUFFER_SIZE)
            msg = data.decode("utf-8")
            t_rcvd = time() * 1000

            if msg[0].isdigit():
                msg_list = ast.literal_eval(msg)
                for line in msg_list:
                    print(line)
                t_send = float(msg_list[-1])
                self.stats(t_send, t_rcvd)
            else:
                t_send = float(msg.split(",")[-1])
                self.stats(t_send, t_rcvd)
                print(msg)

    def msg_load(self):
        msg_data = ''
        msg_per_sec = 1
        msg_count = 0
        rate_interval = 5000
        while True:
            msg_time1 = time() * 1000
            while True:
                msg_time2 = time() * 1000

                if msg_time2 - msg_time1 < rate_interval:
                    sleep(1 / float(msg_per_sec))
                    msg_count = msg_count + 1
                    num_tickets = randint(1, 100)
                    msg_data = ('buy ' + str(num_tickets) + ' tickets')
                    self.process_user_input(msg_data)

                else:

                    if msg_per_sec < 100:
                        msg_per_sec += 1

                    break

    def thread_setup(self):
        msg_thread = Thread(target=self.msg_load)
        threads.append(msg_thread)
        msg_thread.start()
        
        listen_thread = Thread(target=self.listen)
        threads.append(listen_thread)
        listen_thread.start()

def run():
    client = Client()

if __name__ == "__main__":
    with open('tput.txt', 'w') as tput_file:
        tput_file.write("")
    with open('latency.txt', 'w') as tput_file:
        tput_file.write("")
    run()
