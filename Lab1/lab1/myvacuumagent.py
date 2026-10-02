from lab1.vacuum import *

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
        self.mode = "GO_NORTH"
        self.sweep_direction = AGENT_DIRECTION_EAST
        self.initial_random_actions = 10
        self.iteration_counter = world_width*world_height*2
        self.state = MyAgentState(world_width, world_height)
        self.log = log

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
        # Phase 1: move north until reaching the north wall
        if self.mode == "GO_NORTH":

            # If the previous forward movement hit the north wall
            if bump:
                self.mode = "GO_WEST"

                action = self.face_direction(AGENT_DIRECTION_WEST)

                if action is not None:
                    return action

            # Make sure the agent is facing north
            action = self.face_direction(AGENT_DIRECTION_NORTH)

            if action is not None:
                return action

            # Already facing north -> move forward
            return self.do_action(ACTION_FORWARD)

        # Phase 2: move west until reaching the west wall
        if self.mode == "GO_WEST":

            # If the previous forward movement hit the west wall
            if bump:
                self.mode = "SWEEP_EAST"

                action = self.face_direction(AGENT_DIRECTION_EAST)

                if action is not None:
                    return action

            # Make sure the agent is facing west
            action = self.face_direction(AGENT_DIRECTION_WEST)

            if action is not None:
                return action

            # Already facing west -> move forward
            return self.do_action(ACTION_FORWARD)

        if self.mode == "SWEEP_EAST":

            if bump:
                self.mode = "MOVE_DOWN"

                action = self.face_direction(AGENT_DIRECTION_SOUTH)

                if action is not None:
                    return action

                return self.do_action(ACTION_FORWARD)

            action = self.face_direction(AGENT_DIRECTION_EAST)

            if action is not None:
                return action

            return self.do_action(ACTION_FORWARD)

        # Phase 4: move down one row
        if self.mode == "MOVE_DOWN":

            action = self.face_direction(AGENT_DIRECTION_SOUTH)

            if action is not None:
                return action

            self.mode = "AFTER_MOVE_DOWN"
            return self.do_action(ACTION_FORWARD)