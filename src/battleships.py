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
"""

#Import required modules
import platform # To get current system
import os #For file handling
import pickle #For saving game maps to disk
import hmac, hashlib #To sign pickle files to prevent remote code execution
import sys #To exit the program
import shutil #To get terminal size
import threading, itertools, time #For the spinner
import urllib.request #To download the help files
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

        print(message)
        if(platform.system() == 'Windows'):
            msvcrt.getch() #BUG: If run in idle this is non blocking. See: https://bugs.python.org/issue9290
        elif(platform.system() == 'Darwin' or platform.system() == 'Linux'):
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

        #BUG: This doesn't work in idle
        if(platform.system() == 'Windows'):
            os.system('cls')
        elif(platform.system() == 'Darwin' or platform.system() == 'Linux'):
            os.system('clear')
        else:
            print('\n'*100)
        return

class Spinner:
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

class PositionAlreadyPopulated(Error):
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
    addShip(size, posX, posY)
        Adds a ship of size `size` starting at `posX` `posY`
    printBoard()
        Prints the game board
    printBoardHidden()
        Prints the gameboard but hides all except hits and misses
    """

    def __init__(self, x: int = 10, y: int = 10) -> None:
        """
        Returns
        -------
        None
        """

        self.map = None
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

        self.map: list = [[0 for i in range(x)] for j in range(y)]
        return

    def addShip(self, size: int, posX: int, posY: int, rotDir: bool = False) -> None:
        """Adds a ship of specified size to board starting at specified coordinates

        Parameters
        ----------
        size : int
            The size of the ship.
        posX : int
            The x coordinate for the start of the ship
        posY : int
            The y coordinate for the start of the ship
        rotDir : bool, optional
            The direction of the ship. True is vertical. False is horizontal.
            (default False)

        Raises
        ------
        PositionAlreadyPopulated
            If position for ship is already taken.
        
        Returns
        -------
        None
        """

        return

    def printBoard(self) -> None:
        """Prints the game board
        
        Outputs the game board with X and Y headers

        Returns
        -------
        None
        """

        # Print x heading
        print(f"\n\n|{' ':^3}|", end='')
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

        # Print x heading
        print(f"\n\n|{' ':^3}|", end='')
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

    def __init__(self) -> None:
        self.score = 0
        return

    def showScores(self) -> None:
        """Prints a list of the top 10 scores
        
        Reads the contents of scores.json and then sorts by highest
        before printing it to screen.

        Returns
        -------
        None
        """

        return   
        
