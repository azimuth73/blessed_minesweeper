from __future__ import annotations
import random
import numpy as np
from blessed import Terminal, keyboard
from collections import namedtuple
from typing import Optional, List

Position = namedtuple(typename='Position', field_names=['x', 'y'])
Size = namedtuple(typename='Size', field_names=['width', 'height'])

SYMBOLS = {
    'UNREVEALED': '%',
    'EMPTY': ' ',
    'MINE': '*',
    'FLAGGED': 'X',
}


class Cell:
    def __init__(self, minefield: Minefield, position: Position, plant_mine: bool = False) -> None:
        self.minefield = minefield
        self.position = position
        self.is_mine = plant_mine
        self.is_flagged = False
        self.is_revealed = False
        self.clicked_auto_reveal = False
        self.symbol = SYMBOLS['UNREVEALED']

    def neighbours(self) -> List[Cell]:
        neighbours = []
        directions = [(-1, -1), (-1, +0), (-1, +1), (+0, -1), (+0, +1), (+1, -1), (+1, +0), (+1, +1)]
        for dx, dy in directions:
            nx, ny = self.position.x + dx, self.position.y + dy
            if 0 <= nx < self.minefield.size.width and 0 <= ny < self.minefield.size.height:
                neighbours.append(self.minefield.cells[nx, ny])
        return neighbours

    def reveal(self, visited=None) -> None:
        # There is still some weird behaviour i cannot explain where its unpredictable where neigbours neighbours
        # will auto discover nearby
        if visited is None:
            visited = set()

        if self.is_flagged:
            return

        visited.add(self)

        if self.is_revealed:

            # Check if the number of flagged neighbors matches the cell's number
            mine_count = sum(neighbour.is_mine for neighbour in self.neighbours())
            flagged_count = sum(neighbour.is_flagged for neighbour in self.neighbours())
            if mine_count == flagged_count and not self.clicked_auto_reveal:
                self.clicked_auto_reveal = True
                for neighbour in self.neighbours():
                    if not neighbour.is_flagged and neighbour not in visited:
                        neighbour.reveal()
            return

        self.is_revealed = True
        if self.is_mine:
            self.symbol = SYMBOLS['MINE']
        else:
            mine_count = sum(neighbour.is_mine for neighbour in self.neighbours())
            self.symbol = str(mine_count) if mine_count > 0 else SYMBOLS['EMPTY']
            if mine_count == 0:
                for neighbour in self.neighbours():
                    if neighbour not in visited:
                        neighbour.reveal()

    def flag(self) -> None:
        if not self.is_revealed:
            if self.is_flagged:
                self.is_flagged = False
                self.symbol = SYMBOLS['UNREVEALED']
            else:
                self.is_flagged = True
                self.symbol = SYMBOLS['FLAGGED']

    def __str__(self) -> str:
        return self.symbol


