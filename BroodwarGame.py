
import argparse
from BroodwarInterface import BroodwarInterface
from PickleSocket import PickleSocket
import cybw
from itertools import count
import numpy as np
import os

import random

from time import time

ENEMY_TYPE = [cybw.UnitTypes.Terran_SCV]
ALLY_TYPE = [cybw.UnitTypes.Terran_Marine]
TERRAN_SCV = cybw.UnitTypes.Terran_SCV
TERRAN_MARINE = cybw.UnitTypes.Terran_Marine


ACTION_DELAY = 10
DEBUG = False
AGENT_VIEW_WIDTH = 2048
AGENT_VIEW_HEIGHT = 2048
AGENT_ACTION_WIDTH = 640
AGENT_ACTION_HEIGHT = 640



def reduce(array, reduceBy=2):
    '''Reduce the size of an array by squashing the array.

    If there exists a conflict with merging adjacent cells of differing values,
    add their values together and if the sum is less than zero make the value
    -1 otherwise 1'''
    width, height = array.shape
    new_array = np.zeros((int(width/reduceBy), int(height/reduceBy)))
    array[0:reduceBy, 0:reduceBy]
    for x in range(0, reduceBy):
        for y in range(0, reduceBy):
            new_array = new_array + array[x::reduceBy,y::reduceBy]
    new_array[new_array < 0] = -1
    new_array[new_array > 0] = 1
    #new_array = new_array/reduceBy**2
    return new_array

    
