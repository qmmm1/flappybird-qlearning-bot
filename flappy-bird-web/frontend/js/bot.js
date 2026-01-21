/**
 * Flappy Bird AI Bot 类 - 基于Q-Learning算法
 * 对应Python版本中的bot.py
 */
class Bot {
    constructor() {
        this.gameCNT = 0; // 当前运行的游戏计数，每次死亡后递增
        this.DUMPING_N = 25; // 每隔多少次迭代后保存Q值到本地存储
        this.discount = 1.0;
        this.r = {0: 1, 1: -1000}; // 奖励函数
        this.lr = 0.7;
        this.epsilon = 0.1; // ε-贪婪策略的探索率
        this.useEpsilonGreedy = true;

        this.last_state = "420_240_0";
        this.last_action = 0;
        this.moves = [];

        this.loadQValues();
    }

    /**
     * 设置AI参数
     */
    setParameters(params) {
        if (params.discount !== undefined) {
            this.discount = parseFloat(params.discount);
        }
        if (params.lr !== undefined) {
            this.lr = parseFloat(params.lr);
        }
        if (params.rewardAlive !== undefined && params.rewardDeath !== undefined) {
            this.r = {
                0: parseInt(params.rewardAlive),   // 生存奖励
                1: parseInt(params.rewardDeath)    // 死亡惩罚
            };
        }
        if (params.epsilon !== undefined) {
            this.epsilon = parseFloat(params.epsilon);
        }
        if (params.useEpsilonGreedy !== undefined) {
            this.useEpsilonGreedy = params.useEpsilonGreedy;
        }

        console.log(`AI参数更新: lr=${this.lr}, discount=${this.discount}, reward=${JSON.stringify(this.r)}, epsilon=${this.epsilon}`);
    }

    /**
     * 从本地存储加载Q值
     */
    loadQValues() {
        try {
            const saved = localStorage.getItem('flappyBirdQValues');
            if (saved) {
                this.qvalues = JSON.parse(saved);
                console.log(`加载了${Object.keys(this.qvalues).length}个Q值`);
            } else {
                // 如果本地存储中没有，初始化Q值
                this.qvalues = {};
                // 初始化一些基础状态
                this.qvalues["420_240_0"] = [0.0, 0.0];
                console.log("初始化新的Q值表");
            }
        } catch (error) {
            console.error("加载Q值时出错:", error);
            this.qvalues = {};
            this.qvalues["420_240_0"] = [0.0, 0.0];
        }
    }

    /**
     * 保存Q值到本地存储
     */
    saveQValues(force = false) {
        if (force || this.gameCNT % this.DUMPING_N === 0) {
            try {
                localStorage.setItem('flappyBirdQValues', JSON.stringify(this.qvalues));
                console.log(`Q值已保存到本地存储。游戏计数: ${this.gameCNT}, Q值数量: ${Object.keys(this.qvalues).length}`);
                return true;
            } catch (error) {
                console.error("保存Q值时出错:", error);
                return false;
            }
        }
        return false;
    }

    /**
     * 选择最佳动作（0: 不拍打，1: 拍打）
     */
    act(xdif, ydif, vel) {
        const state = this.mapState(xdif, ydif, vel);

        // 如果状态不存在，初始化它
        if (!this.qvalues[state]) {
            this.qvalues[state] = [0.0, 0.0]; // [不跳跃, 跳跃]
        }

        // 确保Q值是有效的数组
        if (!Array.isArray(this.qvalues[state]) || this.qvalues[state].length < 2) {
            this.qvalues[state] = [0.0, 0.0];
        }

        // 添加到经验历史
        this.moves.push({
            last_state: this.last_state,
            last_action: this.last_action,
            current_state: state
        });

        this.last_state = state;

        // ε-贪婪策略
        if (this.useEpsilonGreedy && Math.random() < this.epsilon) {
            // 探索：随机选择动作
            this.last_action = Math.random() < 0.5 ? 0 : 1;
        } else {
            // 利用：选择Q值最高的动作
            // 平局时选择0-不拍打（与Python版本一致）
            if (this.qvalues[state][0] >= this.qvalues[state][1]) {
                this.last_action = 0;
            } else {
                this.last_action = 1;
            }
        }

        return this.last_action;
    }

    /**
     * 更新Q值 - 修复Q-Learning逻辑，与Python版本保持一致
     */
    updateScores() {
        if (this.moves.length === 0) {
            return;
        }

        const history = [...this.moves].reverse();

        // 检查是否死于上方管道 - 与Python版本逻辑一致
        let highDeathFlag = false;
        try {
            const lastState = history[0].current_state;
            const yPos = parseInt(lastState.split('_')[1]);
            highDeathFlag = yPos > 120;
        } catch (error) {
            highDeathFlag = false;
        }

        // Q-learning 更新 - 与Python版本完全一致
        let t = 1;
        for (const exp of history) {
            const state = exp.last_state;
            const action = exp.last_action;
            const res_state = exp.current_state;

            // 确保状态存在
            if (!this.qvalues[state]) {
                this.qvalues[state] = [0.0, 0.0];
            }
            if (!this.qvalues[res_state]) {
                this.qvalues[res_state] = [0.0, 0.0];
            }

            // 选择奖励 - 与Python版本完全一致
            let cur_reward;
            if (t === 1 || t === 2) {
                // 最后两步的奖励为死亡奖励
                cur_reward = this.r[1];
            } else if (highDeathFlag && action === 1) {
                // 如果死于上方管道且执行了跳跃动作
                cur_reward = this.r[1];
                highDeathFlag = false;
            } else {
                // 其他情况为生存奖励
                cur_reward = this.r[0];
            }

            // 更新Q值 - 使用当前的学习率和折扣因子
            try {
                this.qvalues[state][action] = (1 - this.lr) * this.qvalues[state][action] +
                    this.lr * (cur_reward + this.discount * Math.max(...this.qvalues[res_state]));
            } catch (error) {
                console.error(`更新Q值时出错 (状态: ${state}):`, error);
                this.qvalues[state] = [0.0, 0.0];
            }

            t++;
        }

        this.gameCNT++;
        this.saveQValues();
        this.moves = []; // 清空历史
    }

