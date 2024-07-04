from __future__ import annotations
import random
import numpy as np
from blessed import Terminal
from collections import namedtuple
from typing import Optional, List

Position = namedtuple(typename='Position', field_names=['x', 'y'])
Size = namedtuple(typename='Size', field_names=['width', 'height'])


class Cell:
    def __init__(self, minefield: Minefield, position: Position, plant_mine: bool = False) -> None:
        self.minefield = minefield
        self.position = position
        self.is_mine = plant_mine
        self.symbol = '#'
        self.is_flagged = False
        self.is_revealed = False

    def reveal(self) -> None:
        if self.is_revealed:
            return
        self.is_revealed = True
        if self.is_mine:
            self.symbol = '*'
        else:
            self.symbol = '.'

    def flag(self) -> None:
        if not self.is_revealed:
            if self.symbol == '#':
                self.symbol = 'F'
            elif self.symbol == 'F':
                self.symbol = '#'

    def __str__(self) -> str:
        return self.symbol


class Minefield:
    def __init__(self, top_left: Position, size: Size, num_mines: int) -> None:
        self.top_left = top_left
        self.size = size
        self.num_mines = num_mines
        self.cells = np.empty(shape=(self.size.width, self.size.height), dtype=object)

        mine_positions = self._place_mines()

        for x in range(self.size.width):
            for y in range(self.size.height):
                cell_position = Position(x=x, y=y)
                plant_mine = cell_position in mine_positions
                self.cells[x, y] = Cell(self, cell_position, plant_mine)

    def _place_mines(self) -> List[Position]:
        mine_positions = []
        while len(mine_positions) < self.num_mines:
            new_mine_position = Position(
                x=random.randint(0, self.size.width - 1),
                y=random.randint(0, self.size.height - 1)
            )
            if new_mine_position not in mine_positions:
                mine_positions.append(new_mine_position)
        return mine_positions

    def reveal(self, position: Position) -> None:
        cell = self.cells[position.x, position.y]
        cell.reveal()

    def reveal_all(self) -> None:
        for x in range(self.size.width):
            for y in range(self.size.height):
                cell = self.cells[x, y]
                cell.reveal()

    def flag(self, position: Position) -> None:
        self.cells[position.x, position.y].flag()

    def all_cells_revealed_except_mines(self) -> bool:
        for x in range(self.size.width):
            for y in range(self.size.height):
                cell = self.cells[x, y]
                if not cell.is_revealed and not cell.is_mine:
                    return False
        return True

    def __str__(self) -> str:
        return '\n'.join(''.join(str(self.cells[x, y]) for x in range(self.size.width)) for y in range(self.size.height))


class Minesweeper:
    def __init__(self, minefield: Minefield) -> None:
        self.minefield = minefield
        self.game_over = False
        self.victory = False

    def reveal_cell(self, position: Position) -> None:
        if not self.game_over and not self.victory:
            self.minefield.reveal(position)
            if self.minefield.cells[position.x, position.y].is_mine:
                self.game_over = True
            elif self.minefield.all_cells_revealed_except_mines():
                self.victory = True

    def flag_cell(self, position: Position) -> None:
        if not self.game_over and not self.victory:
            self.minefield.flag(position)

    def is_game_over(self) -> bool:
        return self.game_over

    def is_victory(self) -> bool:
        return self.victory

    def __str__(self) -> str:
        return str(self.minefield)


class Action:
    def __init__(self, name: str, target: Position) -> None:
        self.name = name
        self.target = target


class InputHandler:
    def __init__(self, term, minefield) -> None:
        self.term = term
        self.current_position = minefield.top_left
        self.minefield = minefield

        self.movement_keys = [
            self.term.KEY_UP, self.term.KEY_DOWN, self.term.KEY_LEFT, self.term.KEY_RIGHT
        ]

    def get_input(self) -> Optional[Action]:
        key = self.term.inkey(timeout=None)

        if key.code == self.term.KEY_ENTER:
            return Action(name='reveal', target=self.current_position)
        elif key.lower() == 'f':
            return Action(name='flag', target=self.current_position)
        elif key.code in self.movement_keys:
            if key.code == self.term.KEY_UP:
                self.current_position = Position(self.current_position.x, max(0, self.current_position.y - 1))
            elif key.code == self.term.KEY_DOWN:
                self.current_position = Position(self.current_position.x, min(self.minefield.size.height - 1, self.current_position.y + 1))
            elif key.code == self.term.KEY_LEFT:
                self.current_position = Position(max(0, self.current_position.x - 1), self.current_position.y)
            elif key.code == self.term.KEY_RIGHT:
                self.current_position = Position(min(self.minefield.size.width - 1, self.current_position.x + 1), self.current_position.y)
            return Action(name='move', target=self.current_position)

        return None


def main() -> None:
    term = Terminal()
    print(term.clear)

    size = Size(width=10, height=10)
    num_mines = 15

    minefield = Minefield(Position(0, 0), size, num_mines)
    minesweeper = Minesweeper(minefield)
    input_handler = InputHandler(term, minefield)

    with term.cbreak(), term.hidden_cursor():
        while not minesweeper.is_game_over() and not minesweeper.is_victory():
            with term.location(minesweeper.minefield.top_left.x, minesweeper.minefield.top_left.y):
                print(minesweeper)
            with term.location(input_handler.current_position.x, input_handler.current_position.y):
                print('X')
            action = input_handler.get_input()

            if action:
                if action.name == 'reveal':
                    minesweeper.reveal_cell(action.target)
                elif action.name == 'flag':
                    minesweeper.flag_cell(action.target)
                elif action.name == 'move':
                    # Optionally handle cursor movement feedback in the UI
                    pass

        if minesweeper.is_game_over():
            with term.location(minesweeper.minefield.top_left.x, minesweeper.minefield.top_left.y):
                minesweeper.minefield.reveal_all()
                print(minesweeper)
            with term.location(
                    minesweeper.minefield.top_left.x + minesweeper.minefield.size.width,
                    minesweeper.minefield.top_left.y + minesweeper.minefield.size.height
            ):
                print(term.red + "Game Over! You revealed a mine.")
        elif minesweeper.is_victory():
            with term.location(
                    minesweeper.minefield.top_left.x + minesweeper.minefield.size.width,
                    minesweeper.minefield.top_left.y + minesweeper.minefield.size.height
            ):
                print(term.green + "Congratulations! You cleared the minefield.")

    with term.cbreak(), term.hidden_cursor():
        inp = term.inkey()

    print(term.home + term.clear)


if __name__ == '__main__':
    main()
