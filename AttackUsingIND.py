'''Module implements an agent which uses a neural network to determine its actions.
Requirements:
python3.5 (32-bit)
'''

import argparse
import cybw
from PIL import Image
from time import sleep, time
import numpy as np
import pylab as pl
import pickle
import random
from itertools import count
from tqdm import tqdm
#from numpy.ufunc import reduceat


from TwoWayConnection import TwoWayClient

client = cybw.BWAPIClient
Broodwar = cybw.Broodwar

def grab_surroundings(unit, Broodwar, width=320, height=320):
    '''Grab all surrounding units and mark them as ally or enemy.

    The enemy and ally types are currently hardcoded otherwise they will capture the
    units which are only used to capture the vision of the map. In the future, it may be
    better to pass sets which contain the allies and enemies which I want to capture. Or to
    just grab a visible units around our unit where the visible units have their unit type
    as members of a provided set.'''
    decouple = lambda X: (X.x, X.y)
    unit_position = np.array(decouple(unit.getPosition()))
    all_marines = [u.getType() == cybw.UnitTypes.Terran_Marine for u in Broodwar.getAllUnits()]
    allies = np.array(all_marines)
    all_zerglings = [u.getType() == cybw.UnitTypes.Zerg_Zergling for u in Broodwar.getAllUnits()]
    enemies = np.array(all_zerglings)
    all_units = (u for u in Broodwar.getAllUnits())
    otherUnits_positions = np.array([decouple(u.getPosition()) for u in all_units])
    all_units = (u for u in Broodwar.getAllUnits())
    otherUnits_health = np.array([u.getHitPoints()+u.getShields() for u in all_units])
    distance = otherUnits_positions - unit_position
    distance = np.sqrt(np.sum(np.power(distance, 2), axis=1)) < width/2
    surround = np.zeros((width, height))
    otherUnits_positions = (otherUnits_positions - unit_position + width/2).astype(np.int32)
    ############################################################################
    # For Allies
    ############################################################################
    index = np.logical_and(distance, allies)
    for (x, y), h in zip(otherUnits_positions[index], otherUnits_health[index]):
        surround[x, y] = 1
    ############################################################################
    # For Enemies
    ############################################################################
    np.logical_and(distance, enemies)
    for (x, y), h in zip(otherUnits_positions[index], otherUnits_health[index]):
        surround[x, y] = -1
    return surround

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
    new_array[new_array >= 0] = 1
    #new_array = new_array/reduceBy**2
    return new_array

def drawRectangleOnUnit(Broodwar, unit, width=20, height=20, color=cybw.Colors.Blue):
    '''Draws a rectangle with the unit being in the center of the drawn rectangle.'''
    half_width = int(width/2)
    half_height = int(height/2)
    position = unit.getPosition()
    Broodwar.drawBoxMap(cybw.Position(position.x-half_width, position.y-half_height),
                        cybw.Position(position.x+half_width, position.y+half_height), color)

def drawGrid(Broodwar, unit, width=320, height=320, rows=2, columns=2, color=cybw.Colors.Blue):
    '''Draws a Grid with the unit being in the center of the drawn Grid.'''
    half_width = int(width/2)
    half_height = int(height/2)
    position = unit.getPosition()
    row_width = int(width/rows)
    column_height = int(height/columns)
    for row in range(rows):
        for column in range(columns):
            Broodwar.drawBoxMap(cybw.Position(position.x-half_width++row*row_width, position.y-half_height+column*column_height),
                                cybw.Position(position.x-half_width+(row+1)*row_width, position.y-half_height++(column+1)*column_height), color)

def mark_surrounding_units(unit, Broodwar, width=320, height=320):
    surroundings = Broodwar.getAllUnits()
    surroundings = [s for s in surroundings if unit.getDistance(s) < 150]
    drawRectangleOnUnit(Broodwar, unit, width=width, height=height, color=cybw.Colors.Blue)
    for s in surroundings:
        if s.getPlayer().getID() != Broodwar.self().getID():
            drawRectangleOnUnit(Broodwar, s, width=40, height=40, color=cybw.Colors.Red)

def reconnect():
    while not client.connect():
        sleep(0.5)

def task(unit):
    surround = grab_surroundings(unit, Broodwar, 1024, 1024)
    surround = reduce(surround, 16)
    return surround
        
