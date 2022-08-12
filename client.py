#!/usr/bin/env python3

import cv2
import socket
import numpy as np
from pynput.keyboard import Key, Listener
from multiprocessing.pool import ThreadPool 


class KnackCamClient:
    def __init__(self):
        self.port = 3000
        self.packet_size=65000
        self.host_ip = "some.rover.ipv4.address"
        self.client_ip = "some.client.ipv4.address"
        self.sock = None
        self.key = "None"
        self.pool = ThreadPool(processes=2)
        self.pool2 = ThreadPool(processes=2)
        self.pool3 = ThreadPool(processes=2)
    
    #sends ip addres to host through tcp connection
    def send_addr(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host_ip, 3002))
    
    #connects to another port and sends keyboard presses that client made to server
    def send_key_input(self):
        sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        sock.connect((self.host_ip,3001))
        print("hi from send")
        while True:
            if self.key != "None":
                sock.sendall(bytes(self.key,'utf8'))
            else:
                print("None")
                

    #opens up port for server to send frame data to client
    def connect_to_host(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.client_ip,self.port))
    
    #gets frame data from server and modifies frames
    def get_frame(self):
        #gets number of packets a frame was split into
        num_packs = int.from_bytes(self.sock.recv(self.packet_size),'little')
        buffer = None
        #gets all the packets and creates a buffer
        for i in range (num_packs):
            data = self.sock.recv(self.packet_size)
            if i == 0:
                buffer = data
            else:
                buffer += data
        #decodes the buffer into one frame
        frame = np.frombuffer(buffer, dtype=np.uint8)
        frame = frame.reshape(frame.shape[0], 1)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        frame = cv2.flip(frame, 1)
        #Add what button client pressed to frame
        text = f"Button Pressed: {self.key}"
        coordinates = (10,470)
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255,255,255)
        thickness = 2
        frame = cv2.putText(frame, text, coordinates, font, fontScale, color, thickness, cv2.LINE_AA)
        return frame        
    
    #listens to keyboard presses from client. This is a blocking method
    def listen(self):
        print("hi")
        with Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            listener.join()

    def on_press(self,key):
        print(key)
        self.key = str(key)[1]

    def on_release(self,key):
        self.key = 'None'
        if key == Key.esc:
            # Stop listener
            return False

    #displays live feed from camera with modefied frames
    def stream(self):
        while True:
            frame = self.get_frame()
            if frame is not None and type(frame) == np.ndarray:
                cv2.imshow("Stream", frame)

                if cv2.waitKey(1) == 27:
                    return False

    #start each thread processes
    def start_processes(self):
        while True:
            async_result = self.pool.apply_async(self.listen) 
            async_result2 = self.pool2.apply_async(self.stream)
            async_result3 = self.pool3.apply_async(self.send_key_input)
        
            return_val = async_result.get()
            return_val2 = async_result2.get()
            return_val3 = async_result3.get()
                
    


    def run_client(self):
        self.send_addr()
        self.connect_to_host()
        self.start_processes()




if __name__ == "__main__":
    foo = KnackCamClient()
    foo.run_client()


        