"""
Copyright (c) 2021 Matthew Nickson, All rights reserved
You may use, distribute and modify this code under the
terms of the MIT license which can be found in the 
project root.
You should have received a copy of the MIT license with
this file. If not, please write to :
mnickson@sidingsmedia.com
or visit: 
https://raw.githubusercontent.com/Computroniks/python-battleships/main/LICENSE

Python Battleships
------------------
A one sided game of battleships that was written for a 
school project.
"""

#Import required modules
import platform # To get current system
import os #For file handling
import pickle #For saving game maps to disk
import hmac, hashlib #To sign pickle files to prevent remote code execution
import sys #To exit the program
import shutil #To get terminal size
import threading, itertools, time #For the spinner
import urllib.request, distutils.version #To download the help files
import json #For reading score and settings files
import string #To verify filenames
import random #To generate board
from multiprocessing import Process #To timeout placing ships
#Import platform specific module for 'press any key' prompt
if(platform.system() == 'Windows'):
    import msvcrt
elif(platform.system() == 'Darwin' or platform.system() == 'Linux'):
    import termios
else:
    sys.exit('This software only works on Windows or Unix operating systems')

class Helpers():
    """Class to hold all related helper functions

    Methods
    -------
    anykey()
        This function blocks the main thread until any key
        is pressed
    clearScreen()
        This function runs the platform specific command to clear
        the terminal window
    """
    def anyKey(message:str = 'Press any key to continue...') -> None:
        """Waits for any key to be pressed
        
        Blocks the main thread until a key is pressed

        Parameters
        ----------
        message : str, optional
            The message that is displayed at the prompt.

        Returns
        -------
        None
        """

        if ('idlelib.run' in sys.modules):
            input('Press enter to continue...')
        elif(platform.system() == 'Windows'):
            print(message, end='\r')
            msvcrt.getch() #BUG: If run in idle this is non blocking. See: https://bugs.python.org/issue9290
        elif(platform.system() == 'Darwin' or platform.system() == 'Linux'):
            print(message, end='\r')
            fd = sys.stdin.fileno()
            oldterm = termios.tcgetattr(fd)
            newattr = termios.tcgetattr(fd)
            newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
            termios.tcsetattr(fd, termios.TCSANOW, newattr)
            try:
                result = sys.stdin.read(1)
            except IOError:
                pass
            finally:
                termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        else:
            sys.exit('This software only works on Windows or Unix operating systems')

    def clearScreen() -> None:
        """Clears the current console window
        
        Runs the correct system command to clear the current
        console window. Note this will not work in IDLE as it
        runs system commands.

        Returns
        -------
        None
        """

        if ('idlelib.run' in sys.modules):
            for i in range(3): #Avoid idle squeezing the text
                print('\n'*49)
        elif(platform.system() == 'Windows'):
            os.system('cls')
        elif(platform.system() == 'Darwin' or platform.system() == 'Linux'):
            os.system('clear')
        else:
            print('\n'*100)
        return
    def formatFileName(unsafeFileName:str) -> str:
        """Take a string and return a valid filename constructed from the string.

        Uses a whitelist approach: any characters not present in validC hars are
        removed.  

        Parameters
        ----------
        unsafeFileName : string
            This is the user input to be sanitized and formated

        Returns
        -------
        string
            The sanitized and formated file name
        """

        validChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        safeFileName = ''.join(c for c in unsafeFileName if c in validChars)
        safeFileName = safeFileName.replace(' ','_') # I don't like spaces in filenames.
        return safeFileName
#End class Helpers()

