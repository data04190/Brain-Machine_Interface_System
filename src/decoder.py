from pygame.version import ver
import torch
from torch import nn
import mne
from brainflow.board_shim import BoardIds, BoardShim
from config import load_parameters

# parameters
device = 'cuda'
board_id = BoardIds.CYTON_DAISY_BOARD.value
sfreq = BoardShim.get_sampling_rate(board_id)
eeg_channels = [1,2,3,4,5,6]
filt = {'l_freq':.5, 'h_freq':45, 'method':'iir'}
pretrained_model = "res/model.weights"  # not available yet
load_parameters(globals())

# parameters, not loaded by config.json
ch_names = ['EEG'+str(e) for e in eeg_channels]
info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')

def preprocess(data, return_raw=False): # return_raw flag for eeg plot

    raw = mne.io.RawArray(data, info, verbose=False)    # make mne object
    raw = raw.filter(l_freq=filt['l_freq'], h_freq=filt['h_freq'], method=filt['method'], verbose=False) # band-pass filter

    if return_raw: return raw   # used in eeg plot

    data = raw[:][0]
    return torch.Tensor(data).to(device)    # used in model inference

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()

        # load trained weights here
        print(f"load '{pretrained_model}' here")
    
    def forward(self, x):
        # model inference here

        return torch.Tensor([1.]) # or -1.
