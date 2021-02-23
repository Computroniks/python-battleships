"""
Copyright (c) 2021 Matthew Nickson, All rights reserved
You may use, distribute and modify this code under the
terms of the MIT license which can be found in the 
project root.
You should have received a copy of the MIT license with
this file. If not, please visit : 
https://raw.githubusercontent.com/Computroniks/python-battleships/main/LICENSE
"""

#Define custom exceptions
class Error(Exception):
    """Base class for other exceptions
    
    This is the base class on which all custom errors are based.

    Attributes
    ----------
    message : str, optional
        An explanation of the error
    """
    
    def __init__(self, message:str="An unexpected error occured") -> None:
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

    def __init__(self, message:str="This position is already populated") -> None:
        self.message:str = message
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

    def __init__(self, x:int=10, y:int=10) -> None:
        """
        Parameters
        ----------
        x : int, optional
            The width of the game board (default is 10)
        y : int, optional
            The height of the game board (default is 10)
        """

        self.map:list = [[0 for i in range(x)] for j in range(y)]
    
    def addShip(self, size:int, posX:int, posY:int, rotDir:bool=False) -> None:
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
        #Print x heading
        print(f"\n\n|{' ':^3}|", end='')
        for i in range(len(self.map[0])):
            print(f'{i+1:^3}|', end='')
        #Print rows with y heading
        for i in range(len(self.map)):
            print(f'\n|{i+1:^3}|', end='')
            for j in range(len(self.map[i])):
                print(f'{self.map[i][j]:^3}|', end='')


    def printBoardHidden(self) -> None:
        """Prints the game board

        This function prints out the gameboard but all items except for hits and 
        misses are redacted.
        """

        #Print x heading
        print(f"\n\n|{' ':^3}|", end='')
        for i in range(len(self.map[0])):
            print(f'{i+1:^3}|', end='')
        #Print rows with y heading
        for i in range(len(self.map)):
            print(f'\n|{i+1:^3}|', end='')
            for j in range(len(self.map[i])):
                if (self.map[i][j] == 'H' or self.map[i][j] == 'M'):
                    print(f'{self.map[i][j]:^3}|', end='')
                else:
                    print(f"{'#':^3}|", end='')


class Game():
    """This class handles the gameplay and controls all aspects of the game

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
    def __init__(self):
        while True:
            try:
                self.width:int = int(input('Please enter the board width: '))
                if (self.width < 1):
                    print('The minimum board width is 1')
                    continue
                elif (int(str(abs(self.width))) > 3):
                    print('The maximum board width is 999')
                    continue
                else:
                    break
            except ValueError:
                print('Please enter a valid number!')
        while True:
            try:
                self.height:int = int(input('Please enter the board height: '))
                if (self.height < 1):
                    print('The minimum board height is 1')
                    continue
                elif (int(str(abs(self.height))) > 3):
                    print('The maximum board height is 999')
                    continue
                else:
                    break
            except ValueError:
                print('Please enter a valid number!')
        self.gameboard = Board(self.width, self.height)
#Main game loop
if __name__ == '__main__':
    gameBoard = Board(10,10)
    gameBoard.printBoard()
    gameBoard.printBoardHidden()
    
