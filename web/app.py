# app.py
"""
Flappy Bird AI Training Web Application
Provides REST API for configuring and running Q-learning training sessions
"""

import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in os.sys.path:
    os.sys.path.insert(0, project_root)

try:
    from src.bot import Bot
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
    """提供训练好的 Q-values 数据"""
    qvalues_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'qvalues.json')
    try:
        with open(qvalues_path, 'r') as f:
            qvalues = json.load(f)
        return jsonify(qvalues)
    except FileNotFoundError:
        return jsonify({}), 404
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
        
        # Start training in a separate thread
        training_thread = threading.Thread(
            target=run_training_session,
            args=(episodes, learning_rate, discount_factor, alive_reward, death_penalty)
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

def run_training_session(episodes, learning_rate, discount_factor, alive_reward, death_penalty):
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
        bot = Bot(lr=learning_rate, discount=discount_factor, r=bot_reward_config)
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
    if not os.path.exists(template_path):
        create_basic_template()
    
    app.run(debug=True, host='0.0.0.0', port=5000)

def create_basic_template():
    """Create a basic HTML template if it doesn't exist"""
    template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flappy Bird AI Trainer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, button { padding: 8px; margin: 5px; width: 200px; }
        button { background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
        .status { margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px; }
        .progress-bar { width: 100%; height: 20px; background: #ddd; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #4CAF50; transition: width 0.3s; }
    </style>
</head>
<body>
    <h1>Flappy Bird AI Trainer</h1>
    
    <div class="form-group">
        <label for="episodes">Episodes:</label>
        <input type="number" id="episodes" value="100" min="1" max="10000">
    </div>
    
    <div class="form-group">
        <label for="learning_rate">Learning Rate:</label>
        <input type="number" id="learning_rate" value="0.7" step="0.1" min="0.1" max="1.0">
    </div>
    
    <div class="form-group">
        <label for="discount_factor">Discount Factor:</label>
        <input type="number" id="discount_factor" value="1.0" step="0.1" min="0" max="1.0">
    </div>
    
    <div class="form-group">
        <label for="alive_reward">Alive Reward:</label>
        <input type="number" id="alive_reward" value="1.0" step="0.1">
    </div>
    
    <!-- Removed score_reward input -->
    
    <div class="form-group">
        <label for="death_penalty">Death Penalty:</label>
        <input type="number" id="death_penalty" value="-1000.0" step="10">
    </div>
    
    <button onclick="startTraining()">Start Training</button>
    <button onclick="stopTraining()">Stop Training</button>
    
    <div id="status" class="status">
        <h3>Training Status</h3>
        <div id="progress-text">Not training</div>
        <div class="progress-bar">
            <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
        </div>
        <div id="results"></div>
    </div>

    <script>
        let trainingInterval = null;
        
        async function startTraining() {
            const params = {
                episodes: parseInt(document.getElementById('episodes').value),
                learning_rate: parseFloat(document.getElementById('learning_rate').value),
                discount_factor: parseFloat(document.getElementById('discount_factor').value),
                alive_reward: parseFloat(document.getElementById('alive_reward').value),
                // Removed score_reward
                death_penalty: parseFloat(document.getElementById('death_penalty').value)
            };
            
            try {
                const response = await fetch('/api/train', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(params)
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Training started!');
                    startStatusPolling();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Error starting training: ' + error.message);
            }
        }
        
        async function stopTraining() {
            try {
                await fetch('/api/stop', {method: 'POST'});
                clearInterval(trainingInterval);
                updateStatus({is_training: false});
            } catch (error) {
                alert('Error stopping training: ' + error.message);
            }
        }
        
        function startStatusPolling() {
            trainingInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/status');
                    const status = await response.json();
                    updateStatus(status);
                    
                    if (!status.is_training) {
                        clearInterval(trainingInterval);
                    }
                } catch (error) {
                    console.error('Error fetching status:', error);
                }
            }, 1000);
        }
        
        function updateStatus(status) {
            const progressText = document.getElementById('progress-text');
            const progressFill = document.getElementById('progress-fill');
            const resultsDiv = document.getElementById('results');
            
            if (status.is_training && status.progress) {
                const progress = status.progress;
                const percent = (progress.episode / progress.total_episodes) * 100;
                progressFill.style.width = percent + '%';
                progressText.innerHTML = `
                    Episode: ${progress.episode}/${progress.total_episodes}<br>
                    Current Score: ${progress.score}<br>
                    Best Score: ${progress.best_score}<br>
                    Average Score: ${progress.avg_score}
                `;
            } else {
                progressFill.style.width = '0%';
                progressText.innerHTML = 'Not training';
            }
        }
    </script>
</body>
</html>
'''
    
    with open(template_path, 'w') as f:
        f.write(template_content)