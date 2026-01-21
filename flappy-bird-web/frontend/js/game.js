/**
 * Flappy Bird 游戏引擎
 * 对应Python版本中的train_with_display.py
 */
class FlappyBirdGame {
    constructor(canvasId, bot, display = true) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.bot = bot;
        this.display = display;

        // 游戏常量 - 与Python版本完全一致
        this.SCREENWIDTH = 288;
        this.SCREENHEIGHT = 512;
        this.PIPEGAPSIZE = 100;
        this.BASEY = this.SCREENHEIGHT * 0.79;

        // 图片尺寸 - 与Python版本完全一致
        this.IM_WIDTH = 0;
        this.IM_HEIGTH = 1;
        this.PIPE = [52, 320];
        this.PLAYER = [34, 24];
        this.BASE = [336, 112];
        this.BACKGROUND = [288, 512];

        // 游戏状态
        this.score = 0;
        this.bestScore = 0;
        this.gameRunning = false;
        this.gamePaused = false;
        this.trainingMode = false;
        this.currentIteration = 0;
        this.totalIterations = 1000;
        this.displayFrequency = 10;
        this.verbose = true;

        // 游戏对象
        this.player = null;
        this.pipes = [];
        this.base = null;

        // 游戏资源
        this.images = {};
        this.sounds = {};
        this.hitmasks = {};

        // 游戏循环控制
        this.lastTime = 0;
        this.accumulator = 0;
        this.fps = 60;
        this.frameTime = 1000 / this.fps;
        this.animationId = null;

        // 玩家动画
        this.playerIndex = 0;
        this.playerIndexCycle = [0, 1, 2, 1];
        this.playerCycleIndex = 0;

        // 训练控制
        this.isTraining = false;
        this.shouldStopTraining = false;

