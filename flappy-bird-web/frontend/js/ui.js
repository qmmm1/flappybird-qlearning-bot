/**
 * 用户界面管理
 * 处理UI交互和控制逻辑
 */
class UIManager {
    constructor() {
        this.bot = null;
        this.game = null;
        this.isTraining = false;
        this.isPaused = false;
        this.startTime = null;
        this.trainingTimer = null;

        this.scores = {
            current: 0,
            best: 0,
            max: 0,
            avg: 0,
            totalGames: 0,
            totalScore: 0
        };

        this.init();
    }

    /**
     * 初始化UI
     */
    init() {
        // 初始化Bot和Game
        this.bot = new Bot();
        this.game = new FlappyBirdGame('game-canvas', this.bot, true);

        // 设置游戏回调
        this.game.setCallbacks({
            onGameOver: this.onGameOver.bind(this),
            onTrainingProgress: this.onTrainingProgress.bind(this),
            onTrainingComplete: this.onTrainingComplete.bind(this)
        });

        // 绑定UI事件
        this.bindEvents();

        // 更新初始状态
        this.updateUI();
        this.updateStats();

        // 添加初始控制台消息
        this.addConsoleMessage('Flappy Bird AI 前端训练平台已启动', 'info');
        this.addConsoleMessage('选择训练模式并设置参数，然后点击"开始训练"', 'info');

        // 更新时间戳
        this.updateTimestamp();
    }

    /**
     * 绑定UI事件
     */
    bindEvents() {
        // 训练控制按钮
        document.getElementById('start-btn').addEventListener('click', () => this.startTraining());
        document.getElementById('pause-btn').addEventListener('click', () => this.pauseTraining());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopTraining());
        document.getElementById('reset-btn').addEventListener('click', () => this.resetTraining());

        // 游戏控制按钮
        document.getElementById('start-game-btn').addEventListener('click', () => this.startSingleGame());
        document.getElementById('restart-game-btn').addEventListener('click', () => this.continueTraining());
        document.getElementById('flap-btn').addEventListener('click', () => {
            if (this.game && this.game.player && this.game.player.alive) {
                this.game.flap();
            }
        });
        document.getElementById('toggle-sound').addEventListener('click', () => this.toggleSound());

