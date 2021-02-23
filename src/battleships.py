"""
Copyright (c) 2021 Matthew Nickson, All rights reserved
You may use, distribute and modify this code under the
terms of the MIT license which can be found in the 
project root.
You should have received a copy of the MIT license with
this file. If not, please visit : 
https://raw.githubusercontent.com/Computroniks/python-battleships/main/LICENSE
"""

#Import required modules
import platform # To get current system
import os #For file handling
import pickle #For saving game maps to disk
import hmac, hashlib #To sign pickle files to prevent remote code execution
import sys #To exit the program

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
        self.message = message
        super().__init__(self.message)

class PositionAlreadyPopulated(Error):
    """Raised when position is already populated

    This error is raised when a ship is trying to be placed in
    a position which is already populated by another ship.
sss
    Attributes
    ----------
    message : str, optional
        An explanation of the error
    """

    def __init__(self, message: str = "This position is already populated") -> None:
        self.message: str = message
        super().__init__(self.message)


class Board():
    """A class that handles anything to do with the game board

    Attributes
    ----------
    map : list
        a 2d list that is the game board

    Methods
    -------
    addShip(size, posX, posY)
        Adds a ship of size `size` starting at `posX` `posY`
    printBoard()
        Prints the game board
    printBoardHidden()
        Prints the gameboard but hides all except hits and misses
    """

    def __init__(self, x: int = 10, y: int = 10) -> None:
        """
        Parameters
        ----------
        x : int, optional
            The width of the game board (default is 10)
        y : int, optional
            The height of the game board (default is 10)
        """

        self.generateBoard(x, y)

    def generateBoard(self, x:int = 10, y:int = 10) -> None:
        """
        Parameters
        ----------
        x : int, optional
            The width of the game board (default is 10)
        y : int, optional
            The height of the game board (default is 10)
        """

        self.map: list = [[0 for i in range(x)] for j in range(y)]
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
        """

        pass

    def printBoard(self) -> None:
        """Prints the game board

        This function prints out the gameboard with all items seen
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

    def printBoardHidden(self) -> None:
        """Prints the game board

        This function prints out the gameboard but all items except for hits and 
        misses are redacted.
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
    def showScores(self) -> None:
        """Prints a list of the top 10 scores"""
        pass   
        
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
        self.saveKey:bytes = bytes('6P5OajyXaEURcLI0URJb', 'ascii') #Key for testing HMAC. Should be stored more securely
    def listSave(self) -> list:
        """Get a list of all saved games

        Returns
        -------
        list
            a list of all saved games
        """
        pass
    def outSave(self) -> None:
        """Print a list of saved games"""
        print('Saved games')
    def saveGame(self, board:list, saveLocation) -> None:
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
    startNew()
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
            1: self.startNew,
            2: self.loadGame,
            3: self.savedGames.outSave,
            4: self.scoreKeep.showScores,
            5: self.settings,
            6: self.showHelp,
            7: self.quit
        }
        print('Welcome to Battle Ships\nPlease choose an option:')
        while True:
            self.choice:int = 0
            print('[1] Start A New Game\n[2] Load a saved game\n[3] View saved games\n[4] View Scores\n[5] Settings\n[6] Help and troubleshooting\n[7] Quit')
            while self.choice not in range(1,8):
                try:
                    self.choice = int(input('Please choose an option [1-7]: '))
                except ValueError:
                    pass
            self.choiceMap[self.choice]()
        
        
    def startNew(self) -> None:
        """Create a new game"""
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
        self.savedGames.saveGame(self.gameboard.map, self.saveLocation)
        return
    def loadGame(self) -> None:
        """Load a game file from disk"""
        self.gameMap = self.savedGames.loadGame(self.saveLocation)
        if (self.gameMap == None):
            print('Failed to load game files')
            return
        else:
            self.gameboard.map = self.gameMap
            print('Loaded game files')#TODO: call play game or return to main menu
    def settings(self) -> None: #TODO: Add ability to adjust settings
        """Show the settings dialog"""
        pass
    def showHelp(self) -> None: #TODO: Add help text
        """Output the help text"""
        print('Help')
    def quit(self) -> None: 
        """Confirm and exit the program"""
        while True:
            self.quitC:str = input('Are you sure you want to quit? [y/N]').lower().replace(' ', '')
            if (self.quitC == 'y'):
                print('Bye')
                sys.exit()
            else:
                return

if __name__ == '__main__':
    #Establish what platform we are on to get correct file location
    if(platform.system() == 'Windows'):
        saveLocation = os.path.expandvars("%LOCALAPPDATA%/battleships")
    elif(platform.system() == 'Darwin'):
        saveLocation = '~/Library/battleships'
    elif(platform.system() == 'Linux'):
        saveLocation = '~/.battleships'
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