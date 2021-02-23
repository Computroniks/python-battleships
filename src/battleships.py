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
    """Base class for other exceptions"""
    
    pass
class PositionAlreadyPopulated(Error):
    """Raised when position is already populated
    
    This error is raised when a ship is trying to be placed in
    a position which is already populated by another ship.

    Attributes
    ----------
    """

    pass
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
    def addShip(self, size:int=5, posX:int=0, posY:int=0) -> bool:
        """Adds a ship of specified size to board starting at specified coordinates

        Parameters
        ----------
        size
        """

        pass
    def printBoard(self) -> None:
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
#Main game loop
if __name__ == '__main__':
    gameBoard = Board(10,10)
    gameBoard.printBoard()
    gameBoard.printBoardHidden()
    