        // 控制台按钮
        document.getElementById('clear-console').addEventListener('click', () => this.clearConsole());
        document.getElementById('copy-console').addEventListener('click', () => this.copyConsole());
        document.getElementById('send-command').addEventListener('click', () => this.sendCommand());
        document.getElementById('console-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCommand();
        });

        // 底部链接
        document.getElementById('help-link').addEventListener('click', (e) => {
            e.preventDefault();
            this.showHelp();
        });

        document.getElementById('download-qvalues').addEventListener('click', (e) => {
            e.preventDefault();
            this.downloadQValues();
        });

        // 键盘控制
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.game && this.game.player && this.game.player.alive) {
                e.preventDefault();
                this.game.flap();
            }
        });
    }

    /**
     * 开始训练
     */
    async startTraining() {
        const mode = document.getElementById('function-select').value;

        if (mode === 'initialize_qvalues') {
            this.initializeQValues();
            return;
        }

        if (this.isTraining) {
            this.addConsoleMessage('训练已在运行中', 'warning');
            return;
        }

        // 获取所有参数
        const iterations = parseInt(document.getElementById('iterations').value) || 1000;
        const displayFreq = parseInt(document.getElementById('display-freq').value) || 10;
        const fps = parseInt(document.getElementById('fps').value) || 60;
        const verbose = document.getElementById('verbose').checked;

        // 获取新的AI参数
        const learningRate = parseFloat(document.getElementById('learning-rate').value) || 0.7;
        const discountFactor = parseFloat(document.getElementById('discount-factor').value) || 1.0;
        const rewardAlive = parseInt(document.getElementById('reward-alive').value) || 1;
        const rewardDeath = parseInt(document.getElementById('reward-death').value) || -1000;
        const explorationRate = parseFloat(document.getElementById('exploration-rate').value) || 0.1;
        const useEpsilon = document.getElementById('use-epsilon').checked;

        // 更新Bot参数
        this.bot.setParameters({
            lr: learningRate,
            discount: discountFactor,
            rewardAlive: rewardAlive,
            rewardDeath: rewardDeath,
            epsilon: explorationRate,
            useEpsilonGreedy: useEpsilon
        });

        // 更新游戏设置
        this.game.fps = fps;
        this.game.frameTime = 1000 / fps;
        this.game.verbose = verbose;

        // 隐藏欢迎界面
        this.hideWelcomeScreen();

        // 更新UI状态
        this.isTraining = true;
        this.isPaused = false;
        this.startTime = Date.now();

        document.getElementById('start-btn').disabled = true;
        document.getElementById('pause-btn').disabled = false;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('reset-btn').disabled = true;

        // 重置统计数据
        this.resetStats();

        // 添加控制台消息，显示参数设置
        this.addConsoleMessage(`开始训练: ${iterations} 次迭代`, 'info');
        this.addConsoleMessage(`参数: lr=${learningRate}, γ=${discountFactor}, ε=${explorationRate}`, 'info');
        this.addConsoleMessage(`奖励: 生存=${rewardAlive}, 死亡=${rewardDeath}, ε-贪婪=${useEpsilon ? '是' : '否'}`, 'info');

        // 开始训练
        await this.game.startTraining(iterations, displayFreq);

        // 开始训练计时器
        this.startTrainingTimer();

        // 更新状态
        this.updateStatus('training', '训练中');
    }

    /**
     * 暂停训练
     */
    pauseTraining() {
        if (!this.isTraining) return;

        if (this.isPaused) {
            // 继续训练
            this.game.resume();
            this.isPaused = false;
            document.getElementById('pause-btn').innerHTML = '<i class="fas fa-pause"></i> 暂停';
            this.addConsoleMessage('训练继续', 'info');
            this.updateStatus('training', '训练中');
        } else {
            // 暂停训练
            this.game.pause();
            this.isPaused = true;
            document.getElementById('pause-btn').innerHTML = '<i class="fas fa-play"></i> 继续';
            this.addConsoleMessage('训练暂停', 'warning');
            this.updateStatus('paused', '已暂停');
        }
    }

    /**
     * 停止训练
     */
    stopTraining() {
        if (!this.isTraining) return;

        this.isTraining = false;
        this.isPaused = false;

        // 停止游戏训练
        this.game.stopTraining();

        clearInterval(this.trainingTimer);

        // 更新UI状态
        document.getElementById('start-btn').disabled = false;
        document.getElementById('pause-btn').disabled = true;
        document.getElementById('stop-btn').disabled = true;
        document.getElementById('reset-btn').disabled = false;
        document.getElementById('pause-btn').innerHTML = '<i class="fas fa-pause"></i> 暂停';

        // 添加控制台消息
        this.addConsoleMessage(`训练停止。完成 ${this.scores.totalGames} 次迭代`, 'info');

        // 显示欢迎界面
        this.showWelcomeScreen();

        this.updateStatus('ready', '准备就绪');
    }

    /**
     * 重置训练
     */
    resetTraining() {
        if (this.isTraining) {
            if (!confirm('训练正在进行中，确定要重置吗？')) {
                return;
            }
            this.stopTraining();
        }

        // 重置Bot
        this.bot.clearQValues();

        // 重置游戏
        this.game.resetGame();

        // 重置统计数据
        this.resetStats();

        // 添加控制台消息
        this.addConsoleMessage('训练已重置，Q值已清空', 'success');

        // 更新UI
        this.updateUI();

        // 显示欢迎界面
        this.showWelcomeScreen();
    }

    /**
     * 初始化Q值
     */
    initializeQValues() {
        if (this.isTraining) {
            this.addConsoleMessage('请先停止训练再初始化Q值', 'warning');
            return;
        }

        if (!confirm('这将初始化Q值表，确定要继续吗？')) {
            return;
        }

        this.addConsoleMessage('开始初始化Q值表...', 'info');

        try {
            const count = this.bot.initializeQValues();
            this.addConsoleMessage(`Q值表初始化完成，创建了 ${count} 个状态`, 'success');
            this.updateQValuesCount();
        } catch (error) {
            this.addConsoleMessage(`初始化Q值时出错: ${error.message}`, 'error');
        }
    }

    /**
     * 开始单次游戏演示
     */
    startSingleGame() {
        this.hideWelcomeScreen();
        this.game.resetGame();
        this.game.start();
    }

    /**
     * 继续训练（从游戏结束界面）
     */
    continueTraining() {
        this.hideGameOverScreen();

        if (this.isTraining) {
            // 游戏已经自动继续训练，不需要额外操作
        } else {
            this.showWelcomeScreen();
        }
    }

    /**
     * 游戏结束回调
     */
    onGameOver(data) {
        // 更新统计数据
        this.scores.current = data.score;
        this.scores.totalGames = this.game.currentIteration;
        this.scores.totalScore += data.score;

        // 更新最高分
        if (data.score > this.scores.max) {
            this.scores.max = data.score;
        }

        // 计算平均分
        this.scores.avg = this.scores.totalGames > 0 ?
            (this.scores.totalScore / this.scores.totalGames).toFixed(1) : 0;

        // 更新UI
        this.updateStats();

        // 显示游戏结束界面
        if (this.game.display) {
            this.showGameOverScreen(data.score);
        }

        // 添加控制台消息
        if (this.game.verbose) {
            this.addConsoleMessage(`迭代 ${this.game.currentIteration} | 分数: ${data.score}`, 'info');
        }
    }

    /**
     * 训练进度回调
     */
    onTrainingProgress(data) {
        this.scores.current = data.score;
        this.scores.totalGames = data.iteration;
        this.scores.totalScore += data.score;

        if (data.score > this.scores.max) {
            this.scores.max = data.score;
        }

        this.scores.avg = this.scores.totalGames > 0 ?
            (this.scores.totalScore / this.scores.totalGames).toFixed(1) : 0;

        this.updateStats();

        // 每100次迭代输出一次进度
        if (data.iteration % 100 === 0 && this.game.verbose) {
            this.addConsoleMessage(`进度: ${data.iteration}/${data.totalIterations}, 当前分数: ${data.score}, 最高分: ${this.scores.max}`, 'info');
        }
    }

    /**
     * 训练完成回调
     */
    onTrainingComplete() {
        this.isTraining = false;
        this.isPaused = false;

        clearInterval(this.trainingTimer);

        // 更新UI状态
        document.getElementById('start-btn').disabled = false;
        document.getElementById('pause-btn').disabled = true;
        document.getElementById('stop-btn').disabled = true;
        document.getElementById('reset-btn').disabled = false;

        // 保存最终Q值
        this.bot.saveQValues(true);

        this.addConsoleMessage(`训练完成！总共 ${this.scores.totalGames} 次迭代，最高分数: ${this.scores.max}，平均分数: ${this.scores.avg}`, 'success');

        // 更新Q值数量
        this.updateQValuesCount();

        // 显示欢迎界面
        this.showWelcomeScreen();

        this.updateStatus('ready', '准备就绪');
    }

    /**
     * 更新统计数据UI
     */
    updateStats() {
        document.getElementById('current-iter').textContent = this.scores.totalGames;
        document.getElementById('max-score').textContent = this.scores.max;
        document.getElementById('avg-score').textContent = this.scores.avg;
        document.getElementById('current-score').textContent = this.scores.current;
        document.getElementById('best-score').textContent = this.scores.best;

        // 更新训练时间
        if (this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            document.getElementById('training-time').textContent =
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        // 更新进度条
        if (this.game.totalIterations > 0) {
            const progress = (this.scores.totalGames / this.game.totalIterations) * 100;
            document.getElementById('progress-fill').style.width = `${Math.min(progress, 100)}%`;
            document.getElementById('progress-text').textContent = `${Math.round(progress)}%`;
        }

        // 更新Q值数量
        this.updateQValuesCount();
    }

    /**
     * 更新Q值数量显示
     */
    updateQValuesCount() {
        if (this.bot) {
            const info = this.bot.getQValuesInfo();
            document.getElementById('qvalues-count').textContent = info.totalStates;
        }
    }

    /**
     * 重置统计数据
     */
    resetStats() {
        this.scores = {
            current: 0,
            best: 0,
            max: 0,
            avg: 0,
            totalGames: 0,
            totalScore: 0
        };

        this.startTime = Date.now();
        this.updateStats();
    }

    /**
     * 更新状态指示器
     */
    updateStatus(type, text) {
        const statusElement = document.getElementById('game-status');

        switch (type) {
            case 'training':
                statusElement.className = 'status-ready';
                statusElement.innerHTML = `<i class="fas fa-play"></i> ${text}`;
                break;
            case 'paused':
                statusElement.className = 'status-ready';
                statusElement.innerHTML = `<i class="fas fa-pause"></i> ${text}`;
                break;
            case 'ready':
                statusElement.className = 'status-ready';
                statusElement.innerHTML = `<i class="fas fa-play"></i> ${text}`;
                break;
            default:
                statusElement.className = 'status-ready';
                statusElement.innerHTML = `<i class="fas fa-play"></i> 准备就绪`;
        }
    }

    /**
     * 切换声音
     */
    toggleSound() {
        const soundBtn = document.getElementById('toggle-sound');
        const icon = soundBtn.querySelector('i');

        if (icon.classList.contains('fa-volume-up')) {
            icon.className = 'fas fa-volume-mute';
            soundBtn.innerHTML = '<i class="fas fa-volume-mute"></i> 静音';
            this.addConsoleMessage('声音已关闭', 'info');
        } else {
            icon.className = 'fas fa-volume-up';
            soundBtn.innerHTML = '<i class="fas fa-volume-up"></i> 声音';
            this.addConsoleMessage('声音已开启', 'info');
        }
    }

    /**
     * 添加控制台消息
     */
    addConsoleMessage(message, type = 'info') {
        const consoleOutput = document.getElementById('console-output');
        const timestamp = new Date().toLocaleTimeString('en-GB', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        const messageElement = document.createElement('div');
        messageElement.className = `console-message ${type}`;
        messageElement.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message">${message}</span>
        `;

        consoleOutput.appendChild(messageElement);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    /**
     * 清空控制台
     */
    clearConsole() {
        const consoleOutput = document.getElementById('console-output');
        consoleOutput.innerHTML = '';
        this.addConsoleMessage('控制台已清空', 'info');
    }

    /**
     * 复制控制台内容
     */
    copyConsole() {
        const consoleOutput = document.getElementById('console-output');
        const text = consoleOutput.innerText;

        navigator.clipboard.writeText(text).then(() => {
            this.addConsoleMessage('控制台内容已复制到剪贴板', 'success');
        }).catch(err => {
            this.addConsoleMessage(`复制失败: ${err.message}`, 'error');
        });
    }

    /**
     * 发送控制台命令
     */
    sendCommand() {
        const input = document.getElementById('console-input');
        const command = input.value.trim();

        if (!command) return;

        // 添加命令到控制台
        this.addConsoleMessage(`> ${command}`, 'info');

        // 处理命令
        this.processCommand(command);

        // 清空输入框
        input.value = '';
    }

    /**
     * 处理控制台命令
     */
    processCommand(command) {
        const parts = command.toLowerCase().split(' ');
        const cmd = parts[0];
        const args = parts.slice(1);

        switch (cmd) {
            case 'help':
                this.showCommandHelp();
                break;
            case 'status':
                this.showStatus();
                break;
            case 'reset':
                this.resetTraining();
                break;
            case 'start':
                this.startTraining();
                break;
            case 'stop':
                this.stopTraining();
                break;
            case 'pause':
                this.pauseTraining();
                break;
            case 'init':
                this.initializeQValues();
                break;
            case 'clear':
                this.clearConsole();
                break;
            case 'save':
                this.bot.saveQValues(true);
                this.addConsoleMessage('Q值已保存', 'success');
                break;
            case 'load':
                this.bot.loadQValues();
                this.addConsoleMessage('Q值已重新加载', 'success');
                this.updateQValuesCount();
                break;
            case 'stats':
                this.showDetailedStats();
                break;
            case 'params':
                this.showCurrentParameters();
                break;
            default:
                this.addConsoleMessage(`未知命令: ${cmd}。输入 help 查看可用命令。`, 'error');
        }
    }

    /**
     * 显示命令帮助
     */
    showCommandHelp() {
        const helpText = `
可用命令:
- help: 显示此帮助信息
- status: 显示训练状态
- params: 显示当前AI参数
- start: 开始训练
- stop: 停止训练
- pause: 暂停/继续训练
- reset: 重置训练
- init: 初始化Q值
- save: 保存Q值
- load: 重新加载Q值
- stats: 显示详细统计
- clear: 清空控制台
        `.trim();

        this.addConsoleMessage(helpText, 'info');
    }

    /**
     * 显示状态信息
     */
    showStatus() {
        const info = this.bot.getQValuesInfo();
        const params = this.bot.getParameters();
        const status = this.isTraining ? '训练中' : (this.isPaused ? '已暂停' : '未训练');

        const statusText = `
训练状态: ${status}
游戏计数: ${info.gameCount}
Q值总数: ${info.totalStates}
非零状态: ${info.nonZeroStates}
当前分数: ${this.scores.current}
最高分数: ${this.scores.max}
平均分数: ${this.scores.avg}
        `.trim();

        this.addConsoleMessage(statusText, 'info');
    }

    /**
     * 显示当前AI参数
     */
    showCurrentParameters() {
        const params = this.bot.getParameters();

        const paramsText = `
当前AI参数:
==========
学习率(α): ${params.lr}
折扣因子(γ): ${params.discount}
生存奖励: ${params.rewardAlive}
死亡惩罚: ${params.rewardDeath}
探索概率(ε): ${params.epsilon}
ε-贪婪策略: ${params.useEpsilonGreedy ? '启用' : '禁用'}
游戏计数: ${params.gameCount}
        `.trim();

        this.addConsoleMessage(paramsText, 'info');
    }

    /**
     * 显示详细统计
     */
    showDetailedStats() {
        const info = this.bot.getQValuesInfo();
        const params = this.bot.getParameters();

        const statsText = `
训练统计:
==========
总迭代次数: ${this.scores.totalGames}
当前分数: ${this.scores.current}
最高分数: ${this.scores.max}
平均分数: ${this.scores.avg}
总得分: ${this.scores.totalScore}

Q值信息:
==========
总状态数: ${info.totalStates}
非零状态: ${info.nonZeroStates}
游戏计数: ${info.gameCount}
训练模式: ${this.game.trainingMode ? '开启' : '关闭'}

AI参数:
==========
学习率(α): ${params.lr}
折扣因子(γ): ${params.discount}
生存奖励: ${params.rewardAlive}
死亡惩罚: ${params.rewardDeath}
探索概率(ε): ${params.epsilon}
ε-贪婪策略: ${params.useEpsilonGreedy ? '启用' : '禁用'}
        `.trim();

        this.addConsoleMessage(statsText, 'info');
    }

    /**
     * 显示帮助信息
     */
    showHelp() {
        const helpText = `
Flappy Bird AI 训练平台帮助
===========================

1. 训练模式:
   - "训练并显示": 正常训练并显示游戏画面
   - "初始化Q值": 创建初始Q值表

2. 参数设置:
   - 迭代次数: 训练的总次数
   - 显示频率: 每N次显示一次游戏画面
   - FPS帧率: 游戏运行的帧率
   - 学习率(α): Q-learning的学习率 (0.01-1)
   - 折扣因子(γ): 未来奖励的折扣 (0.1-1)
   - 生存奖励: 每存活一帧的奖励值
   - 死亡惩罚: 撞到管道/地面的惩罚值
   - 探索概率(ε): ε-贪婪策略的探索率 (0-1)
   - 详细输出: 在控制台显示详细信息
   - 使用ε-贪婪策略: 是否使用探索策略

3. 操作控制:
   - 开始训练: 开始AI训练
   - 暂停: 暂停/继续训练
   - 停止: 停止训练
   - 重置训练: 重置所有统计数据

4. 游戏控制:
   - 空格键或点击"拍打翅膀": 控制小鸟跳跃
   - 声音按钮: 切换声音开关

5. 控制台命令:
   - 输入 help 查看可用命令

参数调整建议:
============
- 学习率较高(0.5-0.9): 快速学习但可能不稳定
- 学习率较低(0.1-0.3): 稳定学习但较慢
- 折扣因子接近1: 重视长期奖励
- ε值较高(0.1-0.3): 更多探索，适合早期训练
- ε值较低(0-0.1): 更多利用，适合后期训练
- 生存奖励/死亡惩罚: 调整相对值影响学习偏好
        `.trim();

        this.addConsoleMessage(helpText, 'info');
    }

    /**
     * 下载Q值
     */
    downloadQValues() {
        const qvaluesJson = this.bot.exportQValues();
        const blob = new Blob([qvaluesJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `qvalues_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.addConsoleMessage('Q值已导出为JSON文件', 'success');
    }

    /**
     * 隐藏欢迎界面
     */
    hideWelcomeScreen() {
        const overlay = document.getElementById('game-overlay');
        const welcomeScreen = document.getElementById('welcome-screen');

        overlay.classList.remove('active');
        welcomeScreen.classList.remove('active');
    }

    /**
     * 显示欢迎界面
     */
    showWelcomeScreen() {
        const overlay = document.getElementById('game-overlay');
        const welcomeScreen = document.getElementById('welcome-screen');
        const gameOverScreen = document.getElementById('game-over-screen');

        gameOverScreen.classList.remove('active');
        welcomeScreen.classList.add('active');
        overlay.classList.add('active');
    }

    /**
     * 显示游戏结束界面
     */
    showGameOverScreen(score) {
        const overlay = document.getElementById('game-overlay');
        const welcomeScreen = document.getElementById('welcome-screen');
        const gameOverScreen = document.getElementById('game-over-screen');
        const finalScore = document.getElementById('final-score');

        finalScore.textContent = score;
        welcomeScreen.classList.remove('active');
        gameOverScreen.classList.add('active');
        overlay.classList.add('active');
    }

    /**
     * 隐藏游戏结束界面
     */
    hideGameOverScreen() {
        const overlay = document.getElementById('game-overlay');
        const gameOverScreen = document.getElementById('game-over-screen');

        gameOverScreen.classList.remove('active');
        overlay.classList.remove('active');
    }

    /**
     * 开始训练计时器
     */
    startTrainingTimer() {
        clearInterval(this.trainingTimer);

        this.trainingTimer = setInterval(() => {
            if (this.startTime) {
                this.updateStats();
            }
        }, 1000);
    }

    /**
     * 更新时间戳
     */
    updateTimestamp() {
        const now = new Date();
        const timestamp = now.toLocaleTimeString('en-GB', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        const timestampElements = document.querySelectorAll('.timestamp');
        if (timestampElements[0]) {
            timestampElements[0].textContent = `[${timestamp}]`;
        }
    }

    /**
     * 更新UI元素状态
     */
    updateUI() {
        this.updateQValuesCount();
        this.updateTimestamp();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.uiManager = new UIManager();
});