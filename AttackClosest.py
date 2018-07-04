"""
This module handles the script AI for causing Terran Marines to attack the closest enemies.

Requirements:
python version 3.5 (32-bit)

"""

import cybw
from PIL import Image
from time import sleep
import subprocess
import numpy as np
import pylab as pl
import pickle

client = cybw.BWAPIClient
Broodwar = cybw.Broodwar

def grab_surroundings(unit, Broodwar, width=320, height=320):
    surroundings = Broodwar.getAllUnits()
    surroundings = [s for s in surroundings if unit.getDistance(s) < 140]
    position = unit.getPosition()
    surround = np.zeros((width, height))
    surround[int(width/2), int(height/2)] = 255
    for s in surroundings:
        if s.getID() != unit.getID():
            S = s.getPosition()
            x = S.x - position.x + int(width/2)
            y = S.y - position.y + int(height/2)
            if s.getPlayer().getID() == Broodwar.self().getID():
                surround[x, y] = 255 #2
            else:
                surround[x, y] = 255 #3
                e_pos = s.getPosition()
    return surround

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

def showPlayers():
    players = Broodwar.getPlayers()
    for player in players:
        Broodwar << "Player [" << player.getID() << "]: " << player.getName(
            ) << " is in force: " << player.getForce().getName() << "\n"

def showForces():
    forces = Broodwar.getForces()
    for force in forces:
        players = force.getPlayers()
        Broodwar << "Force " << force.getName() << " has the following players:\n"
        for player in players:
            Broodwar << "  - Player [" << player.getID() << "]: " << player.getName() << "\n"

def drawStats():
    line = 0
    allUnitTypes = cybw.UnitTypes.allUnitTypes()
    Broodwar.drawTextScreen(cybw.Position(5, 0), "I have " +
        str(Broodwar.self().allUnitCount())+" units:")
    for unitType in allUnitTypes:
        count = Broodwar.self().allUnitCount(unitType)
        if count > 0:
            line += 1
            statStr = "- "+str(count)+" "+str(unitType)
            Broodwar.drawTextScreen(cybw.Position(5, 12*line), statStr)

def drawBullets():
    bullets = Broodwar.getBullets()
    for bullet in bullets:
        p = bullet.getPosition()
        velocityX = bullet.getVelocityX()
        velocityY = bullet.getVelocityY()
        lineColor = cybw.Colors.Red
        textColor = cybw.Text.Red
        if bullet.getPlayer == Broodwar.self():
            lineColor = cybw.Colors.Green
            textColor = cybw.Text.Green
        Broodwar.drawLineMap(p, p+cybw.Position(velocityX, velocityY), lineColor)
        Broodwar.drawTextMap(p, chr(textColor) + str(bullet.getType()))

def drawVisibilityData():
    wid = Broodwar.mapWidth()
    hgt = Broodwar.mapHeight()
    for x in range(wid):
        for y in range(hgt):
            drawColor = cybw.Colors.Red
            if Broodwar.isExplored(tileX=x, tileY=y):
                if Broodwar.isVisible(tileX=x, tileY=y):
                    drawColor = cybw.Colors.Green
                else:
                    drawColor = cybw.Colors.Blue

            Broodwar.drawDotMap(cybw.Position(x*32+16, y*32+16), drawColor)

def drawRectangleOnUnit(Broodwar, unit, width=20, height=20, color=cybw.Colors.Blue):
    half_width = int(width/2)
    half_height = int(height/2)
    position = unit.getPosition()
    Broodwar.drawBoxMap(cybw.Position(position.x-half_width, position.y-half_height),
                        cybw.Position(position.x+half_width, position.y+half_height), color)

print("Connecting...")
reconnect()
wins = 0
total_games = 0
while True:
    while not Broodwar.isInGame():
        client.update()
        if not client.isConnected():
            print("Reconnecting...")
            reconnect()
    print("starting match!")
    Broodwar.setLocalSpeed(1)
    #Broodwar.setGUI(False)
    Broodwar.setFrameSkip(10);

    show_bullets = False
    show_visibility_data = False
    frame = 0
    previous_actions = [None]*5
    img = None
    while Broodwar.isInGame():

        units    = Broodwar.self().getUnits()
        #minerals  = Broodwar.getMinerals()
        agent_frames = []
        for i, unit in enumerate(units):
            if unit.getType() == cybw.UnitTypes.Terran_Marine:# and unit.isIdle():
                ##################################################################
                # Detects surroundings of the unit
                ##################################################################

                surround = grab_surroundings(unit, Broodwar)
                mark_surrounding_units(unit, Broodwar)
                im = Image.fromarray(surround)
                pick = pickle.dumps(surround)
                if frame%25 == 0:
                    if img is None:
                        img = pl.imshow(im)
                    else:
                        img.set_data(im)
                    pl.pause(.01)
                    pl.draw()
                ##################################################################
                # Gives the unit an action.
                ##################################################################
                #prediction = models[0].predict(surround.reshape((1,320,320,1)))
                #subprocess.run(["echo", 'Prediction: {!s}'.format(prediction)])
                enemy = Broodwar.getAllUnits()
                enemy = [e for e in enemy if e.getPlayer().getID() != Broodwar.self().getID()]
                closest = None
                for e in enemy:
                    if closest is None:
                        closest = e
                    elif unit.getDistance(closest) > unit.getDistance(e):
                        closest = e
                if closest is not None:
                    if previous_actions[i] is None:
                        unit.attack(closest)
                        previous_actions[i] = closest
                    elif previous_actions[i].getID() == closest.getID() and unit.isIdle():
                        unit.attack(closest)
                    elif previous_actions[i].getID() != closest.getID():
                        unit.attack(closest)
                        previous_actions[i] = closest


        events = Broodwar.getEvents()
        #drawBullets()
        frame = (frame+1)%25
        for e in events:
            eventtype = e.getType()
            if eventtype == cybw.EventType.MatchEnd:
                if e.isWinner():
                    Broodwar << "I won the game\n"
                    wins += 1
                else:
                    Broodwar << "I lost the game\n"
                total_games += 1
        Broodwar.drawTextScreen(cybw.Position(300, 0), "FPS: " +
            str(Broodwar.getAverageFPS()))
        client.update()
    subprocess.run(["echo", 'Win Rate: {!s}% Out of: {!s}'.format(100*wins/total_games, total_games)])