class Spinner():
    """This class handles the spinning icon

    The little nice looking spinning icon at the end of the download message
    is controlled by this class.

    Methods
    -------
    writeNext(message, delay)
        Writes the next spinner icon to the screen
    removeSpinner(cleanup)
        Removes the spinner
    spinnerTask()
        The main controler for the spinner
    """

    def __init__(self, message:str, delay:float=0.1) -> None:
        """
        Parameters
        ----------
        message : str
            The message to be displayed before the spinner
        delay : float, optional
            The delay in s between each step of the spinners cycle (default = 0.1)
        
        Returns
        -------
        None
        """

        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.delay = delay
        self.busy = False
        self.spinnerVisible = False
        sys.stdout.write(message)
        return

    def writeNext(self) -> None:
        """Writes the next step of spinner
        
        Writes the next step of the spinners cycle to the screen

        Returns
        -------
        None
        """

        with self._screen_lock:
            if not self.spinnerVisible:
                sys.stdout.write(next(self.spinner))
                self.spinnerVisible = True
                sys.stdout.flush()
        return

    def removeSpinner(self, cleanup:bool=False) -> None:
        """Removes the spinner
        
        Removes the spinner from the screen

        Parameters
        ----------
        cleanup : bool
            Whether to cleanup the spinner
        """

        with self._screen_lock:
            if self.spinnerVisible:
                sys.stdout.write('\b')
                self.spinnerVisible = False
                if cleanup:
                    sys.stdout.write(' ')       # overwrite spinner with blank
                    sys.stdout.write('\r')      # move to next line
                sys.stdout.flush()
        return

    def spinnerTask(self) -> None:
        """Controls the spinner
        
        This method controls the function of the spinner and increments
        it's position
        
        Returns
        -------
        None
        """

        while self.busy:
            self.writeNext()
            time.sleep(self.delay)
            self.removeSpinner()
        return

    def __enter__(self) -> None:
        if sys.stdout.isatty():
            self._screen_lock = threading.Lock()
            self.busy = True
            self.thread = threading.Thread(target=self.spinnerTask)
            self.thread.start()
        return

    def __exit__(self, exception, value, tb) -> None:
        if sys.stdout.isatty():
            self.busy = False
            self.removeSpinner(cleanup=True)
        else:
            sys.stdout.write('\r')
        return
#End class Spinner()

# Define custom exceptions
class Error(Exception):
    """Base class for other exceptions

    This is the base class on which all custom errors are based.

    Attributes
    ----------
    message : str, optional
        An explanation of the error
    """

    def __init__(self, message: str = "An unexpected error occured") -> None:
        """
        Calls parent class with specified message to print out 
        error to screen

        Returns
        -------
        None
        """

        self.message = message
        super().__init__(self.message)
        return None
#End class Error()

class PositionAlreadyPopulatedError(Error):
    """Raised when position is already populated

    This error is raised when a ship is trying to be placed in
    a position which is already populated by another ship.

    Attributes
    ----------
    message : str, optional
        An explanation of the error
    """

    def __init__(self, message: str = "This position is already populated") -> None:
        """
        Calls parent class with specified message to print out
        error to screen

        Returns
        -------
        None
        """

        self.message: str = message
        super().__init__(self.message)
        return
#End class PositionAlreadyPopulatedError()

class OutOfBoundsError(Error):
    """Raised when position out of bounds

    This error is raised when a ship is trying to be placed in
    a position which is not within the bounds of the game board

    Attributes
    ----------
    message : str, optional
        An explanation of the error
    """

    def __init__(self, message: str = "This position is out of bounds") -> None:
        """
        Calls parent class with specified message to print out
        error to screen

        Returns
        -------
        None
        """

        self.message: str = message
        super().__init__(self.message)
        return
#End class OutOfBoundsError()

