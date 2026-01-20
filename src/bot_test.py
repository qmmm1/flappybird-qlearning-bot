import json
import os
import random


class Bot(object):
    """
    The Bot class that applies the Qlearning logic to Flappy bird game
    After every iteration (iteration = 1 game that ends with the bird dying) updates Q values
    After every DUMPING_N iterations, dumps the Q values to the local JSON file
    """

    def __init__(self):
        self.gameCNT = 0  # Game count of current run, incremented after every death
        self.DUMPING_N = 25  # Number of iterations to dump Q values to JSON after
        self.discount = 1
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

    import random

    def act(self, xdif, ydif, vel):
        state = self.map_state(xdif, ydif, vel)

        if state not in self.qvalues:
            self.qvalues[state] = [0.0, 0.0]

        self.moves.append((self.last_state, self.last_action, state))
        self.last_state = state

        # === 新增：ε-greedy 探索 ===
        epsilon = max(0.05, 1.0 - self.gameCNT / 500.0)  # 前500局从1.0衰减到0.05

        if random.random() < epsilon:
            action = random.choice([0, 1])  # 随机探索
        else:
            # 贪心选择（tie-break 优先不跳）
            if self.qvalues[state][0] >= self.qvalues[state][1]:
                action = 0
            else:
                action = 1

        self.last_action = action
        return action

    def update_scores(self, dump_qvalues=True):
        """
        Update qvalues via iterating over experiences
        """
        if not self.moves:
            return

        history = list(reversed(self.moves))

        # Flag if the bird died in the top pipe
        try:
            high_death_flag = True if int(history[0][2].split("_")[1]) > 120 else False
        except (IndexError, ValueError):
            high_death_flag = False

        t = 1
        for exp in history:
            state = exp[0]
            act = exp[1]
            res_state = exp[2]

            if state not in self.qvalues:
                self.qvalues[state] = [0.0, 0.0]
            if res_state not in self.qvalues:
                self.qvalues[res_state] = [0.0, 0.0]

            # === 方案四：基础存活奖励 + 危险区域惩罚 ===
            try:
                ydif = int(res_state.split("_")[1])
            except (IndexError, ValueError):
                ydif = 100  # 默认安全高度

            # 默认使用存活奖励 self.r[0]（即 +1）
            cur_reward = self.r[0]

            # 危险区域惩罚：抑制贴管飞行
            if ydif < 40:          # 飞得太高（接近上管道）
                cur_reward -= 0.8
            elif ydif > 160:       # 飞得太低（接近地面）
                cur_reward -= 0.8

            # 死亡情况：覆盖为 self.r[1]（-1000）
            if t == 1 or t == 2:
                cur_reward = self.r[1]
            elif high_death_flag and act == 1:
                cur_reward = self.r[1]
                high_death_flag = False

            # Q-learning 更新
            try:
                self.qvalues[state][act] = (1 - self.lr) * self.qvalues[state][act] + \
                                           self.lr * (cur_reward + self.discount * max(self.qvalues[res_state]))
            except (IndexError, TypeError, ValueError) as e:
                print(f"Error updating Q-values for state {state}: {e}")
                self.qvalues[state] = [0.0, 0.0]

            t += 1

        self.gameCNT += 1
        if dump_qvalues:
            self.dump_qvalues()
        self.moves = []
    
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