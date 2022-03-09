import json

def load_parameters(globals_dict):
    # add config.json data to another dictionary (parameter)
    # giving globals() as parameter, this function makes data as global variables

    with open('config.json', 'r') as f:
        opt = json.load(f)
        for key in opt.keys():
            globals_dict[key] = opt[key]

if __name__=="__main__":
    # test parameter loading

    serial_port = None
    eeg_channels = None
    load_parameters(globals())

    print(serial_port)
    print(eeg_channels)
