"""
Headless Flappy Bird Game Engine for AI training
Extracted from flappy.py, with all Pygame display/audio removed
Supports configurable reward function
"""

import random
import os
import sys

# Add project root to path to import constants
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Constants from original flappy.py
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 120 # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.79

# Image dimensions (from original code)
PIPE_WIDTH = 52
PIPE_HEIGHT = 320
PLAYER_WIDTH = 34
PLAYER_HEIGHT = 24
BASE_WIDTH = 336
BACKGROUND_WIDTH = 288


class HeadlessFlappyGame:
    """
    Headless version of Flappy Bird game engine for AI training.
    All rendering and audio functionality removed.
    Supports configurable reward function.
    """
    
    def __init__(self, seed=None, reward_function=None):
        """
        Initialize the game engine.
        
        Args:
            seed (int, optional): Random seed for reproducible results
            reward_function (dict or callable, optional): 
                - If dict: should have keys 'alive', 'score', 'death' with float values
                - If callable: function(state, action, next_state, info) -> float
                - If None: uses default rewards {'alive': 1, 'score': 10, 'death': -1000}
        """
        if seed is not None:
            random.seed(seed)
        
        # Set up reward function
        if reward_function is None:
            self.reward_function = {'alive': 1, 'score': 10, 'death': -1000}
        elif isinstance(reward_function, dict):
            # Validate required keys
            required_keys = ['alive', 'score', 'death']
            for key in required_keys:
                if key not in reward_function:
                    raise ValueError(f"Reward function dict must contain key '{key}'")
            self.reward_function = reward_function.copy()
        elif callable(reward_function):
            self.reward_function = reward_function
        else:
            raise ValueError("reward_function must be None, dict, or callable")
            
        self.reset()
    
    def reset(self):
        """
        Reset the game to initial state.
        
        Returns:
            tuple: Initial state (xdif, ydif, vel)
        """
        # Player position and velocity
        self.playerx = int(SCREENWIDTH * 0.2)
        self.playery = int((SCREENHEIGHT - PLAYER_HEIGHT) / 2)
        self.playerVelY = -9  # Initial upward velocity
        
        # Base position
        self.basex = 0
        self.baseShift = BASE_WIDTH - BACKGROUND_WIDTH
        
        # Pipe velocity
        self.pipeVelX = -4
        
        # Physics constants
        self.playerMaxVelY = 10   # max descend speed
        self.playerAccY = 1       # downward acceleration
        self.playerFlapAcc = -9   # speed on flapping
        self.playerFlapped = False
        
        # Score
        self.score = 0
        
        # Initialize pipes
        newPipe1 = self._get_random_pipe()
        newPipe2 = self._get_random_pipe()
        
        self.upperPipes = [
            {"x": SCREENWIDTH + 200, "y": newPipe1[0]["y"]},
            {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[0]["y"]},
        ]
        
        self.lowerPipes = [
            {"x": SCREENWIDTH + 200, "y": newPipe1[1]["y"]},
            {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[1]["y"]},
        ]
        
        return self._get_state()
    
    def step(self, action):
        """
        Execute one step in the game.
        
        Args:
            action (int): 0 = don't flap, 1 = flap
            
        Returns:
            tuple: (next_state, reward, done, info)
                - next_state: (xdif, ydif, vel)
                - reward: float
                - done: bool (True if game over)
                - info: dict with additional info (score, crash_type, scored)
        """
        # Store previous state for custom reward functions
        prev_state = self._get_state()
        
        # Handle player action
        if action == 1:
            if self.playery > -2 * PLAYER_HEIGHT:
                self.playerVelY = self.playerFlapAcc
                self.playerFlapped = True
        
        # Update player physics
        if self.playerVelY < self.playerMaxVelY and not self.playerFlapped:
            self.playerVelY += self.playerAccY
        if self.playerFlapped:
            self.playerFlapped = False
        
        self.playery += min(self.playerVelY, BASEY - self.playery - PLAYER_HEIGHT)
        
        # Move pipes
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe["x"] += self.pipeVelX
            lPipe["x"] += self.pipeVelX
        
        # Add new pipe when first pipe is about to touch left of screen
        if 0 < self.upperPipes[0]["x"] < 5:
            newPipe = self._get_random_pipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])
        
        # Remove first pipe if it's out of the screen
        if self.upperPipes[0]["x"] < -PIPE_WIDTH:
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)
        
        # Check for score
        playerMidPos = self.playerx + PLAYER_WIDTH / 2
        scored = False
        for pipe in self.upperPipes:
            pipeMidPos = pipe["x"] + PIPE_WIDTH / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                self.score += 1
                scored = True
        
        # Check for collision
        crash_info = self._check_crash()
        done = crash_info["crashed"]
        
        # Get current state
        next_state = self._get_state()
        
        # Calculate reward based on reward function type
        if callable(self.reward_function):
            # Custom callable reward function
            info = {
                "score": self.score,
                "crash_type": "ground" if crash_info["ground_crash"] else "pipe",
                "scored": scored,
                "done": done
            }
            reward = self.reward_function(prev_state, action, next_state, info)
        else:
            # Dictionary-based reward function
            if done:
                reward = self.reward_function['death']
            elif scored:
                reward = self.reward_function['score']
            else:
                reward = self.reward_function['alive']
        
        info = {
            "score": self.score,
            "crash_type": "ground" if crash_info["ground_crash"] else "pipe",
            "scored": scored,
            "done": done
        }
        
        return next_state, reward, done, info
    
    def _get_state(self):
        """
        Get the current game state as (xdif, ydif, vel).
        
        Returns:
            tuple: (xdif, ydif, vel)
        """
        # Find the closest pipe
        if -self.playerx + self.lowerPipes[0]["x"] > -30:
            myPipe = self.lowerPipes[0]
        else:
            myPipe = self.lowerPipes[1]
        
        xdif = -self.playerx + myPipe["x"]
        ydif = -self.playery + myPipe["y"]
        vel = self.playerVelY
        
        return xdif, ydif, vel
    
    def _get_random_pipe(self):
        """
        Generate a randomly positioned pipe pair.
        
        Returns:
            list: [upper_pipe, lower_pipe]
        """
        # y of gap between upper and lower pipe
        gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
        gapY += int(BASEY * 0.2)
        pipeX = SCREENWIDTH + 10
        
        return [
            {"x": pipeX, "y": gapY - PIPE_HEIGHT},  # upper pipe
            {"x": pipeX, "y": gapY + PIPEGAPSIZE},  # lower pipe
        ]
    
    def _check_crash(self):
        """
        Check if the player has crashed.
        
        Returns:
            dict: {"crashed": bool, "ground_crash": bool}
        """
        # Check ground collision
        if (self.playery + PLAYER_HEIGHT >= BASEY - 1) or (self.playery + PLAYER_HEIGHT <= 0):
            return {"crashed": True, "ground_crash": True}
        
        # Check pipe collision using simple rectangle collision
        player_rect = {
            "x": self.playerx,
            "y": self.playery,
            "w": PLAYER_WIDTH,
            "h": PLAYER_HEIGHT
        }
        
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            # Upper pipe collision
            if (player_rect["x"] + player_rect["w"] > uPipe["x"] and
                player_rect["x"] < uPipe["x"] + PIPE_WIDTH and
                player_rect["y"] < uPipe["y"] + PIPE_HEIGHT):
                return {"crashed": True, "ground_crash": False}
            
            # Lower pipe collision
            if (player_rect["x"] + player_rect["w"] > lPipe["x"] and
                player_rect["x"] < lPipe["x"] + PIPE_WIDTH and
                player_rect["y"] + player_rect["h"] > lPipe["y"]):
                return {"crashed": True, "ground_crash": False}
        
        return {"crashed": False, "ground_crash": False}


# Utility function for state mapping (matches bot.py map_state logic)
def map_state(xdif, ydif, vel):
    """
    Map continuous state space to discrete states (same logic as bot.py).
    
    Args:
        xdif (float): Horizontal distance to pipe
        ydif (float): Vertical distance to pipe
        vel (float): Player velocity
        
    Returns:
        str: Discrete state string "xdif_ydif_vel"
    """
    if xdif < 140:
        xdif = int(xdif) - (int(xdif) % 10)
    else:
        xdif = int(xdif) - (int(xdif) % 70)

    if ydif < 180:
        ydif = int(ydif) - (int(ydif) % 10)
    else:
        ydif = int(ydif) - (int(ydif) % 60)

    return f"{int(xdif)}_{int(ydif)}_{int(vel)}"