class Minefield:
    def __init__(self, top_left: Position, size: Size, num_mines: int) -> None:
        self.top_left = top_left
        self.size = size
        self.num_mines = num_mines
        self.cells = np.empty(shape=(self.size.width, self.size.height), dtype=object)
        self.cursor_position = self.top_left

        mine_positions = self.__place_mines()

        for x in range(self.size.width):
            for y in range(self.size.height):
                cell_position = Position(x=x, y=y)
                plant_mine = cell_position in mine_positions
                self.cells[x, y] = Cell(self, cell_position, plant_mine)

    def move_cursor(self, dx: int = 0, dy: int = 0) -> None:

        new_x, new_y = self.cursor_position.x + dx, self.cursor_position.y + dy
        min_x, min_y, max_x, max_y = 0, 0, self.size.width - 1, self.size.height - 1

        if new_x > max_x:
            new_x = max_x
        elif new_x < min_x:
            new_x = min_x
        if new_y > max_y:
            new_y = max_y
        elif new_y < min_y:
            new_y = min_y

        self.cursor_position = Position(
            new_x, new_y
        )

    def __place_mines(self) -> List[Position]:
        mine_positions = []
        while len(mine_positions) < self.num_mines:
            new_mine_position = Position(
                x=random.randint(a=0, b=self.size.width - 1),
                y=random.randint(a=0, b=self.size.height - 1)
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
        return '\n'.join(
            ''.join(str(self.cells[x, y]) for x in range(self.size.width)) for y in range(self.size.height)
        )


class Minesweeper:
    def __init__(self, minefield: Minefield) -> None:
        self.minefield = minefield
        self.game_over = False
        self.victory = False

    def __str__(self) -> str:
        return str(self.minefield)


class InputHandler:
    def __init__(self, term) -> None:
        self.term = term

        self.action_to_keystrokes = {
            'MOVE_UP': ['W', self.term.KEY_UP, '8'],
            'MOVE_DOWN': ['S', self.term.KEY_DOWN, '2'],
            'MOVE_LEFT': ['A', self.term.KEY_LEFT, '4'],
            'MOVE_RIGHT': ['D', self.term.KEY_RIGHT, '6'],
            'MOVE_TOP_LEFT': ['7'],
            'MOVE_BOTTOM_LEFT': ['1'],
            'MOVE_TOP_RIGHT': ['9'],
            'MOVE_BOTTOM_RIGHT': ['3'],
            'FLAG': ['F', '0'],
            'REVEAL': ['R', '5'],
        }

    def get_input(self) -> Optional[str]:
        keystroke: keyboard.Keystroke = self.term.inkey(timeout=1)

        for action, keystrokes in self.action_to_keystrokes.items():
            if keystroke.upper() in keystrokes or keystroke.code in keystrokes:
                return action

        return None


def main() -> None:
    term = Terminal()
    print(term.clear)

    size = Size(width=40, height=20)
    num_mines = 100
    minefield = Minefield(Position(0, 0), size, num_mines)

    minesweeper = Minesweeper(minefield)
    ##########
    # Find all empty cells in the minefield
    empty_cells = []
    for x in range(minefield.size.width):
        for y in range(minefield.size.height):
            cell = minefield.cells[x, y]
            if not cell.is_revealed and not cell.is_mine:
                mine_count = sum(neighbour.is_mine for neighbour in cell.neighbours())
                if mine_count == 0:
                    empty_cells.append(cell)
    # Choose a random empty cell and reveal it
    if empty_cells:
        chosen_cell = random.choice(empty_cells)
        chosen_cell.reveal()
        minesweeper.minefield.cursor_position = chosen_cell.position
    else:
        minesweeper.minefield.cursor_position = Position(x=minefield.size.width // 2, y=minefield.size.height // 2)
    #########
    input_handler = InputHandler(term)

    with term.cbreak(), term.hidden_cursor():
        while not minesweeper.game_over and not minesweeper.victory:
            with term.location(minesweeper.minefield.top_left.x, minesweeper.minefield.top_left.y):
                print(minesweeper)
            with term.location(minesweeper.minefield.cursor_position.x, minesweeper.minefield.cursor_position.y):
                print(term.black_on_darkkhaki(str(minesweeper.minefield.cells[
                    minesweeper.minefield.cursor_position.x, minesweeper.minefield.cursor_position.y
                ])))

            action: Optional[str] = input_handler.get_input()

            match action:
                case 'MOVE_UP': minesweeper.minefield.move_cursor(dy=-1)
                case 'MOVE_DOWN': minesweeper.minefield.move_cursor(dy=+1)
                case 'MOVE_LEFT': minesweeper.minefield.move_cursor(dx=-1)
                case 'MOVE_RIGHT': minesweeper.minefield.move_cursor(dx=+1)
                case 'MOVE_TOP_LEFT': minesweeper.minefield.move_cursor(dx=-1, dy=-1)
                case 'MOVE_BOTTOM_LEFT': minesweeper.minefield.move_cursor(dx=-1, dy=+1)
                case 'MOVE_TOP_RIGHT': minesweeper.minefield.move_cursor(dx=+1, dy=-1)
                case 'MOVE_BOTTOM_RIGHT': minesweeper.minefield.move_cursor(dx=+1, dy=+1)
                case 'FLAG': minesweeper.minefield.flag(minesweeper.minefield.cursor_position)
                case 'REVEAL':
                    minesweeper.minefield.reveal(minesweeper.minefield.cursor_position)
                    target_cell = minesweeper.minefield.cells[
                        minesweeper.minefield.cursor_position.x, minesweeper.minefield.cursor_position.y
                    ]
                    if target_cell.is_mine and target_cell.is_revealed:  # TODO: Need to check neighbour mines
                        minesweeper.game_over = True
                    elif minesweeper.minefield.all_cells_revealed_except_mines():
                        minesweeper.victory = True
                case _: pass

        if minesweeper.game_over:
            with term.location(minesweeper.minefield.top_left.x, minesweeper.minefield.top_left.y):
                minesweeper.minefield.reveal_all()
                print(minesweeper)
            with term.location(
                    minesweeper.minefield.top_left.x + minesweeper.minefield.size.width,
                    minesweeper.minefield.top_left.y + minesweeper.minefield.size.height
            ):
                print(term.red + "Game Over! You revealed a mine.")
        elif minesweeper.victory:
            with term.location(minesweeper.minefield.top_left.x, minesweeper.minefield.top_left.y):
                minesweeper.minefield.reveal_all()
                print(minesweeper)
            with term.location(
                    minesweeper.minefield.top_left.x + minesweeper.minefield.size.width,
                    minesweeper.minefield.top_left.y + minesweeper.minefield.size.height
            ):
                print(term.green + "Congratulations! You cleared the minefield.")

    with term.cbreak(), term.hidden_cursor():
        _ = term.inkey()

    print(term.home + term.clear)


if __name__ == '__main__':
    main()
