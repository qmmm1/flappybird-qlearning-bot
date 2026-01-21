// demo.js - Flappy Bird AI Demo using trained Q-table

class FlappyBirdAI {
    constructor() {
    this.canvas = document.getElementById('gameCanvas');
    if (!this.canvas) {
        console.error('❌ Canvas element #gameCanvas not found in HTML.');
        return;
    }
    this.ctx = this.canvas.getContext('2d');
    this.canvas.width = 288;
    this.canvas.height = 512;

    // === 第一步：定义所有状态属性 ===
    this.PIPE_GAP_SIZE = 120;
    this.BASE_Y = 512 * 0.79;
    this.PIPE_VELOCITY_X = -4;
    this.GRAVITY = 1;
    this.FLAP_VELOCITY = -9;
    this.MAX_VELOCITY_Y = 10;
    this.BASE_SHIFT = 336 - 288;

    // 玩家状态（必须在 initGame 前定义！）
    this.player = {
        x: 288 * 0.2,
        y: 256,
        velocityY: 0,
        width: 34,
        height: 24
    };

    // 游戏状态
    this.pipes = [];
    this.baseX = 0;
    this.score = 0;
    this.gameRunning = false;
    this.qValues = {};

    // === 第二步：现在可以安全调用 initGame ===
    this.initGame();

    // === 第三步：后台加载 Q-values（不影响启动）===
    this.loadQValues().then(qTable => {
    // 合并到现有 qValues，而不是替换
    Object.assign(this.qValues, qTable);
    console.log('✅ Q-values loaded and merged');
});
}

    async loadQValues() {
    try {
        const response = await fetch('/api/qvalues');
        if (response.ok) {
            this.qValues = await response.json();
            console.log('✅ Q-values loaded successfully');

            // 🔍 新增：检查是否存在非零 Q 值
            const hasNonZeroQ = Object.values(this.qValues).some(
                q => Array.isArray(q) && (q[0] !== 0 || q[1] !== 0)
            );

            if (hasNonZeroQ) {
                console.log('🧠 Q-table contains trained (non-zero) values — AI is ready!');
            } else {
                console.warn('⚠️ Q-table loaded, but all values are [0, 0] — AI has no training!');
            }
        } else {
            console.warn('⚠️ Q-values not available, using empty Q-table');
            this.qValues = {};
        }
    } catch (error) {
        console.error('❌ Error loading Q-values:', error);
        this.qValues = {};
    }
}

    initGame() {
        // 重置状态
        this.player.y = (512 - 24) / 2; 
        this.player.velocityY = -9;
        this.pipes = [];
        this.score = 0;
        this.baseX = 0;
        this.gameRunning = true;

        // 生成初始两根管道
        this.generatePipe();

        // 更新分数显示
        this.updateScoreDisplay();

        // 启动游戏循环
        console.log('🎮 Game started');
        this.gameLoop();
    }

    updateScoreDisplay() {
        const scoreEl = document.getElementById('scoreValue');
        if (scoreEl) {
            scoreEl.textContent = this.score;
        }
    }

    generatePipe() {
        const pipeGapY = Math.floor(Math.random() * (this.BASE_Y * 0.6 - this.PIPE_GAP_SIZE)) + this.BASE_Y * 0.2;
        this.pipes.push({
            x: 288 + 10,
            topY: pipeGapY - 320,
            bottomY: pipeGapY + this.PIPE_GAP_SIZE,
            passed: false
        });
    }

    mapState(xdif, ydif, vel) {
        let mappedXdif = xdif < 140 ? Math.floor(xdif / 10) * 10 : Math.floor(xdif / 70) * 70;
        let mappedYdif = ydif < 180 ? Math.floor(ydif / 10) * 10 : Math.floor(ydif / 60) * 60;
        return `${mappedXdif}_${mappedYdif}_${vel}`;
    }

    getAction(xdif, ydif, vel) {
        const state = this.mapState(xdif, ydif, vel);
        if (!this.qValues[state]) {
            this.qValues[state] = [0.0, 0.0]; // [no flap, flap]
        }
        return this.qValues[state][0] >= this.qValues[state][1] ? 0 : 1;
    }

