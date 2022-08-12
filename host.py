#!/usr/bin/env python3

import cv2
import socket
import math
from multiprocessing.pool import ThreadPool

class KnackCamServer:
    def __init__(self):
        self.port = 3000
        self.packet_size=65000
        self.camera = 0
        self.host_ip = "some.rover.ipv4.address"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cap = cv2.VideoCapture(self.camera)
        self.run_server_threads = ThreadPool(processes=2)
        self.recv_input_thread = ThreadPool(processes=2)
        self.client_addr = None

    def get_frame(self):
        retval, frame = self.cap.read()
        return frame

    def compression(self,frame):
        comp_frame = cv2.imencode(".jpg",frame)
        return comp_frame[1]

    def get_numpacks(self, frame):
        frame = frame.tobytes()
        frame_size = len(frame)
        num_packs = 1+abs(math.floor(1-frame_size/self.packet_size))
        return num_packs

    def get_client_addr(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host_ip, 3002))
            s.listen(1)
            conn, addr = s.accept()
            self.client_addr = addr

    def send_to_client(self, addr, data):
        self.sock.sendto(data,(addr[0],self.port))
    
    def create_datapacks(self, comp_frame, num_packs):
        left = 0
        right = self.packet_size
        data = []
        for i in range(num_packs):
            data.append(comp_frame[left:right])
            left = right
            right += self.packet_size
        return data
    
    def recv_input(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host_ip, 3001))
            sock.listen(1)
            conn, addr = sock.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if data:
                        print("Key input: ", data.decode(encoding='utf8')[0])

    
    def run_server(self):
        if self.client_addr is None:
            self.get_client_addr()

        frame = self.get_frame()
        while frame.any():
            comp_frame = self.compression(frame)
            num_packs = self.get_numpacks(comp_frame)
            self.send_to_client(self.client_addr,num_packs.to_bytes(1,'little'))
            data = self.create_datapacks(comp_frame, num_packs)
            for i in range(num_packs):
                self.send_to_client(self.client_addr,data[i])
            frame = self.get_frame()
    
    def start_processes(self):
        while True:
            async_result =self.run_server_threads.apply_async(self.run_server)
            async_result2 = self.recv_input_thread.apply_async(self.recv_input)
            return_val = async_result.get()
            return_val2 = async_result2.get()

if __name__ == "__main__":
    foo = KnackCamServer()
    foo.start_processes()



    



        

