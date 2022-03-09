# Mind Pong

system : EEG -> decoder (server) -> Pong

EEG
 - OpenBCI, CYTON_DAISY board connected with serial port

decoder
 - preprocessing with mne package, inference with pytorch

Pong

 - EEG training/testing sessions
 - and Pong (based on https://github.com/clear-code-projects/Pong_in_Pygame/blob/master/pong11_sprites.py)

## install

git clone https://github.com/4NBrain/pong.git

cd pong

pip install -r requirements.txt

## settings

app is controlled by config.json

make sure proper serial_port (eg.: "COM4") before running src/run_eeg.py

## run

running decoder

 - python src/run_decoder.py
  
running pong app

 - python src/run_app.py
  
running eeg app

 - python src/run_eeg.py
