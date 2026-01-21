# app.py
"""
Flappy Bird AI Training Web Application
Provides REST API for configuring and running Q-learning training sessions
"""

import os
import json
import glob
import threading
import time
from datetime import datetime
from flask import Flask, request, session,jsonify, render_template, send_from_directory

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in os.sys.path:
    os.sys.path.insert(0, project_root)

try:
    from bot import Bot
    from game_engine import HeadlessFlappyGame
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure your project structure is correct")
    raise

# Global variables to track training status
training_status = {
    'is_training': False,
    'current_session': None,
    'progress': {
        'episode': 0,
        'total_episodes': 0,
        'score': 0,
        'best_score': 0,
        'avg_score': 0.0
    },
    'results': []
}

# 获取 web 目录的绝对路径
web_dir = os.path.dirname(os.path.abspath(__file__))

# 显式指定模板和静态文件目录
app = Flask(
    __name__,
    template_folder=os.path.join(web_dir, 'templates'),
    static_folder=os.path.join(web_dir, 'static')
)

app.secret_key = 'flappy_bird_ai_training_secret_key_2026'
USER_QDATA_DIR = os.path.join(os.path.dirname(__file__), "user_data")
os.makedirs(USER_QDATA_DIR, exist_ok=True)

def get_user_qfile():
    """返回当前用户的 Q 表文件路径"""
    if 'user_id' not in session:
        session['user_id'] = os.urandom(16).hex()
    return os.path.join(USER_QDATA_DIR, f"qvalues_{session['user_id']}.json")
# Ensure data directory exists
data_dir = os.path.join(project_root, 'data')
os.makedirs(data_dir, exist_ok=True)

@app.route('/')
def index():
    """Serve the main training interface"""
    return render_template('index.html')
@app.route('/demo')
def demo():
    """AI 演示页面"""
    return render_template('demo.html')

@app.route('/api/qvalues')
def get_qvalues():
    """提供当前用户的 Q-values 数据"""
    user_qfile = get_user_qfile()
    try:
        with open(user_qfile, 'r') as f:
            qvalues = json.load(f)
        return jsonify(qvalues)
    except FileNotFoundError:
        return jsonify({})  # 返回空对象，不报错
@app.route('/api/train', methods=['POST'])
def start_training():
    """Start a new training session with provided parameters"""
    global training_status
    
    if training_status['is_training']:
        return jsonify({
            'success': False,
            'message': 'Training is already in progress'
        }), 400
    
    try:
        # Parse request data
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['episodes', 'learning_rate', 'discount_factor']
        for param in required_params:
            if param not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required parameter: {param}'
                }), 400
        
        # Extract training parameters
        episodes = int(data['episodes'])
        learning_rate = float(data['learning_rate'])
        discount_factor = float(data['discount_factor'])
        
        # Extract reward function parameters (with defaults) - ONLY alive and death
        alive_reward = float(data.get('alive_reward', 1.0))
        death_penalty = float(data.get('death_penalty', -1000.0))
        
        # Validate parameter ranges
        if not (1 <= episodes <= 10000):
            return jsonify({
                'success': False,
                'message': 'Episodes must be between 1 and 10000'
            }), 400
        
        if not (0 < learning_rate <= 1.0):
            return jsonify({
                'success': False,
                'message': 'Learning rate must be between 0 and 1'
            }), 400
        
        if not (0 <= discount_factor <= 1.0):
            return jsonify({
                'success': False,
                'message': 'Discount factor must be between 0 and 1'
            }), 400
        
        # Reset training status
        training_status.update({
            'is_training': True,
            'current_session': {
                'start_time': datetime.now().isoformat(),
                'parameters': {
                    'episodes': episodes,
                    'learning_rate': learning_rate,
                    'discount_factor': discount_factor,
                    'alive_reward': alive_reward,
                    'death_penalty': death_penalty
                }
            },
            'progress': {
                'episode': 0,
                'total_episodes': episodes,
                'score': 0,
                'best_score': 0,
                'avg_score': 0.0
            },
            'results': []
        })
        user_qfile = get_user_qfile()
        # Start training in a separate thread
        if os.path.exists(user_qfile):
            os.remove(user_qfile)  # 删除旧 Q 表
            print(f"[INFO] Cleared existing Q-table: {user_qfile}")
        training_thread = threading.Thread(
            target=run_training_session,
            args=(episodes, learning_rate, discount_factor, alive_reward, death_penalty, user_qfile)
        )
        training_thread.daemon = True
        training_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Training started successfully',
            'session_id': training_status['current_session']['start_time']
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        training_status['is_training'] = False
        return jsonify({
            'success': False,
            'message': f'Error starting training: {str(e)}'
        }), 500

@app.route('/api/status')
def get_training_status():
    """Get current training status and progress"""
    return jsonify(training_status)

