import zmq
import decoder
import struct
import numpy as np
from config import load_parameters

# parameters
HOST = '127.0.0.1'
PORT_APP = 9999
PORT_EEG = 9998
eeg_channels = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
load_parameters(globals())

# parameters, not loaded by config.json
ch_num = len(eeg_channels)
data_shape = (ch_num, -1)

def decoder_thread():
    # load model
    model = decoder.Model()

    # open sockets
    context = zmq.Context()
    app_socket = context.socket(zmq.PUSH)
    app_socket.bind(f'tcp://{HOST}:{PORT_APP}')     # socket bind to pong app (push)
    eeg_socket = context.socket(zmq.PULL)
    eeg_socket.bind(f'tcp://{HOST}:{PORT_EEG}')     # socket bind to eeg measuring app (pull)

    while True: # break app with keyboard interrupt (ctrl+c)

        # pulling bytes from eeg measuring app
        try:
            # data = eeg_socket.recv(flags=zmq.NOBLOCK) # non-blocking
            data = eeg_socket.recv()    # blocked until signal comes
        # except zmq.ZMQError: continue   # no socket connection from eeg-app (used for non-blocking)
        except Exception as e: raise e  # errors

        # make np array from bytes
        data = np.frombuffer(data, dtype=float).copy().reshape(data_shape)

        # print for debug
        print('data.shape = ', data.shape)
        print('data[0,0] = ', data[0,0])
        print('data.sum(axis=1) = ', data.sum(axis=1))
        print('')

        # decoding
        data = decoder.preprocess(data)
        data = model(data)
        assert data.shape == (1,)   # make sure the model output is one value
        data = float(data[0])
        print('model output : ', data)

        # non-blocking pushing the model output to pong app
        try:
            app_socket.send(struct.pack('f', data), flags=zmq.NOBLOCK)
        except zmq.ZMQError: continue   # if no socket connection (from pong-app)
        except Exception as e: raise e  # errors

if __name__=='__main__':
    decoder_thread()