class Settings():
    """This class handles all settings files
    
    Anything to do with settings is dealt by this class. This includes
    saveLocation.

    Attributes
    ----------
    self.saveLocation : str
        This is the file path for the save location
    self.settingsData : dict
        This is the contents of settings.json

    Methods
    -------
    """

    def __init__(self) -> None:
        """
        Establishes current system to generate correct file path before
        checking that correct directories and files exist and creating
        them if they don't

        Returns
        -------
        None
        """
        
        #Establish what platform we are on to get correct file location
        if(platform.system() == 'Windows'):
            self.saveLocation = os.path.expandvars("%LOCALAPPDATA%/battleships")
        elif(platform.system() == 'Darwin'):
            self.saveLocation = os.path.expanduser('~/Library/battleships')
        elif(platform.system() == 'Linux'):
            self.saveLocation = os.path.expanduser('~/.battleships')
        else:
            self.saveLocation = './'

        #Directories and files to create
        self.dirs = [
            'saved_games'
        ]
        self.files = [
            'score.json',
            'settings.json',
            'scores.json',
            'saved_games/saves.json'
        ]
        if(os.path.exists(self.saveLocation) == False):
            try:
                os.mkdir(self.saveLocation)
            except OSError:
                sys.exit(f"Creation of directory {self.saveLocation} failed.\n Please create this directory manually and try again.")
        #Iterate through dirs and create missing
        for i in self.dirs:
            if (os.path.exists(os.path.join(self.saveLocation, i)) == False):
                try:
                    os.mkdir(os.path.join(self.saveLocation, i))
                except OSError:
                    sys.exit(f"Creation of directory {os.path.join(self.saveLocation, i)} failed.\n Please create this directory manually and try again.")
        #Iterate through files and create missing
        for i in self.files:
            if (os.path.exists(os.path.join(self.saveLocation, i)) == False):
                try:
                    f = open(os.path.join(self.saveLocation, i), 'w')
                    f.write('{}')
                    f.close()
                except OSError:
                    sys.exit(f"Creation of file {os.path.join(self.saveLocation, i)} failed.\n Please create this file manually and try again.")
        #Load settings.json
        with open(os.path.join(self.saveLocation, 'settings.json'), 'r') as data:
            self.settingsData = json.load(data)
        return

    def changeSetting(self, setting:str, value) -> None:
        """Changes the setting and writes change to disk

        Takes the settings to change and value to change it to
        and changes it in the dictionary before writing the 
        changes to disk.

        Parameters
        ----------
        setting : str
            The setting that is to be changed
        value
            The value that the setting should be changed to

        Returns
        -------
        None
        """

        self.settingsData[setting] = value
        with open(os.path.join(self.saveLocation, 'settings.json'), 'w') as data:
            json.dump(self.settingsData, data)
        return
#End class Settings()