def compute_obs_reward(interface, all_units, prev_observations):
    observations = []
    #rewards = []
    
    enemy_ids = interface.getEnemiesID()
    player_id = [interface.getSelfID()]
    
    #enemy_health = sum(interface.getHealth(players=enemy_ids))
    #ally_health = sum(interface.getHealth(players=player_id))
    
    alive_units = interface.getUnitIDs(players=player_id)
    
    dead = np.zeros(len(all_units), dtype=np.bool)
    for i, unit_id in enumerate(all_units):
        if unit_id in alive_units:
            unit_position = interface.getPositions(units=[unit_id])[0]
            
            interface.set_viewbox_position(unit_position-[300, 150])
            
            position = np.array(interface.get_map_dims())//2
            position = position - [AGENT_VIEW_WIDTH//2, AGENT_VIEW_HEIGHT//2]
            
            surrounding_allies = interface.createUnitsMap(position, AGENT_VIEW_WIDTH, AGENT_VIEW_HEIGHT, players=player_id, types=ALLY_TYPE)
            squashed_surround_allies = reduce(surrounding_allies, 16)
            surrounding_enemies = interface.createUnitsMap(position, AGENT_VIEW_WIDTH, AGENT_VIEW_HEIGHT, players=enemy_ids, types=ENEMY_TYPE)
            squashed_surround_enemies = reduce(surrounding_enemies, 16)
            
            combined_surroundings = squashed_surround_enemies*-1 + squashed_surround_allies
        else:
            combined_surroundings = prev_observations[i]
            dead[i] = True

        #reward = (previous_enemy_health - enemy_health) - (previous_ally_health - ally_health)
        observations.append(combined_surroundings)
        #rewards.append(reward)
    
    return observations, dead #rewards, dead

def drawGrid(X, Y, width=320, height=320, rows=2, columns=2, color=cybw.Colors.Blue):
    '''Draws a Grid with the unit being in the center of the drawn Grid.'''
    Broodwar = cybw.Broodwar
    half_width = width//2
    half_height = height//2
    row_width = width//rows
    column_height = height//columns
    for row in range(rows):
        for column in range(columns):
            Broodwar.drawBoxMap(cybw.Position(X+row*row_width, Y+column*column_height),
                                cybw.Position(X+(row+1)*row_width, Y+(column+1)*column_height), color)
    
def drawCircle(X, Y, radius=5):
    Broodwar = cybw.Broodwar
    Position = cybw.Position(X, Y)
    Broodwar.drawCircleMap(Position, radius, cybw.Colors.Green)
    
def run_episode(interface, socket, timestep_limit=800):
    previous_actions = None
    
    enemy_ids = interface.getEnemiesID()
    player_id = [interface.getSelfID()]
  
    units_all = interface.getUnitIDs(players=player_id)
    
    starting_enemy_health = TERRAN_SCV.maxHitPoints()
    starting_ally_health = TERRAN_MARINE.maxHitPoints()
    
    previous_enemy_health = starting_enemy_health
    previous_ally_health = starting_ally_health
        
    # Should be safe to set to None in beginning; Except all units to be visible
    prev_observations = None
    current_timestep = 0
    
    action_debug = 0
    
    while interface.is_end() is False:
        
        actions = socket.read()
        
        unit_ids = interface.getUnitIDs(players=player_id)
        unit_positions = interface.getPositions(players=player_id)
        for id, position, action in zip(unit_ids, unit_positions, actions):
            X, Y = position - [AGENT_ACTION_WIDTH//2, AGENT_ACTION_HEIGHT//2]
            
            action = action_debug
            action_debug = (action_debug+1)%17
            
            if DEBUG is True:
                drawGrid(X, Y, width=AGENT_ACTION_WIDTH, height=AGENT_ACTION_HEIGHT, rows=4, columns=4)
            if action is not None:
                if action == 16:
                    X = X + (AGENT_ACTION_WIDTH//2)
                    Y = Y + (AGENT_ACTION_HEIGHT//2)
                else:
                    X = X + (AGENT_ACTION_WIDTH//4)*(action%4)+(AGENT_ACTION_WIDTH//8)
                    Y = Y + (AGENT_ACTION_HEIGHT//4)*(action//4)+(AGENT_ACTION_HEIGHT//8)
                    interface.attack_position(id, (X, Y))

                if DEBUG is True:
                    drawCircle(X, Y, 10)
        
        interface.update(ACTION_DELAY)
        
        
        enemy_health = sum(interface.getHealth(players=enemy_ids))
        ally_health = sum(interface.getHealth(players=player_id))
        
        observations, dead = compute_obs_reward(interface, units_all, prev_observations)
        reward = (previous_enemy_health - enemy_health)/starting_enemy_health - (previous_ally_health - ally_health)/starting_ally_health
        rewards = [reward]
        print('E: ', enemy_health, ' R: ', rewards, ' DEAD: ', dead)
        
        
        previous_ally_health = ally_health
        previous_enemy_health = enemy_health
        
        
        prev_observations = observations
        for i, d in enumerate(dead):
            if d is True:
                prev_observations[i] = None
        
        data = {'observations': observations, 'rewards': rewards, 'terminal': dead}
        socket.send(data)
        
        current_timestep += 1
        if timestep_limit is None:
            if enemy_health == 0 or ally_health == 0:
                break
        elif current_timestep > timestep_limit or enemy_health == 0 or ally_health == 0:
            break
        

    actions = socket.read()
    
    enemy_health = sum(interface.getHealth(players=enemy_ids))
    ally_health = sum(interface.getHealth(players=player_id))
    
    observations, dead = compute_obs_reward(interface, units_all, prev_observations)
    reward = (previous_enemy_health - enemy_health)/starting_enemy_health - (previous_ally_health - ally_health)/starting_ally_health
    rewards = [reward]
    #print('E: ', enemy_health, ' R: ', rewards, ' DEAD: ', dead)
        
    data = {'observations': observations, 'rewards': rewards, 'terminal': [True], 'episode end': True}
    socket.send(data)


if __name__ == '__main__':
    #ENEMY_TYPE = cybw.UnitTypes.Protoss_Zealot
    
    
    map_path = os.environ['BROODWAR_MAP_PATH']
    
    
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='The port which the server should connect to.',
                        type=int)
    args = parser.parse_args()
    print(args)
    with PickleSocket(host='localhost', port=args.port) as s:
        print("Connecting...")
        interface = BroodwarInterface()
        
        interface.connect()
        
        test_map = os.path.join(map_path, 'test_{!s}.scm')
        games = count()
        #games = tqdm(games)
        #games.set_description('Gathering data...')
        
        for game_no in games:
            interface.set_map(test_map.format(random.randrange(4)))
            run_episode(interface, s, timestep_limit=None)
            