from lab1.vacuum import *
from collections import deque
DEBUG_OPT_DENSEWORLDMAP = False

AGENT_STATE_UNKNOWN = 0
AGENT_STATE_WALL = 1
AGENT_STATE_CLEAR = 2
AGENT_STATE_DIRT = 3
AGENT_STATE_HOME = 4

AGENT_DIRECTION_NORTH = 0
AGENT_DIRECTION_EAST = 1
AGENT_DIRECTION_SOUTH = 2
AGENT_DIRECTION_WEST = 3

def direction_to_string(cdr):
    cdr %= 4
    return  "NORTH" if cdr == AGENT_DIRECTION_NORTH else\
            "EAST"  if cdr == AGENT_DIRECTION_EAST else\
            "SOUTH" if cdr == AGENT_DIRECTION_SOUTH else\
            "WEST" #if dir == AGENT_DIRECTION_WEST

"""
Internal state of a vacuum agent
"""
class MyAgentState:

    def __init__(self, width, height):

        # Initialize perceived world state
        self.world = [[AGENT_STATE_UNKNOWN for _ in range(height)] for _ in range(width)]
        self.world[1][1] = AGENT_STATE_HOME

        # Agent internal state
        self.last_action = ACTION_NOP
        self.direction = AGENT_DIRECTION_EAST
        self.pos_x = 1
        self.pos_y = 1

        # Metadata
        self.world_width = width
        self.world_height = height
        print(width, height)

    """
    Update perceived agent location
    """
    def update_position(self, bump):
        if not bump and self.last_action == ACTION_FORWARD:
            if self.direction == AGENT_DIRECTION_EAST:
                self.pos_x += 1
            elif self.direction == AGENT_DIRECTION_SOUTH:
                self.pos_y += 1
            elif self.direction == AGENT_DIRECTION_WEST:
                self.pos_x -= 1
            elif self.direction == AGENT_DIRECTION_NORTH:
                self.pos_y -= 1

    """
    Update perceived agent direction
    """
    def update_direction(self, action):
        if action == ACTION_TURN_LEFT:
            self.direction = (self.direction + 3) % 4

        elif action == ACTION_TURN_RIGHT:
            self.direction = (self.direction + 1) % 4

    """
    Update perceived agent direction and last action
    """
    def record_action(self, action):
        self.update_direction(action)
        self.last_action = action

    """
    Update perceived or inferred information about a part of the world
    """
    def update_world(self, x, y, info):
        self.world[x][y] = info

    """
    Corrects the agent's position to (1, 1) if it is at home
    """
    def correct_position_with_home(self, home):
        if home:
            self.pos_x = 1
            self.pos_y = 1

    """
    Dumps a map of the world as the agent knows it
    """
    def print_world_debug(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y] == AGENT_STATE_UNKNOWN:
                    print("?" if DEBUG_OPT_DENSEWORLDMAP else " ? ", end="")
                elif self.world[x][y] == AGENT_STATE_WALL:
                    print("#" if DEBUG_OPT_DENSEWORLDMAP else " # ", end="")
                elif self.world[x][y] == AGENT_STATE_CLEAR:
                    print("." if DEBUG_OPT_DENSEWORLDMAP else " . ", end="")
                elif self.world[x][y] == AGENT_STATE_DIRT:
                    print("D" if DEBUG_OPT_DENSEWORLDMAP else " D ", end="")
                elif self.world[x][y] == AGENT_STATE_HOME:
                    print("H" if DEBUG_OPT_DENSEWORLDMAP else " H ", end="")

            print() # Newline
        print() # Delimiter post-print

