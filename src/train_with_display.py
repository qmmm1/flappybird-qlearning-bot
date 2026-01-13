from itertools import cycle
import random
import sys
import os
import argparse
import pickle

import pygame
from pygame.locals import *

sys.path.append(os.getcwd())

from bot import Bot

# Initialize the bot
bot = Bot()

SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 100
BASEY = SCREENHEIGHT * 0.79

# 图片尺寸
IM_WIDTH = 0
IM_HEIGTH = 1
PIPE = [52, 320]
PLAYER = [34, 24]
BASE = [336, 112]
BACKGROUND = [288, 512]

# 图片和声音字典
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# 玩家图片列表
PLAYERS_LIST = (
    "../data/assets/sprites/redbird-upflap.png",
    "../data/assets/sprites/redbird-midflap.png",
    "../data/assets/sprites/redbird-downflap.png",
)

# 背景图片
BACKGROUNDS_LIST = ("../data/assets/sprites/background-day.png",)

# 管道图片
PIPES_LIST = ("../data/assets/sprites/pipe-green.png",)


def main():
    global SCREEN, FPSCLOCK, HITMASKS, ITERATIONS, VERBOSE, DISPLAY_FREQ, bot

    parser = argparse.ArgumentParser("train_with_display.py")
    parser.add_argument("--iter", type=int, default=1000, help="number of iterations to run")
    parser.add_argument("--display_freq", type=int, default=10, help="display every N iterations")
    parser.add_argument("--verbose", action="store_true", help="output [iteration | score] to stdout")
    args = parser.parse_args()

    ITERATIONS = args.iter
    VERBOSE = args.verbose
    DISPLAY_FREQ = args.display_freq

    # 加载碰撞掩码
    with open("../data/hitmasks_data.pkl", "rb") as input_file:
        HITMASKS = pickle.load(input_file)

    # 初始化pygame
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption("Flappy Bird - Training")

    # 加载基础资源
    load_resources()

    while True:
        # 检查是否需要显示当前迭代
        should_display = (bot.gameCNT % DISPLAY_FREQ == 0) if DISPLAY_FREQ > 0 else False

        if should_display:
            # 显示模式：加载完整资源并显示python train_with_display.py --iter 1000 --display_freq 10 --verbose
            load_display_resources()
            movementInfo = showWelcomeAnimation(display=True)
            crashInfo = mainGame(movementInfo, display=True)
            showGameOverScreen(crashInfo, display=True)
        else:
            # 非显示模式：快速训练
            movementInfo = showWelcomeAnimation(display=False)
            crashInfo = mainGame(movementInfo, display=False)
            showGameOverScreen(crashInfo, display=False)

        # 检查是否完成所有迭代
        if bot.gameCNT >= ITERATIONS:
            bot.dump_qvalues(force=True)
            pygame.quit()
            sys.exit()


def load_resources():
    """加载基础资源（无论显示与否都需要）"""
    # 加载数字图片用于显示分数
    IMAGES["numbers"] = (
        pygame.image.load("../data/assets/sprites/0.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/1.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/2.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/3.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/4.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/5.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/6.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/7.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/8.png").convert_alpha(),
        pygame.image.load("../data/assets/sprites/9.png").convert_alpha(),
    )

    # 游戏结束和消息图片
    IMAGES["gameover"] = pygame.image.load("../data/assets/sprites/gameover.png").convert_alpha()
    IMAGES["message"] = pygame.image.load("../data/assets/sprites/message.png").convert_alpha()
    IMAGES["base"] = pygame.image.load("../data/assets/sprites/base.png").convert_alpha()


def load_display_resources():
    """加载显示所需的所有资源"""
    # 加载背景
    IMAGES["background"] = pygame.image.load(BACKGROUNDS_LIST[0]).convert()

    # 加载玩家图片
    IMAGES["player"] = (
        pygame.image.load(PLAYERS_LIST[0]).convert_alpha(),
        pygame.image.load(PLAYERS_LIST[1]).convert_alpha(),
        pygame.image.load(PLAYERS_LIST[2]).convert_alpha(),
    )

    # 加载管道图片
    IMAGES["pipe"] = (
        pygame.transform.rotate(pygame.image.load(PIPES_LIST[0]).convert_alpha(), 180),
        pygame.image.load(PIPES_LIST[0]).convert_alpha(),
    )

    # 加载声音
    if "win" in sys.platform:
        soundExt = ".wav"
    else:
        soundExt = ".ogg"

    SOUNDS["die"] = pygame.mixer.Sound("../data/assets/audio/die" + soundExt)
    SOUNDS["hit"] = pygame.mixer.Sound("../data/assets/audio/hit" + soundExt)
    SOUNDS["point"] = pygame.mixer.Sound("../data/assets/audio/point" + soundExt)
    SOUNDS["swoosh"] = pygame.mixer.Sound("../data/assets/audio/swoosh" + soundExt)
    SOUNDS["wing"] = pygame.mixer.Sound("../data/assets/audio/wing" + soundExt)