class Board():
    """A class that handles anything to do with the game board

    Attributes
    ----------
    map : list
        a 2d list that is the game board

    Methods
    -------
    generateBoard(x, y)
        Generates a board of size `x` `y`
    addShip(size, posX, posY, rotDir, maxX, maxY, symbol)
        Adds a ship of size `size` starting at `posX` `posY`
    addRandom(x, y)
        Adds all the required ships in random positions on the board
    printBoard()
        Prints the game board
    printBoardHidden()
        Prints the gameboard but hides all except hits and misses
    engage(posX, posY)
        Engages at a specific position
    won()
        Checks if all ships have been destroyed
    """

    def __init__(self) -> None:
        """
        Returns
        -------
        None
        """
        self.hits: list[tuple[int, int]] = []
        self.map = None
        self.ships = {
            'A':{
                'name':'Aircraft Carrier',
                'size':5,
                'hits':0
            },
            'B':{
                'name':'Battleship',
                'size':4,
                'hits':0
            },
            'C':{
                'name':'Cruiser',
                'size':3,
                'hits':0
            }, 
            'S':{
                'name':'Submarine',
                'size':3,
                'hits':0
            },
            'D':{
                'name':'Destroyer',
                'size':2,
                'hits':0
            },
        }
        return

    def generateBoard(self, x:int = 10, y:int = 10) -> None:
        """Creates a board

        Creates a board of size `x` `y` and set self.map to
        the generated board

        Parameters
        ----------
        x : int, optional
            The width of the game board (default is 10)
        y : int, optional
            The height of the game board (default is 10)
        
        Returns
        -------
        None
        """

        self.currentShips = dict(self.ships) #Don't use dict.copy() as it is shallow so doesn't account for nested items
        self.sunkShips:list[str] = []
        self.hits:list = []
        self.hitShip:list = []
        self.map: list = [[0 for i in range(x)] for j in range(y)]
        return

    def addShip(self, size: int, posX: int, posY: int, rotDir: bool, maxX: int, maxY: int, symbol: str) -> None:
        """Adds a ship of specified size to board starting at specified coordinates

        Parameters
        ----------
        size : int
            The size of the ship.
        posX : int
            The x coordinate for the start of the ship
        posY : int
            The y coordinate for the start of the ship
        rotDir : bool
            The direction of the ship. True is vertical. False is horizontal.
        maxX : int
            The width of the board
        maxY : int
            The height of the board
        symbol : string
            The symbol to be placed on the board

        Raises
        ------
        PositionAlreadyPopulatedError
            If position for ship is already taken.
        OutOfBoundsError
            If the position for the ship is not within the confines of the 
            game board.
        
        Returns
        -------
        None
        """

        #Check that way is clear for ship
        if rotDir:
            #Two seperate for loops to avoid only half placing ships
            for i in range(posY, posY+size):
                try:
                    if self.map[i][posX] != 0:
                        raise PositionAlreadyPopulatedError
                        return
                except IndexError:
                    raise OutOfBoundsError
                    return
            for i in range(posY, posY+size):
                self.map[i][posX] = symbol
        else:
            for i in range(posX, posX+size):
                try:
                    if self.map[posY][i] != 0:
                        raise PositionAlreadyPopulatedError
                        return
                except IndexError:
                    raise OutOfBoundsError
                    return
            for i in range(posX, posX+size):
                self.map[posY][i] = symbol
        return

    def addRandom(self, x:int, y:int) -> None: #BUG: Can hang if board is too small
        for key in self.ships:
            while True:
                self.startPos = (random.randint(0,x), random.randint(0, y))
                self.rotDirection = bool(random.getrandbits(1))
                try:
                    self.addShip(self.ships[key]['size'], self.startPos[0], self.startPos[1], self.rotDirection, x, y, key)
                    break
                except (PositionAlreadyPopulatedError, OutOfBoundsError):
                    continue
            

    def printBoard(self) -> None:
        """Prints the game board
        
        Outputs the game board with X and Y headers

        Returns
        -------
        None
        """

        # Print x heading
        print(f"|{' ':^3}|", end='')
        for i in range(len(self.map[0])):
            print(f'{i+1:^3}|', end='')
        # Print rows with y heading
        for i in range(len(self.map)):
            print(f'\n|{i+1:^3}|', end='')
            for j in range(len(self.map[i])):
                print(f'{self.map[i][j]:^3}|', end='')
        return

    def printBoardHidden(self) -> None:
        """Prints the game board

        This function prints out the gameboard but all items except for hits and 
        misses are redacted.
        
        Returns
        -------
        None
        """
        #temporary for debugging. remove for production
        # self.printBoard()
        # return
        # Print x heading
        print(f"|{' ':^3}|", end='')
        for i in range(len(self.map[0])):
            print(f'{i+1:^3}|', end='')
        # Print rows with y heading
        for i in range(len(self.map)):
            print(f'\n|{i+1:^3}|', end='')
            for j in range(len(self.map[i])):
                if (self.map[i][j] == 'H' or self.map[i][j] == 'M'):
                    print(f'{self.map[i][j]:^3}|', end='')
                else:
                    print(f"{'#':^3}|", end='')
        return
    def engage(self, posX: int, posY: int) -> str:
        """Engages a ship at specified position

        Engages the position specified. This checks if the position has 
        aleady been engaged and if not engages the position. It then 
        returns the result of that engagement as a string.

        Parameters
        ----------
        posX : int
            The x coordinate to engage
        posY : int
            The y coordinate to engage 
        
        Returns
        -------
        string
            The type of ship that has been hit
        """

        posX -= 1 #Account for list starting at 0 but board starting at 1
        posY -= 1
        if (posX, posY) in self.hits:
            print('You have already engaged this position!')
            return 'AE'
        else:
            self.hits.append((posX, posY))
            self.hitShip = self.map[posY][posX]
            if self.hitShip == 0:
                self.map[posY][posX] = 'M'
                return 'miss'
            else:
                self.map[posY][posX] = 'H'
                self.currentShips[self.hitShip]['hits'] += 1
                return self.hitShip

    def isSunk(self, ship:str) -> bool:
        """Checks if ship has been sunk 

        Checks if the specified ship has been sunk and returns it 
        as a boolean value.

        Parameters
        ----------
        ship : string
            The ship to check
        
        Returns
        -------
        boolean
            If the specified ship has been sunk or not
        """

        if self.currentShips[ship]['size'] == self.currentShips[ship]['hits']:
            self.sunkShips.append(ship)
            return True
        else:
            return False
    def won(self) -> bool:
        """Checks if all ships have been sunk 

        Checks if all the ships on the board have been sunk and 
        returns the status it as a boolean value.
        
        Returns
        -------
        boolean
            If all of the ships on the board have been sunk
        """

        if len(self.sunkShips) >= 5:
            return True
        else:
            return False
#End class Board()
     