def run_episode():
    
        
if __name__ == '__main__':
    #ENEMY_TYPE = cybw.UnitTypes.Protoss_Zealot
    ENEMY_TYPE = cybw.UnitTypes.Zerg_Zergling
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='The port which the server should connect to.',
                        type=int)
    args = parser.parse_args()
    with TwoWayClient(host='localhost', port=args.port) as s:
        print("Connecting...")
        reconnect()
        wins = 0
        total_games = 0
        games = count(1)
        #games = tqdm(games)
        #games.set_description('Gathering data...')
        for game_no in games:
            while not Broodwar.isInGame():
                client.update()
                if not client.isConnected():
                    print("Reconnecting...")
                    reconnect()
            Broodwar.setLocalSpeed(0)
            #Broodwar.setGUI(False)
            Broodwar.setFrameSkip(0)

            frame = 0
            K = 10
            previous_actions = None
            if Broodwar.isInGame():
                AllUnits = Broodwar.getAllUnits()
                ###
                # Helper Functions
                ###
                health = lambda x: x.getHitPoints() + x.getShields() if x.exists() else 0
                isMarine = lambda x: x.exists() and x.getType() == cybw.UnitTypes.Terran_Marine
                isZealot = lambda x: x.exists() and x.getType() == ENEMY_TYPE
                ###
                
                zealots = [e for e in Broodwar.enemy().getUnits() if isZealot(e)]
                beginning_EnemyHealth = sum((health(e) for e in zealots))
                agents = [t for t in Broodwar.self().getUnits() if isMarine(t)]
                beginning_AllyHealth = sum((health(t) for t in agents))
                
                MarineMaxHealth = max((health(t) for t in agents))
                previous_AllyHealth = beginning_AllyHealth
                previous_EnemyHealth = beginning_EnemyHealth
            while Broodwar.isInGame():
                terminal = len([e for e in Broodwar.getEvents() if cybw.EventType.MatchEnd == e.getType()]) == 1
                AllUnits = Broodwar.getAllUnits()
                EnemyHealth = sum((health(e) for e in zealots))
                AllyHealth = sum((health(t) for t in agents if isMarine(t)))
                if EnemyHealth == 0 or frame >= 2**10 or AllyHealth == 0:
                    terminal = True
                if frame%K == 0:
                    observations = []
                    rewards = []
                    for i, unit in enumerate(agents):
                        surround = grab_surroundings(unit, Broodwar, 1024, 1024)
                        surround = reduce(surround, 16)
                        observations.append(surround)
                                                
                        reward =  (previous_EnemyHealth - EnemyHealth) - (previous_AllyHealth - AllyHealth)
                        rewards.append(reward)
                        
                    data = {'observations': observations, 'rewards': rewards 'Terminal': terminal}
                    pick = pickle.dumps(data)
                    s.send(pick)
                    actions = pickle.loads(s.read())
                    previous_actions = actions
                else:
                    actions = previous_actions

                for i, unit in enumerate(agents):
                    if unit.exists():
                        ##################################################################
                        # Detects surroundings of the unit
                        ##################################################################
                        action = actions[i, :]
                        #drawGrid(Broodwar, unit, width=256, height=256, rows=4, columns=4, color=cybw.Colors.Blue)
                        #drawRectangleOnUnit(Broodwar, unit, width=1024, height=1024, color=cybw.Colors.Yellow)
                        P = unit.getPosition()
                        Broodwar.setScreenPosition(cybw.Position(P.x-250, P.y-250))
                        X = P.x - 256/2
                        Y = P.y - 256/2
                        if np.argmax(action) == 16:
                            pass
                        else:
                            X = X + 64*((np.argmax(action))%4)+32
                            Y = Y + 64*(int((np.argmax(action))/4))+32
                            Position = cybw.Position(X, Y)
                            if frame%K == 0:
                                unit.attack(Position)
                            #Broodwar.drawCircleMap(Position, 10, cybw.Colors.Red)
                        '''elif np.argmax(action) < 16:
                            X = X + 64*(np.argmax(action)%4)+32
                            Y = Y + 64*(int(np.argmax(action)/4))+32
                            Position = cybw.Position(X, Y)
                            if frame%K == 0:
                                unit.move(Position)
                            Broodwar.drawCircleMap(Position, 10, cybw.Colors.Green)'''


                if terminal == True:
                    observations = []
                    AllyHealth = []
                    for i, unit in enumerate(agents):
                        surround = grab_surroundings(unit, Broodwar, 1024, 1024)
                        surround = reduce(surround, 16)
                        observations.append(surround)
                        AllyHealth.append(health(unit)/MarineMaxHealth)
                    data = {'observations': observations, 'EnemyHealth': EnemyHealth/beginning_EnemyHealth,
                            'AllyHealth': AllyHealth, 'Terminal': terminal}
                    pick = pickle.dumps(data)
                    s.send(pick)
                    actions = pickle.loads(s.read())
                    previous_actions = actions
                    frame = 0
                    terminal = False
                    if game_no%5 == 0:
                        Broodwar.leaveGame()
                    else:
                        Broodwar.restartGame()
                    previous_AllyHealth = beginning_AllyHealth
                    previous_EnemyHealth = beginning_EnemyHealth
                else:
                    frame = (frame+1)
                    previous_AllyHealth = AllyHealth
                    previous_EnemyHealth = EnemyHealth
                Broodwar.drawTextScreen(cybw.Position(300, 0), "FPS: " +
                    str(Broodwar.getAverageFPS()))
                client.update()
                #games.set_description('Game: {!s} | E: {!s} A: {!s}'.format(game_no, EnemyHealth/beginning_EnemyHealth,
                #                                                           sum((health(t) for t in agents if isMarine(t)))/beginning_AllyHealth))
            #subprocess.run(["echo", 'Win Rate: {!s}% Out of: {!s}'.format(100*wins/total_games, total_games)])