        // 初始化游戏
        this.init();
    }

    /**
     * 初始化游戏
     */
    init() {
        // 设置画布尺寸
        this.canvas.width = this.SCREENWIDTH;
        this.canvas.height = this.SCREENHEIGHT;

        // 加载资源
        this.loadResources();

        // 初始化游戏对象
        this.resetGame();
    }

    /**
     * 加载游戏资源
     */
    loadResources() {
        // 加载数字图片
        this.images.numbers = [];
        for (let i = 0; i < 10; i++) {
            const img = new Image();
            img.src = `assets/sprites/${i}.png`;
            this.images.numbers.push(img);
        }

        // 加载其他图片
        this.images.gameover = new Image();
        this.images.gameover.src = 'assets/sprites/gameover.png';

        this.images.message = new Image();
        this.images.message.src = 'assets/sprites/message.png';

        this.images.base = new Image();
        this.images.base.src = 'assets/sprites/base.png';

        // 如果显示模式，加载更多资源
        if (this.display) {
            this.images.background = new Image();
            this.images.background.src = 'assets/sprites/background-day.png';

            this.images.player = [
                new Image(),
                new Image(),
                new Image()
            ];
            this.images.player[0].src = 'assets/sprites/redbird-upflap.png';
            this.images.player[1].src = 'assets/sprites/redbird-midflap.png';
            this.images.player[2].src = 'assets/sprites/redbird-downflap.png';

            this.images.pipe = [
                new Image(),
                new Image()
            ];
            this.images.pipe[0].src = 'assets/sprites/pipe-green.png'; // 上管道
            this.images.pipe[1].src = 'assets/sprites/pipe-green.png'; // 下管道

            // 加载声音
            this.sounds.die = new Audio('assets/audio/die.wav');
            this.sounds.hit = new Audio('assets/audio/hit.wav');
            this.sounds.point = new Audio('assets/audio/point.wav');
            this.sounds.swoosh = new Audio('assets/audio/swoosh.wav');
            this.sounds.wing = new Audio('assets/audio/wing.wav');
        }

        // 加载碰撞掩码（简化版本）
        this.loadHitmasks();
    }

    /**
     * 加载碰撞掩码（简化版本）
     */
    loadHitmasks() {
        // 玩家碰撞掩码（简化：假设整个矩形区域）
        this.hitmasks = {
            player: [
                this.createRectHitmask(this.PLAYER[0], this.PLAYER[1]),
                this.createRectHitmask(this.PLAYER[0], this.PLAYER[1]),
                this.createRectHitmask(this.PLAYER[0], this.PLAYER[1])
            ],
            pipe: [
                this.createRectHitmask(this.PIPE[0], this.PIPE[1]),
                this.createRectHitmask(this.PIPE[0], this.PIPE[1])
            ]
        };
    }

    /**
     * 创建矩形碰撞掩码
     */
    createRectHitmask(width, height) {
        const mask = [];
        for (let x = 0; x < width; x++) {
            mask[x] = [];
            for (let y = 0; y < height; y++) {
                // 简化：整个矩形区域都有碰撞
                mask[x][y] = true;
            }
        }
        return mask;
    }

    /**
     * 重置游戏状态
     */
    resetGame() {
        this.score = 0;

        // 玩家初始位置 - 与Python版本完全一致
        this.player = {
            x: this.SCREENWIDTH * 0.2,
            y: this.SCREENHEIGHT * 0.5,
            width: this.PLAYER[0],
            height: this.PLAYER[1],
            velocityY: 0,
            flapAcc: -9,
            accY: 1,
            maxVelY: 10,
            minVelY: -8,
            flapped: false,
            alive: true,
            index: 0
        };

        // 管道 - 与Python版本完全一致
        this.pipes = [];
        const pipe1 = this.getRandomPipe();
        const pipe2 = this.getRandomPipe();

        this.pipes.push({
            upper: {x: this.SCREENWIDTH + 200, y: pipe1.upper.y},
            lower: {x: this.SCREENWIDTH + 200, y: pipe1.lower.y}
        });

        this.pipes.push({
            upper: {x: this.SCREENWIDTH + 200 + (this.SCREENWIDTH / 2), y: pipe2.upper.y},
            lower: {x: this.SCREENWIDTH + 200 + (this.SCREENWIDTH / 2), y: pipe2.lower.y}
        });

        // 地面
        this.base = {
            x: 0,
            y: this.BASEY,
            width: this.BASE[0],
            height: this.BASE[1]
        };

        // 动画状态
        this.playerIndex = 0;
        this.playerCycleIndex = 0;

        // 游戏状态
        this.gameRunning = true;
        this.gamePaused = false;
    }

    /**
     * 开始游戏
     */
    start() {
        if (!this.gameRunning) {
            this.resetGame();
        }
        this.gamePaused = false;
        this.lastTime = performance.now();
        this.gameLoop();
    }

    /**
     * 暂停游戏
     */
    pause() {
        this.gamePaused = true;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    /**
     * 继续游戏
     */
    resume() {
        if (this.gamePaused) {
            this.gamePaused = false;
            this.lastTime = performance.now();
            this.gameLoop();
        }
    }

    /**
     * 停止游戏
     */
    stop() {
        this.gameRunning = false;
        this.gamePaused = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    /**
     * 游戏主循环
     */
    gameLoop(currentTime = performance.now()) {
        if (!this.gameRunning || this.gamePaused) return;

        this.animationId = requestAnimationFrame((time) => this.gameLoop(time));

        const deltaTime = currentTime - this.lastTime;
        this.lastTime = currentTime;

        // 固定时间步长更新
        this.accumulator += deltaTime;
        while (this.accumulator >= this.frameTime) {
            this.update(this.frameTime / 1000);
            this.accumulator -= this.frameTime;
        }

        if (this.display) {
            this.render();
        }
    }

    /**
     * 更新游戏状态
     */
    update(dt) {
        if (!this.player.alive) return;

        // AI决策 - 与Python版本完全一致
        if (this.trainingMode && this.bot) {
            let targetPipe;
            if (-this.player.x + this.pipes[0].lower.x > -30) {
                targetPipe = this.pipes[0];
            } else {
                targetPipe = this.pipes[1];
            }

            const xdif = -this.player.x + targetPipe.lower.x;
            const ydif = -this.player.y + targetPipe.lower.y;
            const vel = this.player.velocityY;

            if (this.bot.act(xdif, ydif, vel)) {
                this.flap();
            }
        }

        // 更新玩家
        this.updatePlayer(dt);

        // 更新管道
        this.updatePipes(dt);

        // 碰撞检测
        const collision = this.checkCollision();
        if (collision.crashed) {
            this.handleCrash(collision);
            return;
        }

        // 计分
        this.updateScore();

        // 更新动画
        this.updateAnimation(dt);
    }

    /**
     * 更新玩家状态 - 修复物理逻辑
     */
    updatePlayer(dt) {
        // 重力 - 与Python版本完全一致
        if (this.player.velocityY < this.player.maxVelY && !this.player.flapped) {
            this.player.velocityY += this.player.accY;
        }

        if (this.player.flapped) {
            this.player.flapped = false;
        }

        // 更新位置 - 修复：确保不会穿过地面
        const playerHeight = this.display ? this.images.player[0].height : this.PLAYER[1];
        const maxY = this.BASEY - playerHeight;

        // 与Python版本完全一致：使用min函数限制下落速度
        const velocity = Math.min(this.player.velocityY, maxY - this.player.y);
        this.player.y += velocity;

        // 确保不会飞出屏幕顶部
        if (this.player.y < 0) {
            this.player.y = 0;
            this.player.velocityY = 0;
        }
    }

    /**
     * 更新管道
     */
    updatePipes(dt) {
        const pipeVelX = -4;

        // 移动管道
        for (const pipe of this.pipes) {
            pipe.upper.x += pipeVelX;
            pipe.lower.x += pipeVelX;
        }

        // 添加新管道 - 与Python版本完全一致
        if (0 < this.pipes[0].upper.x && this.pipes[0].upper.x < 5) {
            const newPipe = this.getRandomPipe();
            this.pipes.push({
                upper: {x: newPipe.upper.x, y: newPipe.upper.y},
                lower: {x: newPipe.lower.x, y: newPipe.lower.y}
            });
        }

        // 移除屏幕外的管道
        const pipeWidth = this.display ? this.images.pipe[0].width : this.PIPE[0];
        if (this.pipes[0].upper.x < -pipeWidth) {
            this.pipes.shift();
        }
    }

    /**
     * 更新分数
     */
    updateScore() {
        const playerMidPos = this.player.x + this.PLAYER[0] / 2;

        for (const pipe of this.pipes) {
            const pipeMidPos = pipe.upper.x + this.PIPE[0] / 2;

            if (pipeMidPos <= playerMidPos && playerMidPos < pipeMidPos + 4) {
                this.score++;
                if (this.display && this.sounds.point) {
                    this.sounds.point.currentTime = 0;
                    this.sounds.point.play();
                }

                // 更新最高分
                if (this.score > this.bestScore) {
                    this.bestScore = this.score;
                }
                break;
            }
        }
    }

    /**
     * 更新动画
     */
    updateAnimation(dt) {
        // 玩家拍打动画 - 与Python版本完全一致
        this.playerCycleIndex = (this.playerCycleIndex + 1) % 30;
        if ((this.playerCycleIndex + 1) % 3 === 0) {
            const nextIndex = Math.floor((this.playerCycleIndex + 1) / 3) % 4;
            this.playerIndex = this.playerIndexCycle[nextIndex];
        }

        // 地面移动 - 与Python版本完全一致
        const baseShift = this.BASE[0] - this.BACKGROUND[0];
        this.base.x = -((-this.base.x + 100) % baseShift);
    }

    /**
     * 检测碰撞 - 修复碰撞检测逻辑
     */
    checkCollision() {
        // 检查是否撞到地面或天花板 - 与Python版本完全一致
        if (this.player.y + this.PLAYER[1] >= this.BASEY - 1) {
            return {crashed: true, groundCrash: true};
        }

        if (this.player.y <= 0) {
            return {crashed: true, groundCrash: false};
        }

        // 创建玩家矩形
        const playerRect = {
            x: this.player.x,
            y: this.player.y,
            width: this.PLAYER[0],
            height: this.PLAYER[1],
            index: this.playerIndex
        };

        // 检查管道碰撞 - 使用与Python版本相同的逻辑
        for (const pipe of this.pipes) {
            const collision = this.checkPipeCollision(playerRect, pipe);
            if (collision.crashed) {
                return {crashed: true, groundCrash: false};
            }
        }

        return {crashed: false, groundCrash: false};
    }

    /**
     * 检查管道碰撞 - 修复碰撞检测
     */
    checkPipeCollision(player, pipe) {
        // 玩家矩形
        const playerRect = {
            x: player.x,
            y: player.y,
            width: this.PLAYER[0],
            height: this.PLAYER[1]
        };

        // 上管道矩形
        const upperPipeRect = {
            x: pipe.upper.x,
            y: pipe.upper.y,
            width: this.PIPE[0],
            height: this.PIPE[1]
        };

        // 下管道矩形
        const lowerPipeRect = {
            x: pipe.lower.x,
            y: pipe.lower.y,
            width: this.PIPE[0],
            height: this.PIPE[1]
        };

        // 简单的矩形碰撞检测（优化性能）
        const collideUpper = this.rectCollision(playerRect, upperPipeRect);
        const collideLower = this.rectCollision(playerRect, lowerPipeRect);

        if (collideUpper || collideLower) {
            return {crashed: true};
        }

        return {crashed: false};
    }

    /**
     * 矩形碰撞检测
     */
    rectCollision(rect1, rect2) {
        return rect1.x < rect2.x + rect2.width &&
            rect1.x + rect1.width > rect2.x &&
            rect1.y < rect2.y + rect2.height &&
            rect1.y + rect1.height > rect2.y;
    }

    /**
     * 处理碰撞
     */
    handleCrash(collision) {
        this.player.alive = false;

        // 播放音效
        if (this.display) {
            if (this.sounds.hit) {
                this.sounds.hit.currentTime = 0;
                this.sounds.hit.play();
            }

            if (!collision.groundCrash && this.sounds.die) {
                this.sounds.die.currentTime = 0;
                this.sounds.die.play();
            }
        }

        // 停止游戏
        this.stop();

        // 更新Bot的Q值 - 关键修复：确保在游戏结束后更新
        if (this.bot) {
            this.bot.updateScores();
        }

        // 触发游戏结束事件
        if (this.onGameOver) {
            this.onGameOver({
                score: this.score,
                iteration: this.currentIteration,
                totalIterations: this.totalIterations
            });
        }
    }

    /**
     * 生成随机管道 - 与Python版本完全一致
     */
    getRandomPipe() {
        const gapY = Math.floor(Math.random() * (this.BASEY * 0.6 - this.PIPEGAPSIZE)) + this.BASEY * 0.2;
        const pipeX = this.SCREENWIDTH + 10;

        const pipeHeight = this.display ? (this.images.pipe[0] ? this.images.pipe[0].height : this.PIPE[1]) : this.PIPE[1];

        return {
            upper: {
                x: pipeX,
                y: gapY - pipeHeight
            },
            lower: {
                x: pipeX,
                y: gapY + this.PIPEGAPSIZE
            }
        };
    }

    /**
     * 拍打翅膀 - 与Python版本完全一致
     */
    flap() {
        if (this.player.y > -2 * this.PLAYER[1]) {
            this.player.velocityY = this.player.flapAcc;
            this.player.flapped = true;

            if (this.display && this.sounds.wing) {
                this.sounds.wing.currentTime = 0;
                this.sounds.wing.play();
            }
        }
    }

    /**
     * 渲染游戏
     */
    render() {
        if (!this.display || !this.gameRunning) return;

        // 清空画布
        this.ctx.clearRect(0, 0, this.SCREENWIDTH, this.SCREENHEIGHT);

        // 绘制背景
        if (this.images.background && this.images.background.complete) {
            this.ctx.drawImage(this.images.background, 0, 0);
        } else {
            // 后备：绘制纯色背景
            this.ctx.fillStyle = '#4fd1c5';
            this.ctx.fillRect(0, 0, this.SCREENWIDTH, this.SCREENHEIGHT);
        }

        // 绘制管道
        for (const pipe of this.pipes) {
            if (this.images.pipe[0] && this.images.pipe[0].complete) {
                // 上管道（旋转180度）
                this.ctx.save();
                this.ctx.translate(pipe.upper.x + this.PIPE[0] / 2, pipe.upper.y + this.PIPE[1] / 2);
                this.ctx.rotate(Math.PI);
                this.ctx.drawImage(this.images.pipe[0], -this.PIPE[0] / 2, -this.PIPE[1] / 2);
                this.ctx.restore();

                // 下管道
                this.ctx.drawImage(this.images.pipe[1], pipe.lower.x, pipe.lower.y);
            } else {
                // 后备：绘制矩形管道
                this.ctx.fillStyle = '#0a0';
                this.ctx.fillRect(pipe.upper.x, pipe.upper.y, this.PIPE[0], this.PIPE[1]);
                this.ctx.fillRect(pipe.lower.x, pipe.lower.y, this.PIPE[0], this.PIPE[1]);
            }
        }

        // 绘制地面
        if (this.images.base && this.images.base.complete) {
            this.ctx.drawImage(this.images.base, this.base.x, this.base.y);
            // 绘制第二个地面以实现循环
            this.ctx.drawImage(this.images.base, this.base.x + this.BASE[0], this.base.y);
        } else {
            // 后备：绘制矩形地面
            this.ctx.fillStyle = '#deb887';
            this.ctx.fillRect(0, this.BASEY, this.SCREENWIDTH, this.SCREENHEIGHT - this.BASEY);
        }

        // 绘制玩家
        if (this.images.player && this.images.player[this.playerIndex] &&
            this.images.player[this.playerIndex].complete) {
            this.ctx.drawImage(
                this.images.player[this.playerIndex],
                this.player.x,
                this.player.y
            );
        } else {
            // 后备：绘制圆形玩家
            this.ctx.fillStyle = '#f00';
            this.ctx.beginPath();
            this.ctx.arc(
                this.player.x + this.PLAYER[0] / 2,
                this.player.y + this.PLAYER[1] / 2,
                this.PLAYER[0] / 2,
                0,
                Math.PI * 2
            );
            this.ctx.fill();
        }

        // 绘制分数
        this.renderScore();
    }

    /**
     * 渲染分数
     */
    renderScore() {
        const scoreStr = this.score.toString();
        let totalWidth = 0;

        // 计算总宽度
        for (let i = 0; i < scoreStr.length; i++) {
            const digit = parseInt(scoreStr[i]);
            if (this.images.numbers[digit] && this.images.numbers[digit].complete) {
                totalWidth += this.images.numbers[digit].width;
            }
        }

        // 绘制数字
        let xOffset = (this.SCREENWIDTH - totalWidth) / 2;
        for (let i = 0; i < scoreStr.length; i++) {
            const digit = parseInt(scoreStr[i]);
            if (this.images.numbers[digit] && this.images.numbers[digit].complete) {
                this.ctx.drawImage(
                    this.images.numbers[digit],
                    xOffset,
                    this.SCREENHEIGHT * 0.1
                );
                xOffset += this.images.numbers[digit].width;
            }
        }
    }

    /**
     * 开始训练 - 修复训练逻辑
     */
    async startTraining(iterations = 1000, displayFreq = 10) {
        this.trainingMode = true;
        this.totalIterations = iterations;
        this.displayFrequency = displayFreq;
        this.currentIteration = 0;
        this.shouldStopTraining = false;

        await this.trainLoop();
    }

    /**
     * 训练循环 - 修复死循环问题
     */
    async trainLoop() {
        while (this.currentIteration < this.totalIterations &&
        this.trainingMode &&
        !this.shouldStopTraining) {

            // 决定是否显示当前迭代
            const shouldDisplay = this.display &&
                (this.displayFrequency > 0 &&
                    (this.currentIteration % this.displayFrequency === 0 || this.currentIteration === 0));

            if (shouldDisplay) {
                // 显示模式：完整游戏循环
                await this.showWelcomeAnimation();

                // 重置游戏状态
                this.resetGame();
                this.gameRunning = true;
                this.player.alive = true;

                // 开始游戏循环
                this.start();

                // 等待游戏结束
                await new Promise(resolve => {
                    const gameOverHandler = (data) => {
                        // 移除事件监听器，避免重复调用
                        if (this.onGameOver === gameOverHandler) {
                            this.onGameOver = null;
                        }
                        resolve(data);
                    };

                    this.onGameOver = gameOverHandler;
                });

                await this.showGameOverScreen();

                // 增加迭代计数
                this.currentIteration++;

            } else {
                // 非显示模式：快速训练
                this.resetGame();
                this.gameRunning = true;
                this.player.alive = true;

                // 模拟游戏循环直到结束
                while (this.player.alive && this.gameRunning) {
                    // AI决策
                    if (this.trainingMode && this.bot) {
                        let targetPipe;
                        if (-this.player.x + this.pipes[0].lower.x > -30) {
                            targetPipe = this.pipes[0];
                        } else {
                            targetPipe = this.pipes[1];
                        }

                        const xdif = -this.player.x + targetPipe.lower.x;
                        const ydif = -this.player.y + targetPipe.lower.y;
                        const vel = this.player.velocityY;

                        if (this.bot.act(xdif, ydif, vel)) {
                            this.flap();
                        }
                    }

                    // 更新玩家
                    if (this.player.velocityY < this.player.maxVelY && !this.player.flapped) {
                        this.player.velocityY += this.player.accY;
                    }

                    if (this.player.flapped) {
                        this.player.flapped = false;
                    }

                    const playerHeight = this.PLAYER[1];
                    const maxY = this.BASEY - playerHeight;
                    const velocity = Math.min(this.player.velocityY, maxY - this.player.y);
                    this.player.y += velocity;

                    if (this.player.y < 0) {
                        this.player.y = 0;
                        this.player.velocityY = 0;
                    }

                    // 更新管道
                    const pipeVelX = -4;
                    for (const pipe of this.pipes) {
                        pipe.upper.x += pipeVelX;
                        pipe.lower.x += pipeVelX;
                    }

                    // 添加新管道
                    if (0 < this.pipes[0].upper.x && this.pipes[0].upper.x < 5) {
                        const newPipe = this.getRandomPipe();
                        this.pipes.push({
                            upper: {x: newPipe.upper.x, y: newPipe.upper.y},
                            lower: {x: newPipe.lower.x, y: newPipe.lower.y}
                        });
                    }

                    // 移除屏幕外的管道
                    if (this.pipes[0].upper.x < -this.PIPE[0]) {
                        this.pipes.shift();
                    }

                    // 碰撞检测
                    const collision = this.checkCollision();
                    if (collision.crashed) {
                        this.player.alive = false;
                        break;
                    }

                    // 计分
                    const playerMidPos = this.player.x + this.PLAYER[0] / 2;
                    for (const pipe of this.pipes) {
                        const pipeMidPos = pipe.upper.x + this.PIPE[0] / 2;
                        if (pipeMidPos <= playerMidPos && playerMidPos < pipeMidPos + 4) {
                            this.score++;
                            break;
                        }
                    }

                    // 更新动画
                    this.playerCycleIndex = (this.playerCycleIndex + 1) % 30;
                    if ((this.playerCycleIndex + 1) % 3 === 0) {
                        const nextIndex = Math.floor((this.playerCycleIndex + 1) / 3) % 4;
                        this.playerIndex = this.playerIndexCycle[nextIndex];
                    }

                    const baseShift = this.BASE[0] - this.BACKGROUND[0];
                    this.base.x = -((-this.base.x + 100) % baseShift);
                }

                // 游戏结束，更新Bot的Q值
                if (this.bot) {
                    this.bot.updateScores();
                }

                // 增加迭代计数
                this.currentIteration++;

                // 更新进度回调
                if (this.onTrainingProgress) {
                    this.onTrainingProgress({
                        iteration: this.currentIteration,
                        totalIterations: this.totalIterations,
                        score: this.score,
                        gameCount: this.bot ? this.bot.gameCNT : 0
                    });
                }
            }

            // 短暂延迟，避免阻塞主线程
            await new Promise(resolve => setTimeout(resolve, 0));
        }

        // 训练完成
        this.trainingMode = false;
        if (this.onTrainingComplete) {
            this.onTrainingComplete();
        }
    }

    /**
     * 停止训练
     */
    stopTraining() {
        this.shouldStopTraining = true;
        this.trainingMode = false;
        this.stop();
    }

    /**
     * 显示欢迎动画
     */
    async showWelcomeAnimation() {
        return new Promise(resolve => {
            if (this.display) {
                // 绘制欢迎界面
                this.renderWelcomeScreen();

                // 播放音效
                if (this.sounds.swoosh) {
                    this.sounds.swoosh.currentTime = 0;
                    this.sounds.swoosh.play();
                }

                // 短暂显示后继续
                setTimeout(() => {
                    if (this.sounds.wing) {
                        this.sounds.wing.currentTime = 0;
                        this.sounds.wing.play();
                    }
                    resolve();
                }, 500);
            } else {
                resolve();
            }
        });
    }

    /**
     * 渲染欢迎界面
     */
    renderWelcomeScreen() {
        this.ctx.clearRect(0, 0, this.SCREENWIDTH, this.SCREENHEIGHT);

        // 绘制背景
        if (this.images.background && this.images.background.complete) {
            this.ctx.drawImage(this.images.background, 0, 0);
        }

        // 绘制玩家
        const playerY = (this.SCREENHEIGHT - this.PLAYER[1]) / 2;
        if (this.images.player && this.images.player[0] && this.images.player[0].complete) {
            this.ctx.drawImage(this.images.player[0], this.SCREENWIDTH * 0.2, playerY);
        }

        // 绘制消息
        if (this.images.message && this.images.message.complete) {
            const messageX = (this.SCREENWIDTH - this.images.message.width) / 2;
            const messageY = this.SCREENHEIGHT * 0.12;
            this.ctx.drawImage(this.images.message, messageX, messageY);
        }

        // 绘制地面
        if (this.images.base && this.images.base.complete) {
            this.ctx.drawImage(this.images.base, 0, this.BASEY);
        }
    }

    /**
     * 显示游戏结束界面
     */
    async showGameOverScreen() {
        return new Promise(resolve => {
            if (this.display) {
                // 绘制游戏结束界面
                this.renderGameOverScreen();

                // 短暂显示后继续
                setTimeout(resolve, 1500);
            } else {
                resolve();
            }
        });
    }

    /**
     * 渲染游戏结束界面
     */
    renderGameOverScreen() {
        this.ctx.clearRect(0, 0, this.SCREENWIDTH, this.SCREENHEIGHT);

        // 绘制背景
        if (this.images.background && this.images.background.complete) {
            this.ctx.drawImage(this.images.background, 0, 0);
        }

        // 绘制管道
        for (const pipe of this.pipes) {
            if (this.images.pipe[0] && this.images.pipe[0].complete) {
                // 上管道
                this.ctx.save();
                this.ctx.translate(pipe.upper.x + this.PIPE[0] / 2, pipe.upper.y + this.PIPE[1] / 2);
                this.ctx.rotate(Math.PI);
                this.ctx.drawImage(this.images.pipe[0], -this.PIPE[0] / 2, -this.PIPE[1] / 2);
                this.ctx.restore();

                // 下管道
                this.ctx.drawImage(this.images.pipe[1], pipe.lower.x, pipe.lower.y);
            }
        }

        // 绘制地面
        if (this.images.base && this.images.base.complete) {
            this.ctx.drawImage(this.images.base, this.base.x, this.BASEY);
        }

        // 绘制分数
        this.renderScore();

        // 绘制游戏结束文字
        if (this.images.gameover && this.images.gameover.complete) {
            const gameoverX = (this.SCREENWIDTH - this.images.gameover.width) / 2;
            const gameoverY = this.SCREENHEIGHT * 0.4;
            this.ctx.drawImage(this.images.gameover, gameoverX, gameoverY);
        }
    }

    /**
     * 设置回调函数
     */
    setCallbacks(options) {
        if (options.onGameOver) this.onGameOver = options.onGameOver;
        if (options.onTrainingProgress) this.onTrainingProgress = options.onTrainingProgress;
        if (options.onTrainingComplete) this.onTrainingComplete = options.onTrainingComplete;
    }
}