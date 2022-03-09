from brainflow.board_shim import BoardIds, BoardShim
import zmq
from time import time, sleep
from board import start_board
from matplotlib import pyplot as plt
import numpy as np
import matplotlib.animation as animation
from threading import Thread
from config import load_parameters
from decoder import preprocess
from mne.time_frequency import psd_welch
import os
from datetime import datetime

# parameters
HOST = '127.0.0.1'
PORT_EEG = 9998
output_dir = 'G:/공유 드라이브/4N/Data/Pong'

prewait_seconds = 1.
dt_measure = .5
dt_sleep = .5
board_id = BoardIds.CYTON_DAISY_BOARD.value
sfreq = BoardShim.get_sampling_rate(board_id)
eeg_channels = BoardShim.get_eeg_channels(board_id)

chnum_plot = 6
plotlen = 1000
cutratio = .3

figsize_inches = [16, 9]
colorlist = ['b', 'g', 'r', 'c', 'm', 'y']
FPS_EEG = 100
eeg_ylim = [-100, 100]
psd_ylim = [0, 500]
band_ylim = [0, 800]
band_fontsize = 8.4

plot_nfft = 128
bands = [[0, 4, "Delta"],
         [4, 8, "Theta"],
         [8, 12, "Alpha"],
         [12, 30, "Beta"],
         [30, 45, "Gamma"]]

load_parameters(globals())

# parameters, not loaded by config.json
dlen = int(dt_measure*sfreq)

# generate figure
fig = plt.figure(figsize=figsize_inches)
axs_eeg = [plt.subplot2grid((chnum_plot,4), (i, 0), colspan=2) for i in range(chnum_plot)]
axs_psd = [plt.subplot2grid((chnum_plot,4), (i, 2)) for i in range(chnum_plot)]
axs_band = [plt.subplot2grid((chnum_plot,4), (i, 3)) for i in range(chnum_plot)]

plotcut = plotlen/sfreq*cutratio, plotlen/sfreq*(1-cutratio)
plot_range = slice(int(plotlen*cutratio), int(plotlen*(1-cutratio)))
lines_eeg = [axs_eeg[i].plot([], [], colorlist[i])[0] for i in range(chnum_plot)]
[axs_eeg[i].set_xlim(*plotcut) for i in range(chnum_plot)]
[axs_eeg[i].set_ylim(*eeg_ylim) for i in range(chnum_plot)]
[axs_eeg[i].set_xticks([]) for i in range(chnum_plot)]
[axs_eeg[i].set_yticks([]) for i in range(chnum_plot)]

lines_psd = [axs_psd[i].plot([], [], colorlist[i])[0] for i in range(chnum_plot)]
[axs_psd[i].set_xlim(0, sfreq/2) for i in range(chnum_plot)]
[axs_psd[i].set_ylim(*psd_ylim) for i in range(chnum_plot)]
[axs_psd[i].set_xticks([]) for i in range(chnum_plot)]
[axs_psd[i].set_yticks([]) for i in range(chnum_plot)]

band_num = len(bands)
bars_band = [axs_band[i].bar(range(band_num),np.zeros(band_num),color=colorlist[i]) for i in range(chnum_plot)]
[axs_band[i].set_xlim(0, band_num) for i in range(chnum_plot)]
[axs_band[i].set_ylim(*band_ylim) for i in range(chnum_plot)]
[axs_band[i].set_xticks(range(band_num)) for i in range(chnum_plot)]
[axs_band[i].set_xticklabels([e[-1] for e in bands], fontsize=band_fontsize) for i in range(chnum_plot)]
[axs_band[i].set_yticks([]) for i in range(chnum_plot)]

def animate(frame, *fargs):
    # called for each frame

    board, eeg_channels = fargs
    
    data = board.get_current_board_data(plotlen)    # gather data from board

    data = data[eeg_channels,:]     # select channels
    raw = preprocess(data, return_raw=True)     # filtering

    data = raw[:][0]
    psds, freqs = psd_welch(raw, n_fft=plot_nfft, verbose=False)    # compute psd

    # update figure
    x = np.arange(0, plotlen/sfreq, 1/sfreq)
    for i in range(chnum_plot):
        y = data[i+1]

        if len(y)<plotlen: y = np.concatenate([np.zeros(plotlen-len(y)), y])
        lines_eeg[i].set_data(x[plot_range], y[plot_range])

        lines_psd[i].set_data(freqs, psds[i])

        [e.set_height(
            psds[i, np.logical_and(freqs>=bands[j][0], freqs<bands[j][1])].sum()
            ) for j, e in enumerate(bars_band[i])]

    # return updated objects
    plt_objects = []
    plt_objects += lines_eeg
    plt_objects += lines_psd
    for i in range(chnum_plot):
        plt_objects += bars_band[i]
    return plt_objects

def socket_thread(running, board, sfreq, eeg_channels, socket):

    # open output file
    fmt = r'%Y-%m-%d_%H-%M-%S'
    filename = os.path.join(output_dir, 'eeg_'+datetime.now().strftime(fmt)+'.csv')
    f = open(filename, 'w')

    # write csv header
    ch_labels = np.char.array(['ch'+str(i) for i in range(len(eeg_channels))])
    time_labels = np.char.array(['-time'+str(i) for i in range(dlen)])
    labels = ch_labels[:, np.newaxis] + time_labels[np.newaxis, :]
    f.write('timestamp, '+ ', '.join(labels.flatten())+'\n')

    while running[0]:
        start_time = time()

        # read data from board
        data = board.get_current_board_data(dlen)

        # make sure data size
        if data.shape[1] < dlen: continue
        data = data[eeg_channels, :]

        # write data to output file
        f.write(datetime.now().isoformat()+', '+', '.join(map(str,data.flatten()))+'\n')
        f.flush()

        # send data to decoder, if connected
        try:
            print(f'sending data of size {data.shape}') # print for debug
            socket.send(data.tobytes(), flags=zmq.NOBLOCK)  # non-blocking sending data
        except zmq.ZMQError: pass   # decoder not connected
        except Exception as e: raise e  # errors
        
        # run one loop for each {dt_sleep} second
        sleep(max(0, dt_sleep-time()+start_time))

def interface():
    
    # make socket and connect to decoder
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(f'tcp://{HOST}:{PORT_EEG}')

    # start board session and stream
    board = start_board()

    # run socket thread
    running = [True]
    t = Thread(target=socket_thread, args=(running, board, sfreq, eeg_channels, socket))
    t.start()

    # show figure with frame generated by animate()
    sleep(prewait_seconds)  # sleep at beginning for enough data to filter
    ani = animation.FuncAnimation(fig, animate, fargs=(board, eeg_channels), interval=1000//FPS_EEG, blit=True)
    plt.show()  # script blocked here until figure closed

    # after figure closed
    # finish socket thread,
    running[0] = False
    t.join()

    # board stream, session
    board.stop_stream()
    board.release_session()

    # and socket (and context)
    socket.close()
    # context.destroy()         # deadlock
    os._exit(1) # force to close app

if __name__=='__main__':
    interface()
