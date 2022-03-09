from json import load
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from config import load_parameters

# parameters
serial_port = 'COM4'
board_id = BoardIds.CYTON_DAISY_BOARD.value
load_parameters(globals())

def start_board():
    params = BrainFlowInputParams()
    params.serial_port = serial_port
    params.serial_number = ''
    params.timeout = 0
    params.other_info = ''
    params.file = ''
    params.mac_address = ''
    params.ip_address = ''
    params.ip_port = 0
    params.ip_protocol = 0
    
    board = BoardShim(board_id, params)
    board.prepare_session()
    board.start_stream()

    return board