@app.route('/api/stop', methods=['POST'])
def stop_training():
    """Stop the current training session"""
    global training_status
    
    if not training_status['is_training']:
        return jsonify({
            'success': False,
            'message': 'No training session is currently running'
        }), 400
    
    training_status['is_training'] = False
    
    return jsonify({
        'success': True,
        'message': 'Training stop requested'
    })

@app.route('/api/results')
def get_training_results():
    """Get training results and statistics"""
    return jsonify({
        'results': training_status['results'],
        'final_progress': training_status['progress']
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)"""
    return send_from_directory(os.path.join(current_dir, 'static'), filename)

@app.route('/templates/<path:filename>')
def serve_template(filename):
    """This route is not typically needed as render_template handles templates"""
    return "Template access not allowed", 403

def run_training_session(episodes, learning_rate, discount_factor, alive_reward, death_penalty,user_qfile):
    """
    Run the actual training session in a separate thread
    
    Args:
        episodes (int): Number of training episodes
        learning_rate (float): Learning rate for Q-learning
        discount_factor (float): Discount factor for Q-learning  
        alive_reward (float): Reward for staying alive each frame
        death_penalty (float): Penalty for dying
    """
    global training_status
    
    try:
        # ✅ Convert to Bot's expected reward format: {0: alive_reward, 1: death_penalty}
        bot_reward_config = {0: alive_reward, 1: death_penalty}
        
        # Initialize bot and game with user parameters
        # Initialize bot with user-specific Q-table
        bot = Bot(lr=learning_rate, discount=discount_factor, r=bot_reward_config, qfile=user_qfile)
        # For game engine, we still pass the original format but only use alive and death
        game_reward_config = {'alive': alive_reward, 'score': 0.0, 'death': death_penalty}
        game = HeadlessFlappyGame(reward_function=game_reward_config)
        
        scores = []
        total_score = 0
        
        for episode in range(episodes):
            if not training_status['is_training']:
                break
                
            # Reset game for new episode
            state = game.reset()
            episode_score = 0
            
            while True:
                if not training_status['is_training']:
                    break
                    
                # Get action from bot
                action = bot.act(*state)
                
                # Step through game
                next_state, reward, done, info = game.step(action)
                episode_score = info['score']
                
                if done:
                    # Update Q-values after episode ends
                    bot.update_scores(dump_qvalues=False)
                    break
                    
                state = next_state
            
            # Update progress tracking
            scores.append(episode_score)
            total_score += episode_score
            current_best = max(scores) if scores else 0
            current_avg = total_score / (episode + 1)
            
            training_status['progress'].update({
                'episode': episode + 1,
                'score': episode_score,
                'best_score': current_best,
                'avg_score': round(current_avg, 2)
            })
            
            # Save intermediate results every 10 episodes or at the end
            if (episode + 1) % 10 == 0 or episode + 1 == episodes:
                training_status['results'].append({
                    'episode': episode + 1,
                    'score': episode_score,
                    'best_score': current_best,
                    'avg_score': round(current_avg, 2),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.01)
        
        # Final save of Q-values
        bot.dump_qvalues(force=True)
        
        # Mark training as complete
        training_status['is_training'] = False
        
    except Exception as e:
        print(f"Training error: {e}")
        import traceback
        traceback.print_exc()  # Add detailed error information
        training_status['is_training'] = False
        training_status['error'] = str(e)

def clear_old_qtables():
    """
    每 24 小时清空 user_data 目录下所有 qvalues_*.json 文件
    """
    while True:
        try:
            # 构造匹配模式
            pattern = os.path.join(USER_QDATA_DIR, "qvalues_*.json")
            qfiles = glob.glob(pattern)
            
            if qfiles:
                print(f"[AUTO-CLEAN] Found {len(qfiles)} Q-table files to remove.")
                for f in qfiles:
                    os.remove(f)
                    print(f"[AUTO-CLEAN] Deleted: {f}")
                print(f"[AUTO-CLEAN] All Q-tables cleared at {datetime.now().isoformat()}")
            else:
                print(f"[AUTO-CLEAN] No Q-table files found at {datetime.now().isoformat()}")
            
            # 等待 24 小时（86400 秒）
            time.sleep(86400)
            
        except Exception as e:
            print(f"[AUTO-CLEAN ERROR] {e}")
            # 出错后也继续尝试，避免线程退出
            time.sleep(3600)  # 1 小时后重试
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(os.path.join(current_dir, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(current_dir, 'static'), exist_ok=True)
    
    # Check if template exists, if not create a basic one
    template_path = os.path.join(current_dir, 'templates', 'index.html')
    cleaner_thread = threading.Thread(target=clear_old_qtables, daemon=True)
    cleaner_thread.start()
    print("[INFO] Auto Q-table cleaner started (runs every 24 hours).")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

