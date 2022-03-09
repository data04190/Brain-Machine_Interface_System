import pygame
from datetime import datetime
from time import time
from numpy import sign
from numpy.random import randn
from config import load_parameters
from os.path import join

# parameters
output_dir = 'G:/공유 드라이브/4N/Data/Pong'
num_trials_train = 20
num_trials_test = 20
wait_fix = 1000
wait_during_test = 50
wait_end_trial = 1000
wait_training_move = 2000
load_parameters(globals())

# parameters, not loaded by config.json
fmt = r'%Y-%m-%d_%H-%M-%S'

def session_test(flags, events):

    # event IDs for pygame, used to control session
    event_down, event_up, event_fix = events

    # open output file
    filename = join(output_dir, 'session_test_'+datetime.now().strftime(fmt)+'.csv')
    f = open(filename, 'w')

    # write csv header
    f.write("timestamp, event(1:up,-1:down)\n")
    f.flush()

    # generate trial events
    trial_events = sign(randn(num_trials_test))

    # loop for events
    for x in trial_events:

        if not flags[0]: break  # check if app closed

        # fix and wait
        pygame.event.post(pygame.event.Event(event_fix))
        pygame.time.wait(wait_fix)

        if not flags[0]: break  # check if app closed

        # decide event signal (event_up or _down) from event id (x=1 or -1)
        event = None
        if x==1: event = event_up
        elif x==-1: event = event_down

        if event:
            # post event signal
            pygame.event.post(pygame.event.Event(event))

            # write event to file
            f.write("'"+datetime.now().isoformat()+"', "+str(x)+'\n')
            f.flush()

            # wait until player touch target
            flags[1] = True # flags[1]=False when player touch target
            while flags[0] and flags[1]:    # while player moving
                pygame.time.wait(wait_during_test)
            print('trial ended')
            pygame.time.wait(wait_end_trial)

    flags[0] = False
    print('session ended')
    f.close()

def session_train(flags, events):

    # event IDs for pygame, used to control session
    event_down, event_up, event_fix, event_movedown, event_moveup = events

    # open output file
    filename = join(output_dir, 'session_train_'+datetime.now().strftime(fmt)+'.csv')
    f = open(filename, 'w')

    # write csv header
    f.write("timestamp, event(1:up,-1:down)\n")
    f.flush()

    # generate trial events
    trial_events = sign(randn(num_trials_train))
    
    # loop for events
    for x in trial_events:

        if not flags[0]: break  # check if app closed

        # fix and wait
        pygame.event.post(pygame.event.Event(event_fix))
        pygame.time.wait(wait_fix)

        if not flags[0]: break  # check if app closed

        # decide event signal (event_up or _down) from event id (x=1 or -1)
        event = None
        if x==1: event = event_up
        elif x==-1: event = event_down

        if event:
            # post event signal
            pygame.event.post(pygame.event.Event(event))

            # write event to file
            f.write("'"+datetime.now().isoformat()+"', "+str(x)+'\n')
            f.flush()

            # post signals to move training dot
            flags[1] = True
            # decide direction to move training dot
            event_move = event_movedown if event==event_down else event_moveup
            while flags[0] and flags[1]:
                pygame.time.wait(wait_training_move)
                # post signal to move training dot
                pygame.event.post(pygame.event.Event(event_move))
            pygame.time.wait(wait_end_trial)

    flags[0] = False
    print('session ended')
    f.close()
