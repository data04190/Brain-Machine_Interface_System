from numpy import tanh
import pygame
import zmq
import struct
from config import load_parameters

# parameters
HOST = '127.0.0.1'
PORT_APP = 9999
difficulty = 0    # 0 using computed target not eeg, where 1 only using eeg
threshold_up = .3
threshold_down = -.3
load_parameters(globals())

def socket_thread(running, events, game_info):

    # event IDs for pygame, used to control player block
    event_moveup, event_movedown = events

    # open connection
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    addr = f'tcp://{HOST}:{PORT_APP}'
    socket.connect(addr)

    # loop while app running
    while running[0]:
        # receive data if socket connected, non-blocking for finishing condition
        try:
            data = socket.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError: continue   # if socket not connected
        except Exception as e: raise e  # errors

        # bytes -> float
        data,  = struct.unpack('f', data)
        
        print(f'Received {data} from {addr}')   # print for debug

        # if game information available, compute "good" target and give bias
        if game_info:
            print(game_info[0].centery, game_info[1].centery)

            # if y-coord difference large enough (sigmoid func), move player block towards ball
            target = tanh(.007*(game_info[0].centery - game_info[1].centery))
            print(target)

            # combination based on difficulty
            # zero-difficulty makes only target used
            data = difficulty*data + (1-difficulty)*target
        
        # post event signal to main thread, based on criteria (eeg + difficulty bias)
        if data > threshold_up:
            pygame.event.post(pygame.event.Event(event_moveup))
        elif data < threshold_down:
            pygame.event.post(pygame.event.Event(event_movedown))
        else:
            print('Stay')

    context.destroy()
    print('Socket closed')
