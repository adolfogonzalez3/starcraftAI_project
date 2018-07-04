#!/usr/bin/env python3
import argparse
import numpy as np
from itertools import count
import random
from time import time

from tqdm import tqdm, trange

import matplotlib.pyplot as plt
#import pygame
from PygameVisualizer import PygameVisualizer

from PickleSocket import PickleSocket
from RLAgents import DQNAgent
from rangefloat import rangefloat

NUMBER_OF_FRAMESKIPS = 0



class GameSingleAgent(object):
    def __init__(self, host='localhost', port=50008):
        self.connection = PickleSocket(host, port, as_server=False)
        self.AllyHealth = None
        self.EnemyHealth = None

    def open(self):
        self.connection.open()

    def close(self):
        self.connection.close(None, None, None)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        
    def frame_step(self, action):
        wrapped_action = [action]
        self.connection.send(wrapped_action)
        state = self.connection.read()
        observation = state['observations'][0]
        reward = state['rewards'][0]
        terminal = state['terminal'][0]
        if 'episode end' in state:
            terminal = True
        return observation, reward, bool(terminal)

def game_init(game_state, agent):
    action = np.zeros(17)
    action[16] = 1
    
    observation, reward, terminal = game_state.frame_step(16)
    
    agent.initialize(observation, action)
    
        
        
def fill_memory(game_state, agent, number_of_frames=1024):
    terminal = False
    
    game_init(game_state, agent)
    
    for steps in trange(number_of_frames):
        #chosen_action = random.randint(0, 16)
        action = agent.choose_random()
        chosen_action = np.argmax(action)
        
        single_step_reward = 0
        for _ in range(1+NUMBER_OF_FRAMESKIPS):
            observation, reward, terminal = game_state.frame_step(chosen_action)
            
            
            allies = observation == 1
            enemies = observation == -1
            null = np.zeros(observation.shape)
            
            rgb = np.stack([allies, enemies, null], axis=-1)*255
            
            VISUALIZER.blit(rgb)
            
            single_step_reward += reward
            if terminal is True:
                break

        agent.feedback(observation, single_step_reward, terminal)
        if terminal is True:
            game_init(game_state, agent)
    
    while terminal is False:
        action = random.randint(0, 16)
        observation, reward, terminal = game_state.frame_step(action)
        
        #agent.feedback(observation, reward, terminal)
        
def run_episode(game_state, agent, training=True):
    terminal = False
    number_of_steps = 0
    
    game_init(game_state, agent)
    total_reward = 0
    while terminal is False:
        if training is True:
            action = agent.choose()
        else:
            action = agent.choose(epsilon=0.005)
        chosen_action = np.argmax(action)
        single_step_reward = 0
        for _ in range(1+NUMBER_OF_FRAMESKIPS):
            observation, reward, terminal = game_state.frame_step(chosen_action)
            single_step_reward += reward
            if terminal is True:
                break
        
        total_reward += single_step_reward
        #print('Action: ', action, ' Reward: ', reward, ' Total Reward: ', total_reward)
        agent.feedback(observation, single_step_reward, terminal)
        agent.train()
        
        number_of_steps += 1
    return total_reward, number_of_steps

def run_test(game_state, agent, number_of_tests=1, progressbar=False):
    '''Run a series of tests and return mean and std of reward.'''
    if progressbar is True:
        tests = trange(number_of_tests)
        tests.set_description('Testing...')
    else:
        tests = range(number_of_tests)
    
    test_reward = []
    for _ in tests:
        reward, steps = run_episode(game_state, agent, training=False)
        test_reward.append(reward)
    return np.mean(test_reward), np.std(test_reward)
    
def main(game_state, agent=None):
    if agent is None:
        agent = DQNAgent('model_starcraft_20.h5', epsilon=rangefloat(0.1, 0.0001,
                        100000, forever=True), memory_size=100000,
                        with_target=True, replayType='simple')
    
    episode_rewards = []
    episode_deviations = []
    episode_steps = []
    
    fill_memory(game_state, agent, 3200)
    with trange(250) as episodes:
        for ep_no in episodes:
            reward, steps = run_episode(game_state, agent, training=True)
            episode_steps.append(steps)
            #if ep_no%10 == 0:
            #    reward, std = run_test(game_state, agent, number_of_tests=20)
            #    episodes.set_description('Reward: {:.3f} ± {:.2f}'.format(reward, std))
            #    episode_rewards.append(reward)
            #    episode_deviations.append(std)
        
    #X = np.arange(len(episode_steps))
    # print(X, episode_steps)
    # plt.ylim(800)
    #plt.plot(X, episode_steps)
    #plt.show()
        
    #run_test(game_state, agent, number_of_tests=1000)

    return episode_rewards, episode_deviations, episode_steps, agent
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='The name of the experiment.')
    parser.add_argument('port', help='The port which the server should connect to.',
                        type=int)

    args = parser.parse_args()
    
    VISUALIZER = PygameVisualizer().open()
    
    print(args)
    
    path_and_filename = 'Results_Frameskip4/timestep_results_{!s}.csv'
    
    with GameSingleAgent(host='localhost', port=args.port) as game_state:
        try:
            for i in range(10):
                _, _, episode_steps, _ = main(game_state)
                with open(path_and_filename.format(i), 'wt') as csv:
                    episode_steps_str = [str(step) for step in episode_steps]
                    results_string = '{}\n'.format(','.join(episode_steps_str))
                    csv.write(results_string)
        except EOFError:
            print('Connection closed.')
        finally:
            VISUALIZER.close()