from dataclasses import dataclass
from itertools import combinations
from typing import List
import z3
import sys


@dataclass
class Position:
    board: List[List[str]]
    width: int
    height: int


def read_position(pos_file: str):
    with open(pos_file) as f:
        metadata = f.readline().strip()
        w, h, *_ = [int(i) for i in metadata.split("x")]
        board: List[List[str]] = []
        for _ in range(h):
            board.append(list(f.readline().strip()))
    return Position(board, w, h)


def get_neighbors(position: Position, x: int, y: int):
    for dx, dy in [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < position.width and 0 <= ny < position.height:
            yield nx, ny


def get_frontier(position: Position):
    for x in range(position.width):
        for y in range(position.height):
            if position.board[y][x] == "H":
                for nx, ny in get_neighbors(position, x, y):
                    if position.board[ny][nx] in "123456789":
                        yield x, y
                        break


def get_numbers(position: Position):
    for x in range(position.width):
        for y in range(position.height):
            if position.board[y][x] in "0123456789":
                yield x, y


def get_possible_bombs(position: Position, x: int, y: int):
    for nx, ny in get_neighbors(position, x, y):
        if position.board[ny][nx] == "H":
            yield nx, ny


def boolean_combinations(n: int, k: int):
    for comb in combinations(range(n), k):
        arr = [False] * n
        for i in comb:
            arr[i] = True
        yield arr


def get_flags(position: Position):
    for x in range(position.width):
        for y in range(position.height):
            if position.board[y][x] == "F":
                yield x, y


def bomb_constraints(
    position: Position, x: int, y: int, variables: List[List[z3.BoolRef]]
):
    possible_bombs = list(get_possible_bombs(position, x, y))
    number = int(position.board[y][x])
    for nx, ny in get_neighbors(position, x, y):
        if position.board[ny][nx] == "F":
            number -= 1
    combs = list(boolean_combinations(len(possible_bombs), number))
    clauses = []
    for comb in combs:
        clauses.append(
            z3.And(
                [
                    (variables[ny][nx] if b else z3.Not(variables[ny][nx]))
                    for (nx, ny), b in zip(possible_bombs, comb)
                ]
            )
        )
    return z3.Or(clauses)


def main():
    pos_file = sys.argv[1]
    position = read_position(pos_file)
    print("\n".join([str(e) for e in position.board]))
    print()

    variables = [
        [z3.Bool(f"b_{x}_{y}") for x in range(position.width)]
        for y in range(position.height)
    ]

    for fx, fy in get_frontier(position):
        solver = z3.Solver()
        for x, y in get_numbers(position):
            solver.add(z3.Not(variables[y][x]))
            if position.board[y][x] == "0":
                for nx, ny in get_neighbors(position, x, y):
                    solver.add(z3.Not(variables[ny][nx]))
            else:
                solver.add(bomb_constraints(position, x, y, variables))
        for x, y in get_flags(position):
            solver.add(variables[y][x])
        solver.add(variables[fy][fx])
        if solver.check() == z3.unsat:
            print(f"Not bomb at {fx}, {fy}")


if __name__ == "__main__":
    main()
