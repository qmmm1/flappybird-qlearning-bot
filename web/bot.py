import json
import os
import random


class Bot(object):
    """
    The Bot class that applies the Qlearning logic to Flappy bird game
    After every iteration (iteration = 1 game that ends with the bird dying) updates Q values
    After every DUMPING_N iterations, dumps the Q values to the local JSON file
    """

    def __init__(self, lr=None, discount=None, r=None, qfile=None):
        self.gameCNT = 0  # Game count of current run, incremented after every death
        self.DUMPING_N = 25  # Number of iterations to dump Q values to JSON after
        
        # 使用传入参数或默认值
        self.lr = lr if lr is not None else 0.7
        self.discount = discount if discount is not None else 1.0
        self.r = r if r is not None else {0: 1, 1: -1000}  # 默认奖励函数
        self.epsilon =0.1

        # ✅ 修正：qfile 是完整文件路径，不是目录！
        if qfile is not None:
            self.qfile = qfile
        else:
            # 默认回退到全局 qvalues.json（兼容旧逻辑）
            self.qfile = os.path.join("user_data", "qvalues.json")

        self.load_qvalues()
        self.last_state = "420_240_0"
        self.last_action = 0
        self.moves = []

    def load_qvalues(self):
        """
        Load q values from a JSON file
        """
        self.qvalues = {}
        try:
            with open(self.qfile, "r") as fil:
                self.qvalues = json.load(fil)
        except (IOError, json.JSONDecodeError):
            print(f"Q-values file not found or invalid: {self.qfile}. Initializing empty Q-values.")
            self.qvalues = {"420_240_0": [0.0, 0.0]}


    def act(self, xdif, ydif, vel):
        state = self.map_state(xdif, ydif, vel)
        if state not in self.qvalues:
            self.qvalues[state] = [0.0, 0.0]
        
        self.moves.append((self.last_state, self.last_action, state))
        self.last_state = state
        
        # 纯贪心：平局时选 0（不 flap）
        if self.qvalues[state][0] >= self.qvalues[state][1]:
            self.last_action = 0
            return 0
        else:
            self.last_action = 1
            return 1

    def update_scores(self, dump_qvalues=True):
        """
        Update qvalues via iterating over experiences
        """
        history = list(reversed(self.moves))

        # Flag if the bird died in the top pipe
        high_death_flag = True if int(history[0][2].split("_")[1]) > 120 else False

        # Q-learning score updates
        t = 1
        for exp in history:
            state = exp[0]
            act = exp[1]
            res_state = exp[2]

            # Select reward
            if t == 1 or t == 2:
                cur_reward = self.r[1]
            elif high_death_flag and act:
                cur_reward = self.r[1]
                high_death_flag = False
            else:
                cur_reward = self.r[0]

            # Update
            self.qvalues[state][act] = (1-self.lr) * (self.qvalues[state][act]) + \
                                       self.lr * ( cur_reward + self.discount*max(self.qvalues[res_state]) )

            t += 1

        self.gameCNT += 1  # increase game count
        if dump_qvalues:
            self.dump_qvalues()  # Dump q values (if game count % DUMPING_N == 0)
        self.moves = []  # clear history after updating strategies

    def map_state(self, xdif, ydif, vel):
        """
        Map the (xdif, ydif, vel) to the respective state, with regards to the grids
        The state is a string, "xdif_ydif_vel"

        X -> [-40,-30...120] U [140, 210 ... 420]
        Y -> [-300, -290 ... 160] U [180, 240 ... 420]
        """
        if xdif < 140:
            xdif = int(xdif) - (int(xdif) % 10)
        else:
            xdif = int(xdif) - (int(xdif) % 70)

        if ydif < 180:
            ydif = int(ydif) - (int(ydif) % 10)
        else:
            ydif = int(ydif) - (int(ydif) % 60)

        return str(int(xdif)) + "_" + str(int(ydif)) + "_" + str(vel)

    def dump_qvalues(self, force=False):
        """
        Dump the qvalues to the JSON file
        """
        if self.gameCNT % self.DUMPING_N == 0 or force:
            # ✅ 确保目录存在（因为 self.qfile 是完整路径）
            os.makedirs(os.path.dirname(self.qfile), exist_ok=True)
            
            with open(self.qfile, "w") as fil:
                json.dump(self.qvalues, fil)
            print(f"Q-values saved to {self.qfile}. Game count: {self.gameCNT}")