    update() {
        if (!this.gameRunning) return;

        // 更新地面滚动
        this.baseX = -((-this.baseX + 1) % this.BASE_SHIFT);

        // 更新玩家物理
        this.player.velocityY += this.GRAVITY;
        if (this.player.velocityY > this.MAX_VELOCITY_Y) {
            this.player.velocityY = this.MAX_VELOCITY_Y;
        }
        this.player.y += this.player.velocityY;

        // 边界限制
        if (this.player.y < 0) {
            this.player.y = 0;
        }

        // 更新管道
        for (let i = 0; i < this.pipes.length; i++) {
            this.pipes[i].x += this.PIPE_VELOCITY_X;
            if (!this.pipes[i].passed && this.pipes[i].x + 52 < this.player.x) {
                this.pipes[i].passed = true;
                this.score++;
                this.updateScoreDisplay();
            }
        }

        // 移除屏幕外的管道
        if (this.pipes.length > 0 && this.pipes[0].x < -52) {
            this.pipes.shift();
        }

        // 添加新管道
        if (this.pipes.length === 0 || this.pipes[this.pipes.length - 1].x < 88) {
            this.generatePipe();
        }

        // AI 决策
        let closestPipe = null;
        for (let pipe of this.pipes) {
            if (pipe.x + 52 > this.player.x) {
                closestPipe = pipe;
                break;
            }
        }

        if (closestPipe) {
            const xdif = closestPipe.x - this.player.x;
            const ydif = closestPipe.bottomY - this.player.y;
            const vel = Math.trunc(this.player.velocityY);
            const action = this.getAction(xdif, ydif, vel);
            if (action === 1 && this.player.y > -2 * this.player.height) {
                this.player.velocityY = this.FLAP_VELOCITY;
            }
        }

        // 碰撞检测
        if (this.checkCollision()) {
            this.gameRunning = false;
            setTimeout(() => this.initGame(), 2000);
        }
    }

    checkCollision() {
        // 地面或天花板碰撞
        if (this.player.y + this.player.height >= this.BASE_Y - 1 || this.player.y <= 0) {
            return true;
        }

        // 管道碰撞
        for (let pipe of this.pipes) {
            if (
                this.player.x + this.player.width > pipe.x &&
                this.player.x < pipe.x + 52 &&
                (this.player.y < pipe.topY + 320 || this.player.y + this.player.height > pipe.bottomY)
            ) {
                return true;
            }
        }
        return false;
    }

    render() {
        // 清空并绘制背景
        this.ctx.fillStyle = '#70c5ce';
        this.ctx.fillRect(0, 0, 288, 512);

        // 绘制管道
        this.ctx.fillStyle = '#73bf2e';
        for (let pipe of this.pipes) {
            this.ctx.fillRect(pipe.x, pipe.topY, 52, 320); // 上管道
            this.ctx.fillRect(pipe.x, pipe.bottomY, 52, 512 - pipe.bottomY); // 下管道
        }

        // 绘制地面
        this.ctx.fillStyle = '#dec94b';
        this.ctx.fillRect(0, this.BASE_Y, 288, 512 - this.BASE_Y);

        // 绘制小鸟
        this.ctx.fillStyle = '#ff0000';
        this.ctx.fillRect(this.player.x, this.player.y, this.player.width, this.player.height);

        // 游戏内分数（可选）
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '24px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(this.score.toString(), 144, 50);

        // 游戏结束覆盖层
        if (!this.gameRunning) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            this.ctx.fillRect(0, 0, 288, 512);
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '20px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('GAME OVER', 144, 256);
            this.ctx.fillText(`Score: ${this.score}`, 144, 286);
        }
    }

    // 在 gameLoop 中加延迟（会卡顿！）
    gameLoop() {
        this.update();
        this.render();
        if (this.gameRunning) {
            setTimeout(() => {
                requestAnimationFrame(() => this.gameLoop());
            }, 50); // 限制 ～20 FPS
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否已初始化
    if (window.FlappyBirdAIInstance) return;

    // 创建 AI 实例
    const aiDemo = new FlappyBirdAI();
    window.FlappyBirdAIInstance = aiDemo;

    // 绑定重启按钮
    const restartBtn = document.getElementById('restartBtn');
    if (restartBtn) {
        restartBtn.onclick = () => {
            aiDemo.initGame();
        };
    }
});

// 可选：禁用空格键默认行为（防止页面滚动）
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' || e.key === ' ') {
        e.preventDefault();
    }
});