    /**
     * 映射状态 (xdif, ydif, vel) 到离散状态字符串
     * 与Python版本完全一致，包括负数处理
     */
    mapState(xdif, ydif, vel) {
        // 与Python版本完全一致的离散化逻辑
        let discretizedXdif;
        if (xdif < 140) {
            // 对于小于140的值，向下取整到10的倍数
            discretizedXdif = Math.floor(xdif) - (Math.floor(xdif) % 10);
        } else {
            // 对于大于等于140的值，向下取整到70的倍数
            discretizedXdif = Math.floor(xdif) - (Math.floor(xdif) % 70);
        }

        let discretizedYdif;
        if (ydif < 180) {
            // 对于小于180的值，向下取整到10的倍数
            discretizedYdif = Math.floor(ydif) - (Math.floor(ydif) % 10);
        } else {
            // 对于大于等于180的值，向下取整到60的倍数
            discretizedYdif = Math.floor(ydif) - (Math.floor(ydif) % 60);
        }

        // 确保值与Python版本一致（负数的处理）
        discretizedXdif = Math.floor(discretizedXdif);
        discretizedYdif = Math.floor(discretizedYdif);
        const discretizedVel = Math.floor(vel);

        return `${discretizedXdif}_${discretizedYdif}_${discretizedVel}`;
    }

    /**
     * 重置Bot状态（不清除Q值）
     */
    reset() {
        this.last_state = "420_240_0";
        this.last_action = 0;
        this.moves = [];
        this.gameCNT = 0;
    }

    /**
     * 初始化Q值表（创建初始状态）
     */
    initializeQValues() {
        console.log("开始初始化Q值...");
        this.qvalues = {};

        // 与Python版本完全相同的状态空间
        // X范围: [-40,-30...120] U [140, 210 ... 490]
        // Y范围: [-300, -290 ... 160] U [180, 240 ... 420]
        // 速度范围: [-10, 11)

        // 创建X值数组
        const xValues = [];
        for (let x = -40; x < 140; x += 10) xValues.push(x);
        for (let x = 140; x <= 490; x += 70) xValues.push(x);

        // 创建Y值数组
        const yValues = [];
        for (let y = -300; y < 180; y += 10) yValues.push(y);
        for (let y = 180; y <= 420; y += 60) yValues.push(y);

        // 创建速度值数组
        const vValues = [];
        for (let v = -10; v < 11; v++) vValues.push(v);

        // 生成所有状态组合
        let count = 0;
        for (const x of xValues) {
            for (const y of yValues) {
                for (const v of vValues) {
                    const state = `${x}_${y}_${v}`;
                    this.qvalues[state] = [0.0, 0.0];
                    count++;
                }
            }
        }

        console.log(`初始化完成，创建了${count}个状态`);
        this.saveQValues(true);
        return count;
    }

    /**
     * 获取Q值表信息
     */
    getQValuesInfo() {
        const totalStates = Object.keys(this.qvalues).length;
        const nonZeroStates = Object.values(this.qvalues).filter(v => v[0] !== 0 || v[1] !== 0).length;

        return {
            totalStates,
            nonZeroStates,
            gameCount: this.gameCNT
        };
    }

    /**
     * 获取当前参数
     */
    getParameters() {
        return {
            discount: this.discount,
            lr: this.lr,
            rewardAlive: this.r[0],
            rewardDeath: this.r[1],
            epsilon: this.epsilon,
            useEpsilonGreedy: this.useEpsilonGreedy,
            gameCount: this.gameCNT
        };
    }

    /**
     * 导出Q值为JSON字符串
     */
    exportQValues() {
        return JSON.stringify(this.qvalues, null, 2);
    }

    /**
     * 从JSON字符串导入Q值
     */
    importQValues(jsonString) {
        try {
            const imported = JSON.parse(jsonString);
            if (typeof imported === 'object' && imported !== null) {
                this.qvalues = imported;
                this.saveQValues(true);
                return true;
            }
            return false;
        } catch (error) {
            console.error("导入Q值时出错:", error);
            return false;
        }
    }

    /**
     * 清空Q值
     */
    clearQValues() {
        this.qvalues = {};
        this.qvalues["420_240_0"] = [0.0, 0.0];
        this.gameCNT = 0;
        this.saveQValues(true);
        console.log("Q值已清空");
    }
}