def showWelcomeAnimation(display=True):
    """显示欢迎动画"""
    playerIndexGen = cycle([0, 1, 2, 1])

    if display:
        playery = int((SCREENHEIGHT - IMAGES["player"][0].get_height()) / 2)

        # 显示欢迎界面
        SCREEN.blit(IMAGES["background"], (0, 0))
        SCREEN.blit(IMAGES["player"][0], (int(SCREENWIDTH * 0.2), playery))
        SCREEN.blit(IMAGES["message"],
                    (int((SCREENWIDTH - IMAGES["message"].get_width()) / 2),
                     int(SCREENHEIGHT * 0.12)))
        SCREEN.blit(IMAGES["base"], (0, BASEY))
        pygame.display.update()

        # 短暂显示欢迎界面
        pygame.time.wait(500)

        # 播放翅膀声音
        SOUNDS["wing"].play()
    else:
        playery = int((SCREENHEIGHT - PLAYER[IM_HEIGTH]) / 2)

    return {
        "playery": playery,
        "basex": 0,
        "playerIndexGen": playerIndexGen,
    }


def mainGame(movementInfo, display=True):
    """主游戏逻辑"""
    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo["playerIndexGen"]

    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo["playery"]
    basex = movementInfo["basex"]

    if display:
        baseShift = IMAGES["base"].get_width() - IMAGES["background"].get_width()
    else:
        baseShift = BASE[IM_WIDTH] - BACKGROUND[IM_WIDTH]

    # 获取初始管道
    newPipe1 = getRandomPipe(display)
    newPipe2 = getRandomPipe(display)

    # 上管道列表
    upperPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[0]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[0]["y"]},
    ]

    # 下管道列表
    lowerPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[1]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[1]["y"]},
    ]

    pipeVelX = -4

    # 玩家物理参数
    playerVelY = -9
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1
    playerFlapAcc = -9
    playerFlapped = False

    # 游戏主循环
    while True:
        # 事件处理（仅在显示模式下）
        if display:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    bot.dump_qvalues(force=True)
                    pygame.quit()
                    sys.exit()

        # AI决策
        if -playerx + lowerPipes[0]["x"] > -30:
            myPipe = lowerPipes[0]
        else:
            myPipe = lowerPipes[1]

        if bot.act(-playerx + myPipe["x"], -playery + myPipe["y"], playerVelY):
            if playery > -2 * (IMAGES["player"][0].get_height() if display else PLAYER[IM_HEIGTH]):
                playerVelY = playerFlapAcc
                playerFlapped = True
                if display:
                    SOUNDS["wing"].play()

        # 碰撞检测
        crashTest = checkCrash(
            {"x": playerx, "y": playery, "index": playerIndex},
            upperPipes, lowerPipes, display
        )

        if crashTest[0]:
            # 更新Q值
            bot.update_scores(dump_qvalues=False)

            return {
                "y": playery,
                "groundCrash": crashTest[1],
                "basex": basex,
                "upperPipes": upperPipes,
                "lowerPipes": lowerPipes,
                "score": score,
                "playerVelY": playerVelY,
            }

        # 计分
        if display:
            playerMidPos = playerx + IMAGES["player"][0].get_width() / 2
        else:
            playerMidPos = playerx + PLAYER[IM_WIDTH] / 2

        for pipe in upperPipes:
            if display:
                pipeMidPos = pipe["x"] + IMAGES["pipe"][0].get_width() / 2
            else:
                pipeMidPos = pipe["x"] + PIPE[IM_WIDTH] / 2

            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                if display:
                    SOUNDS["point"].play()

        # 更新玩家动画和地面
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        # 玩家移动
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False

        if display:
            playerHeight = IMAGES["player"][playerIndex].get_height()
        else:
            playerHeight = PLAYER[IM_HEIGTH]

        playery += min(playerVelY, BASEY - playery - playerHeight)

        # 管道移动
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe["x"] += pipeVelX
            lPipe["x"] += pipeVelX

        # 添加新管道
        if 0 < upperPipes[0]["x"] < 5:
            newPipe = getRandomPipe(display)
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # 移除屏幕外的管道
        if display:
            pipe_width = IMAGES["pipe"][0].get_width()
        else:
            pipe_width = PIPE[IM_WIDTH]

        if upperPipes[0]["x"] < -pipe_width:
            upperPipes.pop(0)
            lowerPipes.pop(0)

        # 显示（仅在显示模式下）
        if display:
            # 绘制背景
            SCREEN.blit(IMAGES["background"], (0, 0))

            # 绘制管道
            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                SCREEN.blit(IMAGES["pipe"][0], (uPipe["x"], uPipe["y"]))
                SCREEN.blit(IMAGES["pipe"][1], (lPipe["x"], lPipe["y"]))

            # 绘制地面
            SCREEN.blit(IMAGES["base"], (basex, BASEY))

            # 显示分数
            showScore(score)

            # 绘制玩家
            SCREEN.blit(IMAGES["player"][playerIndex], (playerx, playery))

            pygame.display.update()
            FPSCLOCK.tick(60)


