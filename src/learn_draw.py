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

IM_WIDTH = 0
IM_HEIGTH = 1
PIPE = [52, 320]
PLAYER = [34, 24]
BASE = [336, 112]
BACKGROUND = [288, 512]

# Global list to store scores of each episode
scores = []


def main():
    global HITMASKS, ITERATIONS, VERBOSE, bot, scores

    parser = argparse.ArgumentParser("learn.py")
    parser.add_argument("--iter", type=int, default=1000, help="number of iterations to run")
    parser.add_argument(
        "--verbose", action="store_true", help="output [iteration | score] to stdout"
    )
    args = parser.parse_args()
    ITERATIONS = args.iter
    VERBOSE = args.verbose

    # Load precomputed hitmasks
    with open("../data/hitmasks_data.pkl", "rb") as input_file:
        HITMASKS = pickle.load(input_file)

    # Reset scores before starting
    scores = []

    while True:
        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


def showWelcomeAnimation():
    playerIndexGen = cycle([0, 1, 2, 1])
    playery = int((SCREENHEIGHT - PLAYER[IM_HEIGTH]) / 2)
    basex = 0
    playerShmVals = {"val": 0, "dir": 1}
    return {
        "playery": playery + playerShmVals["val"],
        "basex": basex,
        "playerIndexGen": playerIndexGen,
    }


def mainGame(movementInfo):
    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo["playerIndexGen"]
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo["playery"]
    basex = movementInfo["basex"]
    baseShift = BASE[IM_WIDTH] - BACKGROUND[IM_WIDTH]

    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    upperPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[0]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[0]["y"]},
    ]
    lowerPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[1]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[1]["y"]},
    ]

    pipeVelX = -4
    playerVelY = -9
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1
    playerFlapAcc = -9
    playerFlapped = False

    while True:
        if -playerx + lowerPipes[0]["x"] > -30:
            myPipe = lowerPipes[0]
        else:
            myPipe = lowerPipes[1]

        if bot.act(-playerx + myPipe["x"], -playery + myPipe["y"], playerVelY):
            if playery > -2 * PLAYER[IM_HEIGTH]:
                playerVelY = playerFlapAcc
                playerFlapped = True

        crashTest = checkCrash(
            {"x": playerx, "y": playery, "index": playerIndex}, upperPipes, lowerPipes
        )
        if crashTest[0]:
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

        playerMidPos = playerx + PLAYER[IM_WIDTH] / 2
        for pipe in upperPipes:
            pipeMidPos = pipe["x"] + PIPE[IM_WIDTH] / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1

        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False
        playerHeight = PLAYER[IM_HEIGTH]
        playery += min(playerVelY, BASEY - playery - playerHeight)

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe["x"] += pipeVelX
            lPipe["x"] += pipeVelX

        if 0 < upperPipes[0]["x"] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        if upperPipes[0]["x"] < -PIPE[IM_WIDTH]:
            upperPipes.pop(0)
            lowerPipes.pop(0)


def showGameOverScreen(crashInfo):
    global scores, ITERATIONS, bot
    score = crashInfo["score"]
    scores.append(score)

    if VERBOSE:
        print(f"{bot.gameCNT - 1} | {score}")

    if bot.gameCNT == ITERATIONS:
        bot.dump_qvalues(force=True)

        # ====== 绘制并保存散点图 ======
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 6))
            episodes = list(range(1, len(scores) + 1))
            plt.scatter(episodes, scores, alpha=0.6, s=12, color='steelblue')
            plt.title("Training Progress: Score per Episode", fontsize=14)
            plt.xlabel("Episode", fontsize=12)
            plt.ylabel("Score", fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.savefig("../training_scores.png", dpi=150)
            plt.show()
        except ImportError:
            print("matplotlib not installed. Skipping plot generation.")
            # Optionally save scores to file
            with open("scores.txt", "w") as f:
                for i, s in enumerate(scores, 1):
                    f.write(f"{i},{s}\n")
        # ================================

        sys.exit()


def playerShm(playerShm):
    if abs(playerShm["val"]) == 8:
        playerShm["dir"] *= -1
    if playerShm["dir"] == 1:
        playerShm["val"] += 1
    else:
        playerShm["val"] -= 1


def getRandomPipe():
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = PIPE[IM_HEIGTH]
    pipeX = SCREENWIDTH + 10
    return [
        {"x": pipeX, "y": gapY - pipeHeight},
        {"x": pipeX, "y": gapY + PIPEGAPSIZE},
    ]


def checkCrash(player, upperPipes, lowerPipes):
    pi = player["index"]
    player["w"] = PLAYER[IM_WIDTH]
    player["h"] = PLAYER[IM_HEIGTH]

    if (player["y"] + player["h"] >= BASEY - 1) or (player["y"] + player["h"] <= 0):
        return [True, True]
    else:
        playerRect = pygame.Rect(player["x"], player["y"], player["w"], player["h"])
        pipeW = PIPE[IM_WIDTH]
        pipeH = PIPE[IM_HEIGTH]

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipeRect = pygame.Rect(uPipe["x"], uPipe["y"], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe["x"], lPipe["y"], pipeW, pipeH)

            pHitMask = HITMASKS["player"][pi]
            uHitmask = HITMASKS["pipe"][0]
            lHitmask = HITMASKS["pipe"][1]

            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
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