class Scoring():
    """This class handles the scoring and saving of scores

    Attributes
    ----------
    score : int
        The current users score

    Methods
    -------
    showScores()
        print a list of top 10 scores
    """

    def __init__(self, saveLocation:str) -> None:
        self.score = 0
        with open(os.path.join(saveLocation, 'scores.json'), 'r') as data:
            self.scoresSave = json.load(data)
        return

    def getScores(self, ordered:bool = False) -> dict:
        if ordered:
            return {k: v for k, v in sorted(self.scoresSave.items(), key=lambda item: item[1])}
        else:
            return self.scoresSave

    def showScores(self) -> None:
        """Prints a list of the top 10 scores
        
        Reads the contents of scores.json and then sorts by highest
        before printing it to screen.

        Returns
        -------
        None
        """
        self.tempScore = dict(itertools.islice(self.getScores(True).items(), 10))
        i = 0
        print('Scores:')
        for key in self.tempScore:
            i +=1
            print(f'[{i}] {key}: {self.scoresSave[key]}')
        Helpers.anyKey()

        return   

    def addScore(self, name:str, saveLocation:str, force:bool = False) -> dict:
        """Adds a score to scores file
        
        Adds a score to the scores file with the users name as 
        the key. If force is not set then it checks to see if 
        it is going to overwrite an existing score. It returns 
        a dict that contains the return status and if error an
        error code .

        Parameters
        -----------
        name : string
            The name to write the score under
        saveLocation : string
            The path to the current save location
        force : bool, optional
            Bypass overwriting check (default false)

        Returns
        -------
        dict : {'status':bool, 'errCd':str}
            A simple success or fail indicator. If fail returns 
            status false and the appropriate error code. If 
            success returns status true and appropriate error
            code. 
            Error Codes
            -----------
            ok
                Success
            ovrwrt
                This action will overwrite a pre-existing entry
        """

        if force:
            pass
        else:
            if name in self.scoresSave:
                return {'status':False, 'errCd':'ovrwrt'}
        self.scoresSave[name] = self.score
        with open(os.path.join(saveLocation, 'scores.json'), 'w') as data:
            json.dump(self.scoresSave, data)
        return {'status':True, 'errCd':'ok'}        
#End class Scoring()
        
class GameSave():
    """This class handles the saving and loading of game files

    Methods
    -------
    listSave()
        return a list of all saved games
    saveGame()
        Saves the current game to disk
    loadGame()
        Loads a game from disk
    deleteGame()
        Deletes a game from disk
    """

    def __init__(self, saveLocation:str) -> None: #TODO: Add gamesave features
        """

        Parameters
        ----------
        saveLocation : string
            The path to the current save location
            
        Returns
        -------
        None
        """
        with open(os.path.join(saveLocation, 'saved_games/saves.json'), 'r') as data:
            self.savesFile = json.load(data)
        self.saveKey:bytes = bytes('6P5OajyXaEURcLI0URJb', 'ascii') #Key for testing HMAC. Should be stored more securely
        return

    def listSave(self, saveLocation:str) -> list:
        """Get a list of all saved games

        Parameters
        ----------
        saveLocation : string
            The path to the battleships directory

        Returns
        -------
        list
            a list of all saved games
        """

        self.savedGames:list = []
        for key in self.savesFile:
            self.savedGames.append(key)
        return self.savedGames

    def saveGame(self, board:list, saveLocation:str, score:int) -> None:
        """Saves the current gameboard
        
        Pickles provided gameboard and then signs data using HMAC before 
        saving to file

        Parameters
        ----------
        board : list
            The game map in list form
        saveLocation : string
            The path to the battleships directory
        score : int
            The current game score

        Returns
        -------
        None
        """

        self.name = input('Please enter a name for this game: ')
        self.pickledData = pickle.dumps(board)
        self.digest = hmac.new(self.saveKey, self.pickledData, hashlib.sha256).hexdigest()
        self.savesFile[self.name] = {'fileName': Helpers.formatFileName(self.name), 'score':score, 'hash':self.digest}
        with open(os.path.join(saveLocation, 'saved_games', f'{Helpers.formatFileName(self.name)}.pkl'), 'wb') as data:
            data.write(self.pickledData)
            data.close()
        with open(os.path.join(saveLocation, 'saved_games/saves.json'), 'w') as data:
            json.dump(self.savesFile, data)
        return

    def loadGame(self, saveLocation:str) -> tuple:
        """Loads a game file

        Loads the relevant game files before verifying the pickled
        data's signature to verify it hasn't been modified

        Parameters
        ----------
        saveLocation : str
            The path to the battleships directory

        Returns
        -------
        list
            The game map loaded from file
        int
            The score loaded from json file
        """

        while True:
            self.fileName = input('Please enter the name of the game you wish to load or input \'view\' to view all saved games: ')
            if (self.fileName == 'view'):
                self.saves:list = self.listSave(saveLocation)
                print('Saved Games:')
                for i in range(len(self.saves)):
                    print(f'[{i+1}] {self.saves[i]}')
            else:
                break
        if (self.fileName in self.savesFile):
            self.recvdDigest = self.savesFile[self.fileName]['hash']
            with open(os.path.join(saveLocation, 'saved_games', f'{Helpers.formatFileName(self.fileName)}.pkl'), 'rb') as data:
                self.pickledData = data.read()
                data.close()
            self.newDigest = hmac.new(self.saveKey, self.pickledData, hashlib.sha256).hexdigest()
            if (self.recvdDigest != self.newDigest):
                print('Integrity check failed. Game files have been modified.')
                return None, 0
            else:
                return pickle.loads(self.pickledData), self.savesFile[self.fileName]['score']
        else:
            print('Failed to load game files')
            return None, 0

    def deleteGame(self, saveLocation:str) -> bool:
        """Deletes a game file from disk

        Parameters
        ----------
        saveLocation : string
            The path to the current save location

        Returns
        -------
        bool
            Success or fail of deletion
        """

        while True:
            self.fileName = input('Please enter the name of the game you wish to delete or input \'view\' to view all saved games: ')
            if (self.fileName == 'view'):
                self.saves:list = self.listSave(saveLocation)
                print('Saved Games:')
                for i in range(len(self.saves)):
                    print(f'[{i+1}] {self.saves[i]}')
            else:
                break
        if(input(f'Are you sure you want to delete {self.fileName}? [y/N]: ').replace(' ', '').lower() == 'y'):
            self.temp = self.savesFile.pop(self.fileName, None)
            with open(os.path.join(saveLocation, 'saved_games/saves.json'), 'w') as data:
                json.dump(self.savesFile, data)
            if (self.temp is not None):
                if(os.path.exists(os.path.join(saveLocation, 'saved_games', f'{self.fileName}.pkl'))):
                    try:
                        os.remove(os.path.join(saveLocation, 'saved_games', f'{self.fileName}.pkl'))
                        return True
                    except OSError:
                        return False
                else:
                    return False
            else:
                return False
