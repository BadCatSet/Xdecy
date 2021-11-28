import heapq
import math
import time

import numpy as np

USE_NUMPY = True
MAX_RUNS = float('inf')

TIME_LIMIT = float('inf')

BY_START = 1
BY_END = 2
SQRT2 = math.sqrt(2)


class DiagonalMovement:
    always = 1
    never = 2
    if_at_most_one_obstacle = 3
    only_when_no_obstacle = 4


class ExecutionTimeException(Exception):
    def __init__(self, message):
        super(ExecutionTimeException, self).__init__(message)


class ExecutionRunsException(Exception):
    def __init__(self, message):
        super(ExecutionRunsException, self).__init__(message)


class Grid(object):
    def __init__(self, width=0, height=0, matrix=None, inverse=False):
        """
        a grid represents the map (as 2d-list of nodes).
        """
        self.width = width
        self.height = height
        self.passable_left_right_border = False
        self.passable_up_down_border = False
        if isinstance(matrix, (tuple, list)) or (
                USE_NUMPY and isinstance(matrix, np.ndarray) and
                matrix.size > 0):
            self.height = len(matrix)
            self.width = self.width = len(matrix[0]) if self.height > 0 else 0
        if self.width > 0 and self.height > 0:
            self.nodes = build_nodes(self.width, self.height, matrix, inverse)
        else:
            self.nodes = [[]]

    def set_passable_left_right_border(self):
        self.passable_left_right_border = True

    def set_passable_up_down_border(self):
        self.passable_up_down_border = True

    def node(self, x, y):
        """
        get node at position
        :param x: x pos
        :param y: y pos
        :return:
        """
        return self.nodes[y][x]

    def inside(self, x, y):
        """
        check, if field position is inside map
        :param x: x pos
        :param y: y pos
        :return:
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable(self, x, y):
        """
        check, if the tile is inside grid and if it is set as walkable
        """
        return self.inside(x, y) and self.nodes[y][x].walkable

    def neighbors(self, node, diagonal_movement=DiagonalMovement.never):
        """
        get all neighbors of one node
        :param node: node
        """
        x = node.x
        y = node.y
        neighbors = []
        s0 = d0 = s1 = d1 = s2 = d2 = s3 = d3 = False

        # ↑
        if y == 0 and self.passable_up_down_border:
            if self.walkable(x, self.height - 1):
                neighbors.append(self.nodes[self.height - 1][x])
                s0 = True
        else:
            if self.walkable(x, y - 1):
                neighbors.append(self.nodes[y - 1][x])
                s0 = True
        # →
        if x == self.width - 1 and self.passable_left_right_border:
            if self.walkable(0, y):
                neighbors.append(self.nodes[y][0])
                s1 = True
        else:
            if self.walkable(x + 1, y):
                neighbors.append(self.nodes[y][x + 1])
                s1 = True
        # ↓
        if y == self.height - 1 and self.passable_up_down_border:
            if self.walkable(x, 0):
                neighbors.append(self.nodes[0][x])
                s2 = True
        else:
            if self.walkable(x, y + 1):
                neighbors.append(self.nodes[y + 1][x])
                s2 = True
        # ←
        if x == 0 and self.passable_left_right_border:
            if self.walkable(self.width - 1, y):
                neighbors.append(self.nodes[y][self.width - 1])
                s3 = True
        else:
            if self.walkable(x - 1, y):
                neighbors.append(self.nodes[y][x - 1])
                s3 = True

        if diagonal_movement == DiagonalMovement.never:
            return neighbors

        if diagonal_movement == DiagonalMovement.only_when_no_obstacle:
            d0 = s3 and s0
            d1 = s0 and s1
            d2 = s1 and s2
            d3 = s2 and s3
        elif diagonal_movement == DiagonalMovement.if_at_most_one_obstacle:
            d0 = s3 or s0
            d1 = s0 or s1
            d2 = s1 or s2
            d3 = s2 or s3
        elif diagonal_movement == DiagonalMovement.always:
            d0 = d1 = d2 = d3 = True

        # ↖
        if d0 and self.walkable(x - 1, y - 1):
            neighbors.append(self.nodes[y - 1][x - 1])

        # ↗
        if d1 and self.walkable(x + 1, y - 1):
            neighbors.append(self.nodes[y - 1][x + 1])

        # ↘
        if d2 and self.walkable(x + 1, y + 1):
            neighbors.append(self.nodes[y + 1][x + 1])

        # ↙
        if d3 and self.walkable(x - 1, y + 1):
            neighbors.append(self.nodes[y + 1][x - 1])

        return neighbors

    def cleanup(self):
        for y_nodes in self.nodes:
            for node in y_nodes:
                node.cleanup()

    def grid_str(self, path=None, start=None, end=None,
                 border=True, start_chr='s', end_chr='e',
                 path_chr='x', empty_chr=' ', block_chr='#',
                 show_weight=False):
        """
        create a printable string from the grid using ASCII characters

        :param path: list of nodes that show the path
        :param start: start node
        :param end: end node
        :param border: create a border around the grid
        :param start_chr: character for the start (default "s")
        :param end_chr: character for the destination (default "e")
        :param path_chr: character to show the path (default "x")
        :param empty_chr: character for empty fields (default " ")
        :param block_chr: character for blocking elements (default "#")
        :param show_weight: instead of empty_chr show the cost of each empty
                            field (shows a + if the value of weight is > 10)
        :return:
        """
        data = ''
        if border:
            data = '+{}+'.format('-' * len(self.nodes[0]))
        for y in range(len(self.nodes)):
            line = ''
            for x in range(len(self.nodes[y])):
                node = self.nodes[y][x]
                if node == start:
                    line += start_chr
                elif node == end:
                    line += end_chr
                elif path and ((node.x, node.y) in path or node in path):
                    line += path_chr
                elif node.walkable:
                    # empty field
                    weight = str(node.weight) if node.weight < 10 else '+'
                    line += weight if show_weight else empty_chr
                else:
                    line += block_chr  # blocked field
            if border:
                line = '|' + line + '|'
            if data:
                data += '\n'
            data += line
        if border:
            data += '\n+{}+'.format('-' * len(self.nodes[0]))
        return data


class Finder(object):
    def __init__(self, heuristic=None, weight=1,
                 diagonal_movement=DiagonalMovement.never,
                 weighted=True,
                 time_limit=TIME_LIMIT,
                 max_runs=MAX_RUNS):
        """
        find shortest path
        :param heuristic: heuristic used to calculate distance of 2 points
            (defaults to manhattan)
        :param weight: weight for the edges
        :param diagonal_movement: if diagonal movement is allowed
            (see enum in diagonal_movement)
        :param weighted: the algorithm supports weighted nodes
            (should be True for A* and Dijkstra)
        :param time_limit: max. runtime in seconds
        :param max_runs: max. amount of tries until we abort the search
            (optional, only if we enter huge grids and have time constrains)
            <=0 means there are no constrains and the code might run on any
            large map.
        """
        self.time_limit = time_limit
        self.max_runs = max_runs
        self.weighted = weighted

        self.diagonal_movement = diagonal_movement
        self.weight = weight
        self.heuristic = heuristic

    def calc_cost(self, node_a, node_b):
        """
        get the distance between current node and the neighbor (cost)
        """
        if node_b.x - node_a.x == 0 or node_b.y - node_a.y == 0:
            # direct neighbor - distance is 1
            ng = 1
        else:
            # not a direct neighbor - diagonal movement
            ng = SQRT2

        # weight for weighted algorithms
        if self.weighted:
            ng *= node_b.weight

        return node_a.g + ng

    def apply_heuristic(self, node_a, node_b, heuristic=None):
        """
        helper function to apply heuristic
        """
        if not heuristic:
            heuristic = self.heuristic
        return heuristic(
            abs(node_a.x - node_b.x),
            abs(node_a.y - node_b.y))

    def find_neighbors(self, grid, node, diagonal_movement=None):
        '''
        find neighbor, same for Djikstra, A*, Bi-A*, IDA*
        '''
        if not diagonal_movement:
            diagonal_movement = self.diagonal_movement
        return grid.neighbors(node, diagonal_movement=diagonal_movement)

    def keep_running(self):
        """
        check, if we run into time or iteration constrains.
        :returns: True if we keep running and False if we run into a constraint
        """
        if self.runs >= self.max_runs:
            raise ExecutionRunsException(
                '{} run into barrier of {} iterations without '
                'finding the destination'.format(
                    self.__class__.__name__, self.max_runs))

        if time.time() - self.start_time >= self.time_limit:
            raise ExecutionTimeException(
                '{} took longer than {} seconds, aborting!'.format(
                    self.__class__.__name__, self.time_limit))

    def process_node(self, node, parent, end, open_list, open_value=True):
        '''
        we check if the given node is path of the path by calculating its
        cost and add or remove it from our path
        :param node: the node we like to test
            (the neighbor in A* or jump-node in JumpPointSearch)
        :param parent: the parent node (the current node we like to test)
        :param end: the end point to calculate the cost of the path
        :param open_list: the list that keeps track of our current path
        :param open_value: needed if we like to set the open list to something
            else than True (used for bi-directional algorithms)

        '''
        # calculate cost from current node (parent) to the next node (neighbor)
        ng = self.calc_cost(parent, node)

        if not node.opened or ng < node.g:
            node.g = ng
            node.h = node.h or \
                     self.apply_heuristic(node, end) * self.weight
            # f is the estimated total cost from start to goal
            node.f = node.g + node.h
            node.parent = parent

            if not node.opened:
                heapq.heappush(open_list, node)
                node.opened = open_value
            else:
                # the node can be reached with smaller cost.
                # Since its f value has been updated, we have to
                # update its position in the open list
                open_list.remove(node)
                heapq.heappush(open_list, node)

    def check_neighbors(self, start, end, grid, open_list,
                        open_value=True, backtrace_by=None):
        """
        find next path segment based on given node
        (or return path if we found the end)

        :param start: start node
        :param end: end node
        :param grid: grid that stores all possible steps/tiles as 2D-list
        :param open_list: stores nodes that will be processed next
        """
        raise NotImplementedError(
            'Please implement check_neighbors in your finder')

    def find_path(self, start, end, grid):
        """
        find a path from start to end node on grid by iterating over
        all neighbors of a node (see check_neighbors)
        :param start: start node
        :param end: end node
        :param grid: grid that stores all possible steps/tiles as 2D-list
        :return:
        """
        self.start_time = time.time()  # execution time limitation
        self.runs = 0  # count number of iterations
        start.opened = True

        open_list = [start]

        while len(open_list) > 0:
            self.runs += 1
            self.keep_running()

            path = self.check_neighbors(start, end, grid, open_list)
            if path:
                return path, self.runs

        # failed to find path
        return [], self.runs


class Node(object):
    """
    basic node, saves X and Y coordinates on some grid and determine if
    it is walkable.
    """

    def __init__(self, x=0, y=0, walkable=True, weight=1):
        # Coordinates
        self.x = x
        self.y = y

        # Whether this node can be walked through.
        self.walkable = walkable

        # used for weighted algorithms
        self.weight = weight

        # values used in the finder
        self.cleanup()

    def __lt__(self, other):
        """
        nodes are sorted by f value (see a_star.py)

        :param other: compare Node
        :return:
        """
        return self.f < other.f

    def cleanup(self):
        """
        reset all calculated values, fresh start for pathfinding
        """
        # cost from this node to the goal
        self.h = 0.0

        # cost from the start node to this node
        self.g = 0.0

        # distance from start to this point (f = g + h )
        self.f = 0.0

        self.opened = 0
        self.closed = False

        # used for backtracking to the start point
        self.parent = None

        # used for recurion tracking of IDA*
        self.retain_count = 0
        # used for IDA* and Jump-Point-Search
        self.tested = False


class AStarFinder(Finder):
    def __init__(self, heuristic=None, weight=1,
                 diagonal_movement=DiagonalMovement.never,
                 time_limit=TIME_LIMIT,
                 max_runs=MAX_RUNS):
        """
        find shortest path using A* algorithm
        :param heuristic: heuristic used to calculate distance of 2 points
            (defaults to manhattan)
        :param weight: weight for the edges
        :param diagonal_movement: if diagonal movement is allowed
            (see enum in diagonal_movement)
        :param time_limit: max. runtime in seconds
        :param max_runs: max. amount of tries until we abort the search
            (optional, only if we enter huge grids and have time constrains)
            <=0 means there are no constrains and the code might run on any
            large map.
        """
        super(AStarFinder, self).__init__(
            heuristic=heuristic,
            weight=weight,
            diagonal_movement=diagonal_movement,
            time_limit=time_limit,
            max_runs=max_runs)

        if not heuristic:
            if diagonal_movement == DiagonalMovement.never:
                self.heuristic = manhattan
            else:
                # When diagonal movement is allowed the manhattan heuristic is
                # not admissible it should be octile instead
                self.heuristic = octile

    def check_neighbors(self, start, end, grid, open_list,
                        open_value=True, backtrace_by=None):
        """
        find next path segment based on given node
        (or return path if we found the end)

        :param start: start node
        :param end: end node
        :param grid: grid that stores all possible steps/tiles as 2D-list
        :param open_list: stores nodes that will be processed next
        """
        # pop node with minimum 'f' value
        node = heapq.nsmallest(1, open_list)[0]
        open_list.remove(node)
        node.closed = True

        # if reached the end position, construct the path and return it
        # (ignored for bi-directional a*, there we look for a neighbor that is
        #  part of the oncoming path)
        if not backtrace_by and node == end:
            return backtrace(end)

        # get neighbors of the current node
        neighbors = self.find_neighbors(grid, node)
        for neighbor in neighbors:
            if neighbor.closed:
                # already visited last minimum f value
                continue
            if backtrace_by and neighbor.opened == backtrace_by:
                # found the oncoming path
                if backtrace_by == BY_END:
                    return bi_backtrace(node, neighbor)
                else:
                    return bi_backtrace(neighbor, node)

            # check if the neighbor has not been inspected yet, or
            # can be reached with smaller cost from the current node
            self.process_node(neighbor, node, end, open_list, open_value)

        # the end has not been reached (yet) keep the find_path loop running
        return None

    def find_path(self, start, end, grid):
        """
        find a path from start to end node on grid using the A* algorithm
        :param start: start node
        :param end: end node
        :param grid: grid that stores all possible steps/tiles as 2D-list
        :return:
        """
        start.g = 0
        start.f = 0
        return super(AStarFinder, self).find_path(start, end, grid)


def manhattan(dx, dy):
    """manhattan heuristics"""
    return dx + dy


def euclidean(dx, dy):
    """euclidean distance heuristics"""
    return math.sqrt(dx * dx + dy * dy)


def chebyshev(dx, dy):
    """ Chebyshev distance. """
    return max(dx, dy)


def octile(dx, dy):
    f = SQRT2 - 1
    if dx < dy:
        return f * dx + dy
    else:
        return f * dy + dx


def backtrace(node):
    """
    Backtrace according to the parent records and return the path.
    (including both start and end nodes)
    """
    path = [(node.x, node.y)]
    while node.parent:
        node = node.parent
        path.append((node.x, node.y))
    path.reverse()
    return path


def bi_backtrace(node_a, node_b):
    """
    Backtrace from start and end node, returns the path for bi-directional A*
    (including both start and end nodes)
    """
    path_a = backtrace(node_a)
    path_b = backtrace(node_b)
    path_b.reverse()
    return path_a + path_b


def build_nodes(width, height, matrix=None, inverse=False):
    """
    create nodes according to grid size. If a matrix is given it
    will be used to determine what nodes are walkable.
    :rtype : list
    """
    nodes = []
    use_matrix = (isinstance(matrix, (tuple, list))) or \
                 (USE_NUMPY and isinstance(matrix, np.ndarray) and matrix.size > 0)

    for y in range(height):
        nodes.append([])
        for x in range(width):
            # 1, '1', True will be walkable
            # while others will be obstacles
            # if inverse is False, otherwise
            # it changes
            weight = int(matrix[y][x]) if use_matrix else 1
            walkable = weight <= 0 if inverse else weight >= 1

            nodes[y].append(Node(x=x, y=y, walkable=walkable, weight=weight))
    return nodes
