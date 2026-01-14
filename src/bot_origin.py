import json
import os


class Bot(object):
    """
    The Bot class that applies the Qlearning logic to Flappy bird game
    After every iteration (iteration = 1 game that ends with the bird dying) updates Q values
    After every DUMPING_N iterations, dumps the Q values to the local JSON file
    """

    def __init__(self):
        self.gameCNT = 0  # Game count of current run, incremented after every death
        self.DUMPING_N = 25  # Number of iterations to dump Q values to JSON after
        self.discount = 1.0
        self.r = {0: 1, 1: -1000}  # Reward function
        self.lr = 0.7

        # 获取项目根目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(current_dir)
        self.data_dir = os.path.join(self.project_root, 'data')

        self.load_qvalues()
        self.last_state = "420_240_0"
        self.last_action = 0
        self.moves = []

    def load_qvalues(self):
        """
        Load q values from a JSON file
        """
        self.qvalues = {}
        qvalues_path = os.path.join(self.data_dir, "qvalues.json")
        try:
            with open(qvalues_path, "r") as fil:
                self.qvalues = json.load(fil)
        except (IOError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，初始化一个空字典
            print(f"Q-values file not found or invalid. Initializing empty Q-values.")
            self.qvalues = {}
            # 初始化一些基础状态
            self.qvalues = {"420_240_0": [0.0, 0.0]}

    def act(self, xdif, ydif, vel):
        """
        Chooses the best action with respect to the current state - Chooses 0 (don't flap) to tie-break
        """
        state = self.map_state(xdif, ydif, vel)

        # 如果状态不存在，初始化它
        if state not in self.qvalues:
            self.qvalues[state] = [0.0, 0.0]  # [不跳跃, 跳跃]

        # 确保状态值存在且是列表
        if not isinstance(self.qvalues[state], list) or len(self.qvalues[state]) < 2:
            self.qvalues[state] = [0.0, 0.0]

        self.moves.append(
            (self.last_state, self.last_action, state)
        )  # Add the experience to the history

        self.last_state = state  # Update the last_state with the current state

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
        if not self.moves:
            return

        history = list(reversed(self.moves))

        # Flag if the bird died in the top pipe
        # 添加错误处理，防止状态格式不正确
        try:
            high_death_flag = True if int(history[0][2].split("_")[1]) > 120 else False
        except (IndexError, ValueError):
            high_death_flag = False

        # Q-learning score updates
        t = 1
        for exp in history:
            state = exp[0]
            act = exp[1]
            res_state = exp[2]

            # 确保所有状态都存在
            if state not in self.qvalues:
                self.qvalues[state] = [0.0, 0.0]
            if res_state not in self.qvalues:
                self.qvalues[res_state] = [0.0, 0.0]

            # Select reward
            if t == 1 or t == 2:
                cur_reward = self.r[1]
            elif high_death_flag and act:
                cur_reward = self.r[1]
                high_death_flag = False
            else:
                cur_reward = self.r[0]

            # Update - 添加错误处理
            try:
                self.qvalues[state][act] = (1 - self.lr) * (self.qvalues[state][act]) + \
                                           self.lr * (cur_reward + self.discount * max(self.qvalues[res_state]))
            except (IndexError, TypeError, ValueError) as e:
                # 如果发生错误，重新初始化该状态
                print(f"Error updating Q-values for state {state}: {e}")
                self.qvalues[state] = [0.0, 0.0]

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
            qvalues_path = os.path.join(self.data_dir, "qvalues.json")

            # 确保data目录存在
            os.makedirs(self.data_dir, exist_ok=True)

            with open(qvalues_path, "w") as fil:
                json.dump(self.qvalues, fil)
            print(f"Q-values updated on local file. Game count: {self.gameCNT}")