
```
```
flappybird-qlearning-bot
├─ .idea
│  ├─ flappybird-qlearning-bot.iml
│  ├─ inspectionProfiles
│  │  └─ profiles_settings.xml
│  ├─ misc.xml
│  ├─ modules.xml
│  └─ vcs.xml
├─ data
│  ├─ assets
│  │  ├─ audio
│  │  │  ├─ die.ogg
│  │  │  ├─ die.wav
│  │  │  ├─ hit.ogg
│  │  │  ├─ hit.wav
│  │  │  ├─ point.ogg
│  │  │  ├─ point.wav
│  │  │  ├─ swoosh.ogg
│  │  │  ├─ swoosh.wav
│  │  │  ├─ wing.ogg
│  │  │  └─ wing.wav
│  │  └─ sprites
│  │     ├─ 0.png
│  │     ├─ 1.png
│  │     ├─ 2.png
│  │     ├─ 3.png
│  │     ├─ 4.png
│  │     ├─ 5.png
│  │     ├─ 6.png
│  │     ├─ 7.png
│  │     ├─ 8.png
│  │     ├─ 9.png
│  │     ├─ background-day.png
│  │     ├─ background-future.png
│  │     ├─ background-mid.png
│  │     ├─ background-night.png
│  │     ├─ background-war.png
│  │     ├─ base.png
│  │     ├─ bluebird-anger-downflap.png
│  │     ├─ bluebird-anger-midflap.png
│  │     ├─ bluebird-anger-upflap.png
│  │     ├─ bluebird-downflap.png
│  │     ├─ bluebird-midflap.png
│  │     ├─ bluebird-upflap.png
│  │     ├─ fadebird-downflap.png
│  │     ├─ fadebird-midflap.png
│  │     ├─ fadebird-upflap.png
│  │     ├─ gameover.png
│  │     ├─ message.png
│  │     ├─ pipe-green.png
│  │     ├─ pipe-grey.png
│  │     ├─ pipe-red.png
│  │     ├─ redbird-downflap.png
│  │     ├─ redbird-fade-downflap.png
│  │     ├─ redbird-fade-midflap.png
│  │     ├─ redbird-fade-upflap.png
│  │     ├─ redbird-midflap.png
│  │     ├─ redbird-upflap.png
│  │     ├─ yellowbird-downflap.png
│  │     ├─ yellowbird-midflap.png
│  │     └─ yellowbird-upflap.png
│  ├─ flappy.ico
│  ├─ hitmasks_data.pkl
│  └─ qvalues.json
├─ LICENSE
├─ README.md
├─ requirements.txt
├─ requirements_web.txt
├─ src
│  ├─ bot.py
│  ├─ bot_test.py
│  ├─ flappy.py
│  ├─ flappy_gui.py
│  ├─ initialize_qvalues.py
│  ├─ learn.py
│  ├─ learn_draw.py
│  └─ train_with_display.py
├─ test
│  ├─ add_safearea_check.png
│  ├─ discount=0.9.png
│  ├─ learn_rate_0.5.png
│  ├─ No_live_score.png
│  └─ ε-greedy_with_safecheck.png
├─ training_scores.png
└─ web
   ├─ app.py
   ├─ bot.py
   ├─ game_engine.py
   ├─ static
   │  └─ js
   │     ├─ assets
   │     │  ├─ audio
   │     │  │  ├─ die.ogg
   │     │  │  ├─ die.wav
   │     │  │  ├─ hit.ogg
   │     │  │  ├─ hit.wav
   │     │  │  ├─ point.ogg
   │     │  │  ├─ point.wav
   │     │  │  ├─ swoosh.ogg
   │     │  │  ├─ swoosh.wav
   │     │  │  ├─ wing.ogg
   │     │  │  └─ wing.wav
   │     │  └─ sprites
   │     │     ├─ 0.png
   │     │     ├─ 1.png
   │     │     ├─ 2.png
   │     │     ├─ 3.png
   │     │     ├─ 4.png
   │     │     ├─ 5.png
   │     │     ├─ 6.png
   │     │     ├─ 7.png
   │     │     ├─ 8.png
   │     │     ├─ 9.png
   │     │     ├─ background-day.png
   │     │     ├─ background-future.png
   │     │     ├─ background-mid.png
   │     │     ├─ background-night.png
   │     │     ├─ background-war.png
   │     │     ├─ base.png
   │     │     ├─ bluebird-anger-downflap.png
   │     │     ├─ bluebird-anger-midflap.png
   │     │     ├─ bluebird-anger-upflap.png
   │     │     ├─ bluebird-downflap.png
   │     │     ├─ bluebird-midflap.png
   │     │     ├─ bluebird-upflap.png
   │     │     ├─ fadebird-downflap.png
   │     │     ├─ fadebird-midflap.png
   │     │     ├─ fadebird-upflap.png
   │     │     ├─ gameover.png
   │     │     ├─ message.png
   │     │     ├─ pipe-green.png
   │     │     ├─ pipe-grey.png
   │     │     ├─ pipe-red.png
   │     │     ├─ redbird-downflap.png
   │     │     ├─ redbird-fade-downflap.png
   │     │     ├─ redbird-fade-midflap.png
   │     │     ├─ redbird-fade-upflap.png
   │     │     ├─ redbird-midflap.png
   │     │     ├─ redbird-upflap.png
   │     │     ├─ yellowbird-downflap.png
   │     │     ├─ yellowbird-midflap.png
   │     │     └─ yellowbird-upflap.png
   │     └─ demo.js
   ├─ templates
   │  ├─ demo.html
   │  └─ index.html
   └─ user_data

```