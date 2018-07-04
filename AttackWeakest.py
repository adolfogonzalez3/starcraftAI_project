import cybw
from time import sleep
import subprocess

client = cybw.BWAPIClient
Broodwar = cybw.Broodwar

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

print("Connecting...")
reconnect()
var1 = 0
wins = 0
total_games = 0
while True:
    print("TEST1" + str(var1))
    var1 += 1
    print("waiting to enter match")
    while not Broodwar.isInGame():
        client.update()
        if not client.isConnected():
            print("Reconnecting...")
            reconnect()
    print("starting match!")
    Broodwar.setLocalSpeed(1)
    Broodwar.setGUI(False)
    Broodwar.setFrameSkip(10);
    Broodwar.sendText( "Hello world from python!")
    Broodwar.printf( "Hello world from python!")

    # need newline to flush buffer
    Broodwar << "The map is " << Broodwar.mapName() << ", a " \
        << len(Broodwar.getStartLocations()) << " player map" << " \n"

    # Enable some cheat flags
    Broodwar.enableFlag(cybw.Flag.UserInput)

    Broodwar.enableFlag(cybw.Flag.CompleteMapInformation)

    show_bullets = False
    show_visibility_data = False
    previous_actions = [None]*5
    while Broodwar.isInGame():
        units    = Broodwar.self().getUnits()
        minerals  = Broodwar.getMinerals()
        for i, unit in enumerate(units):
            if unit.getType() == cybw.UnitTypes.Terran_Marine:# and unit.isIdle():
                leastHealth = None
                enemy = Broodwar.getAllUnits()
                enemy = [e for e in enemy if e.getPlayer().getID() != Broodwar.self().getID()]
                for e in Broodwar.enemy().getUnits():
                    if e.exists() is False:
                        continue
                    if leastHealth is None:
                        leastHealth = e
                    elif leastHealth.getHitPoints() > e.getHitPoints():
                        leastHealth = e
                if leastHealth is not None:
                    if previous_actions[i] is None:
                        unit.attack(leastHealth)
                        previous_actions[i] = leastHealth
                    elif previous_actions[i].getID() == leastHealth.getID() and unit.isIdle():
                        unit.attack(leastHealth)
                    elif previous_actions[i].getID() != leastHealth.getID():
                        unit.attack(leastHealth)
                        previous_actions[i] = leastHealth
                    unit.attack(leastHealth, True)
        events = Broodwar.getEvents()
        for e in events:
            eventtype = e.getType()
            if eventtype == cybw.EventType.MatchEnd:
                if e.isWinner():
                    Broodwar << "I won the game\n"
                    wins += 1
                else:
                    Broodwar << "I lost the game\n"
                total_games += 1
            elif eventtype == cybw.EventType.SendText:
                if e.getText() == "/show bullets":
                    show_bullets = not show_bullets
                elif e.getText() == "/show players":
                    showPlayers()
                elif e.getText() == "/show forces":
                    showForces()
                elif e.getText() == "/show visibility":
                    show_visibility_data = not show_visibility_data
                else:
                    Broodwar << "You typed \"" << e.getText() << "\"!\n"
            elif eventtype == cybw.EventType.ReceiveText:
                Broodwar << e.getPlayer().getName() << " said \"" << e.getText() << "\"\n"
            elif eventtype == cybw.EventType.PlayerLeft:
                Broodwar << e.getPlayer().getName() << " left the game.\n"
            elif eventtype == cybw.EventType.NukeDetect:
                if e.getPosition() is not cybw.Positions.Unknown:
                    Broodwar.drawCircleMap(e.getPosition(), 40,
                        cybw.Colors.Red, True)
                    Broodwar << "Nuclear Launch Detected at " << e.getPosition() << "\n"
                else:
                    Broodwar << "Nuclear Launch Detected.\n"
            elif eventtype == cybw.EventType.UnitCreate:
                if not Broodwar.isReplay():
                    Broodwar << "A " << e.getUnit() << " has been created at " << e.getUnit().getPosition() << "\n"
                else:
                    if(e.getUnit().getType().isBuilding() and
                      (e.getUnit().getPlayer().isNeutral() == False)):
                        seconds = Broodwar.getFrameCount()/24
                        minutes = seconds/60
                        seconds %= 60
                        Broodwar.sendText(str(minutes)+":"+str(seconds)+": "+e.getUnit().getPlayer().getName()+" creates a "+str(e.getUnit().getType())+"\n")
            elif eventtype == cybw.EventType.UnitDestroy:
                if not Broodwar.isReplay():
                    Broodwar << "A " << e.getUnit() << " has been destroyed at " << e.getUnit().getPosition() << "\n"
            elif eventtype == cybw.EventType.UnitMorph:
                if not Broodwar.isReplay():
                    Broodwar << "A " << e.getUnit() << " has been morphed at " << e.getUnit().getPosition() << "\n"
                else:
                    # if we are in a replay, then we will print out the build order
                    # (just of the buildings, not the units).
                    if e.getUnit().getType().isBuilding() and not e.getUnit().getPlayer().isNeutral():
                        seconds = Broodwar.getFrameCount()/24
                        minutes = seconds/60
                        seconds %= 60
                        Broodwar << str(minutes) << ":" << str(seconds) << ": " << e.getUnit().getPlayer().getName() << " morphs a " << e.getUnit().getType() << "\n"
            elif eventtype == cybw.EventType.UnitShow:
                if not Broodwar.isReplay():
                    Broodwar << e.getUnit() << " spotted at " << e.getUnit().getPosition() << "\n"
            elif eventtype == cybw.EventType.UnitHide:
                if not Broodwar.isReplay():
                    Broodwar << e.getUnit() << " was last seen at " << e.getUnit().getPosition() << "\n"
            elif eventtype == cybw.EventType.UnitRenegade:
                if not Broodwar.isReplay():
                    Broodwar << e.getUnit() << " is now owned by " << e.getUnit().getPlayer() << "\n"
            elif eventtype == cybw.EventType.SaveGame:
                Broodwar << "The game was saved to " << e.getText() << "\n"
        if show_bullets:
            drawBullets()
        if show_visibility_data:
            drawVisibilityData()
        drawStats()
        Broodwar.drawTextScreen(cybw.Position(300, 0), "FPS: " +
            str(Broodwar.getAverageFPS()))
        client.update()
    subprocess.run(["echo", 'Win Rate: {!s} Out of: {!s}'.format(100*wins/total_games, total_games)])