def showGameOverScreen(crashInfo, display=True):
    """显示游戏结束屏幕"""
    if VERBOSE:
        score = crashInfo["score"]
        print(f"{bot.gameCNT - 1} | {score}")

    if display:
        # 播放碰撞声音
        SOUNDS["hit"].play()
        if not crashInfo["groundCrash"]:
            SOUNDS["die"].play()

        # 显示游戏结束画面
        score = crashInfo["score"]
        SCREEN.blit(IMAGES["background"], (0, 0))

        # 绘制管道
        for uPipe, lPipe in zip(crashInfo["upperPipes"], crashInfo["lowerPipes"]):
            SCREEN.blit(IMAGES["pipe"][0], (uPipe["x"], uPipe["y"]))
            SCREEN.blit(IMAGES["pipe"][1], (lPipe["x"], lPipe["y"]))

        # 绘制地面
        SCREEN.blit(IMAGES["base"], (crashInfo["basex"], BASEY))

        # 显示分数
        showScore(score)

        # 显示游戏结束文字
        SCREEN.blit(IMAGES["gameover"],
                    ((SCREENWIDTH - IMAGES["gameover"].get_width()) / 2,
                     SCREENHEIGHT * 0.4))

        pygame.display.update()

        # 短暂显示游戏结束画面
        pygame.time.wait(1500)


def getRandomPipe(display=True):
    """生成随机管道"""
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeX = SCREENWIDTH + 10

    if display:
        pipeHeight = IMAGES["pipe"][0].get_height()
    else:
        pipeHeight = PIPE[IM_HEIGTH]

    return [
        {"x": pipeX, "y": gapY - pipeHeight},  # 上管道
        {"x": pipeX, "y": gapY + PIPEGAPSIZE},  # 下管道
    ]


def showScore(score):
    """显示分数"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0

    for digit in scoreDigits:
        totalWidth += IMAGES["numbers"][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES["numbers"][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES["numbers"][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes, display=True):
    """检测碰撞"""
    pi = player["index"]

    if display:
        player["w"] = IMAGES["player"][0].get_width()
        player["h"] = IMAGES["player"][0].get_height()
        pipeW = IMAGES["pipe"][0].get_width()
        pipeH = IMAGES["pipe"][0].get_height()
    else:
        player["w"] = PLAYER[IM_WIDTH]
        player["h"] = PLAYER[IM_HEIGTH]
        pipeW = PIPE[IM_WIDTH]
        pipeH = PIPE[IM_HEIGTH]

    # 检测是否撞到地面或天花板
    if (player["y"] + player["h"] >= BASEY - 1) or (player["y"] + player["h"] <= 0):
        return [True, True]
    else:
        playerRect = pygame.Rect(player["x"], player["y"], player["w"], player["h"])

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # 上下管道矩形
            uPipeRect = pygame.Rect(uPipe["x"], uPipe["y"], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe["x"], lPipe["y"], pipeW, pipeH)

            # 碰撞掩码
            if display:
                pHitMask = HITMASKS["player"][pi]
                uHitmask = HITMASKS["pipe"][0]
                lHitmask = HITMASKS["pipe"][1]
            else:
                # 使用预加载的碰撞掩码
                pHitMask = HITMASKS["player"][pi]
                uHitmask = HITMASKS["pipe"][0]
                lHitmask = HITMASKS["pipe"][1]

            # 检测碰撞
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """像素级碰撞检测"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


if __name__ == "__main__":
    main()