"""
Vacuum agent
"""
class MyVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)

        self.mode = "DFS_INIT"
        self.home_path = []

        self.initial_random_actions = 10
        self.iteration_counter = world_width * world_height * 10

        self.state = MyAgentState(world_width, world_height)
        self.log = log

        # DFS memory
        self.visited = set()
        self.dfs_stack = []
        self.tried_directions = {}
        self.pending_move = None
        self.selected_direction = None

    def move_to_random_start_position(self, bump):
        action = random()

        self.initial_random_actions -= 1
        self.state.update_position(bump)

        if action < 0.1666666:
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            return ACTION_TURN_LEFT

        elif action < 0.3333333:
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            return ACTION_TURN_RIGHT

        else:
            self.state.last_action = ACTION_FORWARD
            return ACTION_FORWARD

    def do_action(self, action):
        self.state.record_action(action)
        return action

    def get_neighbor(self, x, y, direction):

        if direction == AGENT_DIRECTION_NORTH:
            return (x, y - 1)

        elif direction == AGENT_DIRECTION_EAST:
            return (x + 1, y)

        elif direction == AGENT_DIRECTION_SOUTH:
            return (x, y + 1)

        elif direction == AGENT_DIRECTION_WEST:
            return (x - 1, y)

    def has_tried_direction(self, x, y, direction):

        position = (x, y)

        if position not in self.tried_directions:
            return False

        return direction in self.tried_directions[position]

    def get_untried_direction(self, x, y):

        directions = [
            AGENT_DIRECTION_NORTH,
            AGENT_DIRECTION_EAST,
            AGENT_DIRECTION_SOUTH,
            AGENT_DIRECTION_WEST
        ]

        for direction in directions:
            if not self.has_tried_direction(x, y, direction):
                return direction

        return None

    def mark_direction_tried(self, x, y, direction):
        position = (x, y)

        if position not in self.tried_directions:
            self.tried_directions[position] = set()

        self.tried_directions[position].add(direction)

    def face_direction(self, target_direction):

        diff = (target_direction - self.state.direction) % 4

        if diff == 0:
            return None

        if diff == 1:
            return self.do_action(ACTION_TURN_RIGHT)

        if diff == 3:
            return self.do_action(ACTION_TURN_LEFT)

        # opposite direction
        return self.do_action(ACTION_TURN_RIGHT)

    def find_path_to_home(self, start):

        goal = (1, 1)

        # Already at home
        if start == goal:
            return []

        queue = deque([start])

        # parent[cell] = previous cell on the BFS path
        parent = {
            start: None
        }

        # direction_used[cell] = direction used to enter this cell
        direction_used = {}

        directions = [
            AGENT_DIRECTION_NORTH,
            AGENT_DIRECTION_EAST,
            AGENT_DIRECTION_SOUTH,
            AGENT_DIRECTION_WEST
        ]

        while queue:

            current = queue.popleft()

            if current == goal:
                break

            x, y = current

            for direction in directions:

                neighbor = self.get_neighbor(
                    x,
                    y,
                    direction
                )

                # Only travel through cells already known to be reachable
                if neighbor not in self.visited:
                    continue

                # Already discovered by BFS
                if neighbor in parent:
                    continue

                parent[neighbor] = current
                direction_used[neighbor] = direction

                queue.append(neighbor)

        # No known path to home
        if goal not in parent:
            return None

        # Reconstruct path from home back to start
        path = []

        current = goal

        while current != start:
            path.append(
                direction_used[current]
            )

            current = parent[current]

        path.reverse()

        return path

    def direction_between(self, current, target):

        x, y = current
        target_x, target_y = target

        if target_x == x and target_y == y - 1:
            return AGENT_DIRECTION_NORTH

        elif target_x == x + 1 and target_y == y:
            return AGENT_DIRECTION_EAST

        elif target_x == x and target_y == y + 1:
            return AGENT_DIRECTION_SOUTH

        elif target_x == x - 1 and target_y == y:
            return AGENT_DIRECTION_WEST

        return None

    def has_unexplored_frontier(self):

        directions = [
            AGENT_DIRECTION_NORTH,
            AGENT_DIRECTION_EAST,
            AGENT_DIRECTION_SOUTH,
            AGENT_DIRECTION_WEST
        ]

        for x, y in self.visited:

            for direction in directions:

                nx, ny = self.get_neighbor(
                    x,
                    y,
                    direction
                )

                # Outside the internal world
                if not (
                        0 <= nx < self.state.world_width
                        and 0 <= ny < self.state.world_height
                ):
                    continue

                neighbor = (nx, ny)

                # Already known reachable
                if neighbor in self.visited:
                    continue

                # Already known obstacle
                if self.state.world[nx][ny] == AGENT_STATE_WALL:
                    continue

                # Unknown cell adjacent to a reachable cell
                return True

        return False

    def is_exploration_complete(self):

        directions = [
            AGENT_DIRECTION_NORTH,
            AGENT_DIRECTION_EAST,
            AGENT_DIRECTION_SOUTH,
            AGENT_DIRECTION_WEST
        ]

        for x, y in self.visited:

            for direction in directions:

                neighbor = self.get_neighbor(
                    x,
                    y,
                    direction
                )

                nx, ny = neighbor

                # Outside internal world boundaries
                if not (
                        0 <= nx < self.state.world_width
                        and 0 <= ny < self.state.world_height
                ):
                    continue

                # Already known reachable
                if neighbor in self.visited:
                    continue

                # Already known wall
                if self.state.world[nx][ny] == AGENT_STATE_WALL:
                    continue

                # Still an unresolved neighboring cell
                return False

        return True



    def execute(self, percept):

        ###########################
        # DO NOT MODIFY THIS CODE #
        ###########################

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Move agent to a randomly chosen initial position
        if self.initial_random_actions > 0:
            self.log("Moving to random start position ({} steps left)".format(self.initial_random_actions))
            return self.move_to_random_start_position(bump)

        # Finalize randomization by properly updating position (without subsequently changing it)
        elif self.initial_random_actions == 0:
            self.initial_random_actions -= 1
            self.state.update_position(bump)
            self.state.last_action = ACTION_SUCK
            self.log("Processing percepts after position randomization")
            return ACTION_SUCK


        ########################
        # START MODIFYING HERE #
        ########################

        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log("Performance: {}".format(self.performance))
            return ACTION_NOP

        self.iteration_counter -= 1

        # Track position of agent
        self.state.update_position(bump)
        self.state.correct_position_with_home(home)

        self.log(
            "Position: ({}, {})\t\tDirection: {}".format(
                self.state.pos_x,
                self.state.pos_y,
                direction_to_string(self.state.direction)
            )
        )

        if bump:
            # Get an xy-offset pair based on where the agent is facing
            offset = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.state.direction]

            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(self.state.pos_x + offset[0], self.state.pos_y + offset[1], AGENT_STATE_WALL)

        # Update perceived state of current tile
        if dirt:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_DIRT)
        else:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_CLEAR)

        # Debug
        self.state.print_world_debug()

        # Decide action
        if dirt:
            self.state.update_world(
                self.state.pos_x,
                self.state.pos_y,
                AGENT_STATE_DIRT
            )
            return self.do_action(ACTION_SUCK)

        elif home:
            self.state.update_world(
                self.state.pos_x,
                self.state.pos_y,
                AGENT_STATE_HOME
            )

        else:
            self.state.update_world(
                self.state.pos_x,
                self.state.pos_y,
                AGENT_STATE_CLEAR
            )


        # =========================
        # Phase 1: Initialize DFS
        # =========================
        if self.mode == "DFS_INIT":
            current = (
                self.state.pos_x,
                self.state.pos_y
            )

            # Mark the starting cell as visited
            self.visited.add(current)

            # Start the DFS path from the current cell
            self.dfs_stack.append(current)

            # Move to the next DFS phase
            self.mode = "DFS_SELECT"

        # =========================
        # Phase 4: Process movement result
        # =========================
        if self.mode == "DFS_PROCESS_MOVE":

            move = self.pending_move

            # Safety check
            if move is None:
                self.mode = "DFS_SELECT"

            else:
                target = move["to"]

                # Movement failed -> obstacle/wall
                if bump:
                    self.state.update_world(
                        target[0],
                        target[1],
                        AGENT_STATE_WALL
                    )

                    self.pending_move = None
                    self.selected_direction = None
                    self.mode = "DFS_SELECT"

                # Movement succeeded -> new reachable cell
                else:
                    if target not in self.visited:
                        self.visited.add(target)
                        self.dfs_stack.append(target)

                    self.pending_move = None
                    self.selected_direction = None
                    self.mode = "DFS_SELECT"

        # =========================
        # Phase 6: Process backtrack result
        # =========================
        if self.mode == "DFS_PROCESS_BACKTRACK":

            move = self.pending_move

            # Safety check
            if move is None:
                self.mode = "DFS_SELECT"

            else:
                # Backtracking should normally succeed
                if bump:
                    self.log("Warning: Backtrack movement failed.")

                    self.pending_move = None
                    self.mode = "DFS_DONE"

                else:
                    # Remove the cell we just left
                    if len(self.dfs_stack) > 1:
                        self.dfs_stack.pop()

                    self.pending_move = None
                    self.mode = "DFS_SELECT"

        # =========================
        # Phase 10: Process home movement
        # =========================
        if self.mode == "DFS_PROCESS_HOME_MOVE":

            move = self.pending_move

            if move is None:
                self.mode = "PLAN_HOME_PATH"

            else:
                # This should normally never happen because
                # BFS only uses previously visited cells.
                if bump:
                    self.log("Warning: Return-home movement failed. Replanning path.")

                    self.pending_move = None
                    self.mode = "PLAN_HOME_PATH"

                else:
                    # Successfully completed the first step
                    if len(self.home_path) > 0:
                        self.home_path.pop(0)

                    self.pending_move = None
                    self.mode = "RETURN_HOME"

        # =========================
        # Phase 2: Select next cell
        # =========================
        if self.mode == "DFS_SELECT":

            if not self.has_unexplored_frontier():

                self.log(
                    "All reachable cells explored. Planning shortest path home."
                )

                self.mode = "PLAN_HOME_PATH"

            else:
                current_x = self.state.pos_x
                current_y = self.state.pos_y

                while True:

                    direction = self.get_untried_direction(
                        current_x,
                        current_y
                    )

                    if direction is None:
                        self.mode = "DFS_BACKTRACK"
                        break

                    neighbor = self.get_neighbor(
                        current_x,
                        current_y,
                        direction
                    )

                    # Skip cells that are already visited
                    if neighbor in self.visited:
                        self.mark_direction_tried(
                            current_x,
                            current_y,
                            direction
                        )
                        continue

                    nx, ny = neighbor

                    # Skip walls that are already known
                    if (
                            0 <= nx < self.state.world_width
                            and 0 <= ny < self.state.world_height
                            and self.state.world[nx][ny] == AGENT_STATE_WALL
                    ):
                        self.mark_direction_tried(
                            current_x,
                            current_y,
                            direction
                        )
                        continue

                    self.selected_direction = direction
                    self.mode = "DFS_MOVE"
                    break

        # =========================
        # Phase 3: Move to selected cell
        # =========================
        if self.mode == "DFS_MOVE":

            direction = self.selected_direction

            # Turn toward the selected direction
            action = self.face_direction(direction)

            if action is not None:
                return action

            # Agent is now facing the selected direction
            current = (
                self.state.pos_x,
                self.state.pos_y
            )

            neighbor = self.get_neighbor(
                self.state.pos_x,
                self.state.pos_y,
                direction
            )

            # This direction is now actually being tried
            self.mark_direction_tried(
                self.state.pos_x,
                self.state.pos_y,
                direction
            )

            # Remember the attempted movement
            self.pending_move = {
                "from": current,
                "to": neighbor,
                "direction": direction,
                "type": "EXPLORE"
            }

            # Next percept will tell us whether the move succeeded
            self.mode = "DFS_PROCESS_MOVE"

            return self.do_action(ACTION_FORWARD)



        # =========================
        # Phase 5: Backtrack
        # =========================
        if self.mode == "DFS_BACKTRACK":

            # If only the root remains, DFS exploration is finished
            if len(self.dfs_stack) <= 1:

                if not self.has_unexplored_frontier():
                    self.mode = "PLAN_HOME_PATH"

                else:
                    self.log(
                        "Warning: DFS root reached while unexplored frontier remains."
                    )
                    self.mode = "DFS_DONE"
            else:
                current = (
                    self.state.pos_x,
                    self.state.pos_y
                )

                # Parent is the previous cell in the DFS path
                parent = self.dfs_stack[-2]

                direction = self.direction_between(
                    current,
                    parent
                )

                # Turn toward the parent
                action = self.face_direction(direction)

                if action is not None:
                    return action

                # Remember that this is a backtracking movement
                self.pending_move = {
                    "from": current,
                    "to": parent,
                    "direction": direction,
                    "type": "BACKTRACK"
                }

                self.mode = "DFS_PROCESS_BACKTRACK"

                return self.do_action(ACTION_FORWARD)

        # =========================
        # Phase 8: Plan path home
        # =========================
        if self.mode == "PLAN_HOME_PATH":

            current = (
                self.state.pos_x,
                self.state.pos_y
            )

            self.home_path = self.find_path_to_home(
                current
            )

            # No known route to home
            if self.home_path is None:
                self.log("Warning: No path to home was found.")
                self.mode = "DFS_DONE"

            else:
                self.log(
                    "Path home found. Length: {}".format(
                        len(self.home_path)
                    )
                )

                self.mode = "RETURN_HOME"

        # =========================
        # Phase 9: Return home
        # =========================
        if self.mode == "RETURN_HOME":

            # Simulator confirms that the agent is home
            if home:
                self.mode = "DFS_DONE"

            # Path finished
            elif len(self.home_path) == 0:

                self.log(
                    "Home path exhausted but agent is not home. Replanning."
                )

                self.mode = "PLAN_HOME_PATH"

            else:
                direction = self.home_path[0]

                # Turn toward the next step
                action = self.face_direction(direction)

                if action is not None:
                    return action

                current = (
                    self.state.pos_x,
                    self.state.pos_y
                )

                target = self.get_neighbor(
                    self.state.pos_x,
                    self.state.pos_y,
                    direction
                )

                # Remember the movement before executing it
                self.pending_move = {
                    "from": current,
                    "to": target,
                    "direction": direction,
                    "type": "RETURN_HOME"
                }

                self.mode = "DFS_PROCESS_HOME_MOVE"

                return self.do_action(ACTION_FORWARD)

        # =========================
        # Phase 7: Finish DFS
        # =========================
        if self.mode == "DFS_DONE":
            self.log("DFS exploration completed.")
            self.log("Visited cells: {}".format(len(self.visited)))
            self.log("Performance: {}".format(self.performance))

            return self.do_action(ACTION_NOP)