#End class GameSave()

class Game():
    """This class handles the gameplay and controls all aspects of the game

    Methods
    -------
    mainMenu()
        shows the main menu
    play()
        The main game loop
    createNew()
        Generates a new game
    loadGame()
        loads a game from file
    settings()
        open the settings menu
    showHelp()
        show the help prompt
    quit()
        exit the program
    
    """

    def __init__(self) -> None:
        self.settings = Settings()
        self.saveLocation:str = self.settings.saveLocation
        self.scoreKeep = Scoring(self.saveLocation)
        self.savedGames = GameSave(self.saveLocation)
        self.gameboard = Board()
        self.mainMenu()
    def mainMenu(self) -> None:
        """Show the main menu"""
        self.choiceMap = {
            1: self.play,
            2: self.createNew,
            3: self.loadGame,
            4: self.deleteSave,
            5: self.showSave,
            6: self.scoreKeep.showScores,
            7: self.settingsOptions,
            8: self.showHelp,
            9: self.quit
        }
        while True:
            print('Welcome to Battle Ships\nPlease choose an option:')
            self.choice:int = 0
            print('[1] Play\n[2] Start A New Game\n[3] Load a saved game\n[4] Delete a saved game\n[5] View saved games\n[6] View Scores\n[7] Settings\n[8] Help and troubleshooting\n[9] Quit')
            while self.choice not in range(1,10):
                try:
                    self.choice = int(input('Please choose an option [1-9]: '))
                except ValueError:
                    pass
            Helpers.clearScreen()
            self.choiceMap[self.choice]()
            Helpers.clearScreen()
        
    def play(self) -> None:
        """The main game loop
        
        This is the main game loop for battleships. This is where
        all of the main game logic is.

        Returns
        -------
        None
        """

        #If no game loaded create new one
        if(self.gameboard.map == None):
            if self.createNew():
                pass
            else:
                return
        #Get gameboard height and width
        self.xy = [len(self.gameboard.map[0]), len(self.gameboard.map)]
        print('To exit press CTRL + C at any time')
        #Game loop
        while True:
            if self.gameboard.won():
                print('All of the enemies ships have been destroyed. You win!')
                print(f'Your score is {self.scoreKeep.score}')
                if input('Would you like to save your score? [y/N]: ').lower().replace(' ', '') == 'y':
                    self.name = input('Please enter your name: ')
                    self.saveResponse = self.scoreKeep.addScore(self.name, self.saveLocation)
                    if self.saveResponse['status']:
                        print('Score saved successfully')
                    elif self.saveResponse['status'] == False and self.saveResponse['errCd'] == 'ovrwrt':
                        if input('You are about to overwrite an existing entry! Are you sure you want to proceed? [y/N]: ').lower().replace(' ', '') == 'y':
                            self.scoreKeep.addScore(self.name, self.saveLocation, True)
                        else:
                            pass
                else:
                    pass
                Helpers.anyKey()
                Helpers.clearScreen()
                break
            try:
                print(f'Current score: {self.scoreKeep.score}')
                self.gameboard.printBoardHidden()
                print('')
                #Get coordinates to engage
                self.error = False
                while True:
                    self.coordinates:list = input('Please enter the X and Y coordinates you wish to engage seperated by a comma: ').replace(' ', '').split(',')
                    if (not (len(self.coordinates) == 2)):
                        self.error = True
                    for i in range(len(self.coordinates)):
                        try:
                            self.coordinates[i] = int(self.coordinates[i])
                        except ValueError:
                            self.error = True
                        if (not (self.coordinates[i] in range(self.xy[i]+1))):
                            self.error = True
                    if (self.error):
                        self.error = False
                        print('Invalid coordinates')
                        continue
                    else:
                        break
                self.engageResult = self.gameboard.engage(self.coordinates[0], self.coordinates[1])
                if self.engageResult is not None:
                    if self.engageResult == 'miss':
                        print('Miss')
                        self.scoreKeep.score -= 1
                    elif self.engageResult == 'AE':
                        pass
                    else:
                        if self.gameboard.isSunk(self.engageResult):
                            print(f'You sunk a {self.gameboard.ships[self.engageResult]["name"]}')
                        else:
                            print(f'You hit a {self.gameboard.ships[self.engageResult]["name"]}')

            except KeyboardInterrupt:
                Helpers.clearScreen()
                print('[1] Save and exit\n[2] Exit without saving\n[3] Return to game')
                while True:
                    try:
                        self.choice = int(input('Please enter an option [1-3]: '))
                        break
                    except ValueError:
                        pass
                if (self.choice == 1):
                    self.savedGames.saveGame(self.gameboard.map, self.settings.saveLocation, self.scoreKeep.score)
                    print('Game saved')
                    Helpers.anyKey()
                    return
                elif (self.choice == 2):
                    if (input('Are you sure? [y/N]: ').replace(' ', '').lower() == 'y'):
                        return
                else:
                    pass
            time.sleep(2)
            Helpers.clearScreen()
        return
        
    def createNew(self) -> None:
        """Create a new game
        
        Creates a new game board acording to the users specifications

        Returns
        -------
        None
        """

        while True:
            try:
                self.width: int = int(input('Please enter the board width: '))
                if (self.width < 1):
                    print('The minimum board width is 1')
                    continue
                elif (len(str(abs(self.width))) > 3):
                    print('The maximum board width is 999')
                    continue
                else:
                    break
            except ValueError:
                print('Please enter a valid number!')
        while True:
            try:
                self.height: int = int(
                    input('Please enter the board height: '))
                if (self.height < 1):
                    print('The minimum board height is 1')
                    continue
                elif (len(str(abs(self.height))) > 3):
                    print('The maximum board height is 999')
                    continue
                else:
                    break
            except ValueError:
                print('Please enter a valid number!')
        with Spinner('Placing Ships'):
            self.error = False
            self.gameboard.generateBoard(self.width, self.height)
            #Timeout for placing ships
            self.placeShipsTmOt = Process(target=self.gameboard.addRandom, args=[self.width, self.height])
            self.placeShipsTmOt.start()
            self.placeShipsTmOt.join(timeout=10)
            self.placeShipsTmOt.terminate()
            if self.placeShipsTmOt.exitcode is None:
                self.gameboard.map = None
                self.error = True
            self.scoreKeep.score = self.width + self.height
        if self.error:
            print('Failed to place ships.\nTry making the board larger.')
            self.error = False
            Helpers.anyKey()
            Helpers.clearScreen()
            return False
        else:
            print('\nGame created')
            Helpers.anyKey()
            Helpers.clearScreen()
            return True

    def loadGame(self) -> None:
        """Load a game file from disk
        
        Loads specified game from disk.

        Returns
        -------
        None
        """

        self.gameMap, self.scoreKeep.score = self.savedGames.loadGame(self.saveLocation)
        if (self.gameMap == None):
            pass
        else:
            self.gameboard.map = self.gameMap
            print('Loaded game files')
        Helpers.anyKey()
        Helpers.clearScreen()
        return
    
    def showSave(self) -> None:
        """Prints a list of saved games
        
        Prints a list of all games in `saveLocation/saved_games`

        Returns
        -------
        None
        """

        self.saves:list = self.savedGames.listSave(self.saveLocation)
        print('Saved Games:')
        for i in range(len(self.saves)):
            print(f'[{i+1}] {self.saves[i]}')#FIXME: outputs file exension
        Helpers.anyKey()
        Helpers.clearScreen()
        return
    def deleteSave(self) -> None:
        if(self.savedGames.deleteGame(self.saveLocation)):
            print('Game deleted')
        else:
            print('Failed to delete game')
        Helpers.anyKey()
        Helpers.clearScreen()

    def settingsOptions(self) -> None: #TODO: Add ability to adjust settings
        """Show the settings dialog
        
        Opens the settings dialog with with options to set `saveLocation`

        Returns
        -------
        None
        """

        pass
    def showHelp(self) -> None: #TODO: Add help text
        """Output the help text
        
        Downloads help file if not already downloaded and then displays it
        page by page.

        Returns
        -------
        None
        """
        self.error = False
        try:
            self.response = urllib.request.urlopen('https://raw.githubusercontent.com/Computroniks/python-battleships/main/assets/HELPVER')
            self.newHelpVer = self.response.read().decode('utf-8')
        except urllib.error.URLError:
            self.newHelpVer = '1.0.0'
        if ('helpVer' in self.settings.settingsData):
            self.currentHelpVer = self.settings.settingsData['helpVer']
        else:
            self.currentHelpVer = '1.0.0'
        if(os.path.exists(os.path.join(self.saveLocation, 'help.txt')) == False) or (distutils.version.LooseVersion(self.newHelpVer) > distutils.version.LooseVersion(self.currentHelpVer)):
            self.settings.changeSetting('helpVer', self.newHelpVer)
            with Spinner('Downloading help files'):
                try:
                    time.sleep(0.1)
                    urllib.request.urlretrieve('https://raw.githubusercontent.com/Computroniks/python-battleships/main/assets/help.txt', os.path.join(self.saveLocation, 'help.txt'))
                    time.sleep(0.1)
                    print('\nDone')
                except urllib.error.URLError:
                     self.error = True
        if (self.error):
            print('\nFailed to download help files. Please make sure you are connected to the internet.')
            Helpers.anyKey()
            Helpers.clearScreen()
            return
        print('Help and troubleshooting')
        print('To continue to the next page press any key.')
        Helpers.anyKey()
        Helpers.clearScreen()
        with open(os.path.join(self.saveLocation, 'help.txt')) as rfile:
            self.helpContent = rfile.readlines()
            rfile.close()
        self.columns, self.rows = shutil.get_terminal_size()
        self.oldRows = self.rows
        for i in range(len(self.helpContent)):
            print(self.helpContent[i], end=(''))
            if(i == self.rows):
                self.rows += self.oldRows
                Helpers.anyKey('--MORE--')
                print(' '*15, end='\r')#Make sure that --MORE-- is removed even if line is blank space
        print()
        Helpers.anyKey('--END--')
        Helpers.clearScreen()
        return

    def quit(self) -> None: 
        """Confirm and exit the program
        
        Asks user if they really want to quit. Default it no.

        Returns
        -------
        None
        """

        while True:
            self.quitC:str = input('Are you sure you want to quit? [y/N]').lower().replace(' ', '')
            if (self.quitC == 'y'):
                print('Bye')
                sys.exit()
            else:
                Helpers.clearScreen()
                return
#End class Game()

if __name__ == '__main__':
    Helpers.clearScreen()
    app = Game()