class GameSave():
    """This class handles the saving and loading of game files

    Methods
    -------
    listSave()
        return a list of all saved games
    outSave()
        print a list of all saved games
    """

    def __init__(self) -> None: #TODO: Add gamesave features
        """      
        Returns
        -------
        None
        """

        self.saveKey:bytes = bytes('6P5OajyXaEURcLI0URJb', 'ascii') #Key for testing HMAC. Should be stored more securely
        return

    def listSave(self, saveLocation) -> list:
        """Get a list of all saved games

        Returns
        -------
        list
            a list of all saved games
        """

        self.savedGames:list = []
        for file in os.listdir(os.path.join(saveLocation, 'saved_games')):
            if file.endswith(".pkl"):
                self.savedGames.append(file)
        return self.savedGames

    def saveGame(self, board:list, saveLocation:str) -> None:
        """Saves the current gameboard
        
        Pickles provided gameboard and then signs data using HMAC before 
        saving to file

        Parameters
        ----------
        board : list
            The game map in list form
        saveLocation:
            The path to the battleships directory

        Returns
        -------
        None
        """

        self.name = input('Please enter a name for this game: ')
        self.pickledData = pickle.dumps(board)
        self.digest = hmac.new(self.saveKey, self.pickledData, hashlib.sha256).hexdigest()
        with open(os.path.join(saveLocation, 'saved_games', f'{self.name}.sha256'), 'w') as data:
            data.write(self.digest)
            data.close()
        with open(os.path.join(saveLocation, 'saved_games', f'{self.name}.pkl'), 'wb') as data:
            data.write(self.pickledData)
            data.close()
        return

    def loadGame(self, saveLocation) -> list:
        """Loads a game file

        Loads the relevant game files before verifying the pickled
        data's signature to verify it hasn't been modified

        Parameters
        ----------
        saveLocation : str
            The path to the battleships directory

        Returns
        -------
        None
        """

        while True:
            self.fileName = input('Please enter the name of the game you wish to load or input \'view\' to view all saved games: ')
            if (self.fileName == 'view'):
                self.outSave()
            else:
                break
        if(os.path.exists(os.path.join(saveLocation, 'saved_games', f'{self.fileName}.pkl')) and os.path.exists(os.path.join(saveLocation, 'saved_games', f'{self.fileName}.sha256'))):
            with open(os.path.join(saveLocation, 'saved_games', f'{self.fileName}.sha256'), 'r') as data:
                self.recvdDigest = data.read()
                data.close()
            with open(os.path.join(saveLocation, 'saved_games', f'{self.fileName}.pkl'), 'rb') as data:
                self.pickledData = data.read()
                data.close()
            self.newDigest = hmac.new(self.saveKey, self.pickledData, hashlib.sha256).hexdigest()
            if (self.recvdDigest != self.newDigest):
                print('Integrity check failed. Game files have been modified.')
                return
            else:
                return pickle.loads(self.pickledData)
        else:
            print('Failed to load game files')
            return

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

    def __init__(self, saveLocation:str) -> None:
        self.saveLocation:str = saveLocation
        self.scoreKeep = Scoring()
        self.savedGames = GameSave()
        self.gameboard = Board()
        self.mainMenu()
    def mainMenu(self) -> None:
        """Show the main menu"""
        self.choiceMap = {
            1: self.play,
            2: self.createNew,
            3: self.loadGame,
            4: self.showSave,
            5: self.scoreKeep.showScores,
            6: self.settings,
            7: self.showHelp,
            8: self.quit
        }
        while True:
            print('Welcome to Battle Ships\nPlease choose an option:')
            self.choice:int = 0
            print('[1] Play\n[2] Start A New Game\n[3] Load a saved game\n[4] View saved games\n[5] View Scores\n[6] Settings\n[7] Help and troubleshooting\n[8] Quit')
            while self.choice not in range(1,9):
                try:
                    self.choice = int(input('Please choose an option [1-8]: '))
                except ValueError:
                    pass
            Helpers.clearScreen()
            self.choiceMap[self.choice]()
        
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
            self.createNew()
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
        self.gameboard.generateBoard(self.width, self.height)
        print('Game created')
        Helpers.anyKey()
        Helpers.clearScreen()
        return

    def loadGame(self) -> None:
        """Load a game file from disk
        
        Loads specified game from disk.

        Returns
        -------
        None
        """

        self.gameMap = self.savedGames.loadGame(self.saveLocation)
        if (self.gameMap == None):
            print('Failed to load game files')
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

    def settings(self) -> None: #TODO: Add ability to adjust settings
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
        if(os.path.exists(os.path.join(self.saveLocation, 'help.txt')) == False):
            with Spinner('Downloading help files'):
                time.sleep(0.1)
                urllib.request.urlretrieve('https://raw.githubusercontent.com/Computroniks/python-battleships/main/assets/help.txt', os.path.join(self.saveLocation, 'help.txt'))
                time.sleep(0.1)
                print('\nDone')
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
            print(self.helpContent[i])
            if(i == self.rows-2):
                self.rows += self.oldRows
                Helpers.anyKey('--MORE--')
        
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

if __name__ == '__main__':
    if('idlelib.run' in sys.modules):
        print('Warning. This code should not be run in IDLE. Some features will not work\nas intended. Please run this code in the terminal or \ncommand line.')
        choice = input('Are you sure you want to continue? [y/N]: ').lower().replace(' ', '')
        if (choice == 'y'):
            pass
        else:
            sys.exit()
    Helpers.clearScreen()
    #Establish what platform we are on to get correct file location
    if(platform.system() == 'Windows'):
        saveLocation = os.path.expandvars("%LOCALAPPDATA%/battleships")
    elif(platform.system() == 'Darwin'):
        saveLocation = os.path.expanduser('~/Library/battleships')
    elif(platform.system() == 'Linux'):
        saveLocation = os.path.expanduser('~/.battleships')
    else:
        saveLocation = './'
    #Check if directory exists and if not create it
    if(os.path.exists(saveLocation) == False):
        try:
            os.mkdir(saveLocation)
        except OSError:
            sys.exit(f"Creation of directory {saveLocation} failed.\n Please create this directory manually and try again.")
    #Check if directory exists and if not create it
    if(os.path.exists(os.path.join(saveLocation, 'saved_games')) == False):
        try:
            os.mkdir(os.path.join(saveLocation, 'saved_games'))
        except OSError:
            sys.exit(f"Creation of directory {os.path.join(saveLocation, 'saved_games')} failed.\n Please create this directory manually and try again.")
    #Check if file exists and if not create it
    if(os.path.exists(os.path.join(saveLocation, 'score.json')) == False):
        try:
            f = open(os.path.join(saveLocation, 'score.json'), 'w')
            f.write('{}')
            f.close()
        except OSError:
            sys.exit(f"Creation of directory {os.path.join(saveLocation, 'score.json')} failed.\n Please create this directory manually and try again.")
    
    app = Game(saveLocation)