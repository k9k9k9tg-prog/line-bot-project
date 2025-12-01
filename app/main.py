from flask import Flask, request, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os, json, time, re
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    picture_url = db.Column(db.String(255))

class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    steps = db.Column(db.JSON, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False) # incoming, outgoing, auto, notify
    timestamp = db.Column(db.Integer, nullable=False)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    step = db.Column(db.Integer, default=0)
    variables = db.Column(db.JSON, default=dict)

class KeyValueStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

auth = HTTPBasicAuth()

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")

@auth.verify_password
def verify_password(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPERATOR_ID = os.getenv("OPERATOR_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# --- Admin Panel ---
@app.route('/admin')
@auth.login_required
def admin_panel():
    return render_template('admin.html')

# --- Operator View ---
@app.route('/operator')
@auth.login_required
def operator_view():
    return render_template('operator.html')

# --- Scenario Editor ---
@app.route('/editor')
@auth.login_required
def scenario_editor():
    return render_template('editor.html')

def substitute_variables(data, variables):
    """
    Recursively substitutes placeholders in strings, dictionaries, or lists.
    e.g., "Hello {{name}}" with variables {"name": "World"} becomes "Hello World".
    """
    if isinstance(data, str):
        for key, value in variables.items():
            data = data.replace(f"{{{{{key}}}}}", str(value))
        return data
    elif isinstance(data, dict):
        return {k: substitute_variables(v, variables) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_variables(item, variables) for item in data]
    else:
        return data

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        events = parser.parse(body, signature)
    except Exception as e:
        app.logger.error(f"Error parsing webhook: {e}")
        return "Error", 400

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_id = event.source.user_id
            
            user = User.query.filter_by(line_user_id=user_id).first()
            if not user:
                try:
                    profile = line_bot_api.get_profile(user_id)
                    new_user = User(line_user_id=user_id, display_name=profile.display_name, picture_url=profile.picture_url or "")
                    db.session.add(new_user)
                    db.session.commit()
                    user = new_user
                    socketio.emit('new_user', {"line_user_id": user.line_user_id, "display_name": user.display_name, "picture_url": user.picture_url})
                except Exception:
                    fallback_user = User(line_user_id=user_id, display_name="Unknown User", picture_url="")
                    db.session.add(fallback_user)
                    db.session.commit()
                    user = fallback_user
                    socketio.emit('new_user', {"line_user_id": user.line_user_id, "display_name": user.display_name, "picture_url": user.picture_url})

            db.session.add(Message(user_id=user_id, text=event.message.text, type="incoming", timestamp=int(time.time())))
            db.session.commit()
            socketio.emit('new_message', {"user_id": user_id, "text": event.message.text, "type": "incoming", "timestamp": int(time.time())})

            current_scenario_entry = KeyValueStore.query.filter_by(key='current_scenario_name').first()
            current_scenario_name = current_scenario_entry.value if current_scenario_entry else 'default'
            
            scenario_obj = Scenario.query.filter_by(name=current_scenario_name).first()
            user_progress = UserProgress.query.filter_by(user_id=user_id).first()

            if not user_progress:
                user_progress = UserProgress(user_id=user_id, scenario_name=current_scenario_name, step=0, variables={})
                db.session.add(user_progress)
                db.session.commit()
            
            if not scenario_obj or not scenario_obj.steps:
                return "OK"

            steps = scenario_obj.steps
            
            # --- New Scenario Engine ---

            # 1. Process user's answer to a previous input step
            if user_progress.step < len(steps):
                previous_step_data = steps[user_progress.step]
                if isinstance(previous_step_data, dict):
                    previous_step_type = previous_step_data.get("type")
                    if previous_step_type == "input_text":
                        variable_name = previous_step_data.get("save_as")
                        if variable_name:
                            if user_progress.variables is None:
                                user_progress.variables = {}
                            new_variables = dict(user_progress.variables)
                            new_variables[variable_name] = event.message.text
                            user_progress.variables = new_variables
                        user_progress.step += 1
                        db.session.commit()
            
            # 2. Execute next steps until we need to wait for user input
            while user_progress.step < len(steps):
                current_step_data = steps[user_progress.step]
                step_type = None
                
                if isinstance(current_step_data, str):
                    step_type = "message"
                    current_step_data = {"content": current_step_data}
                elif isinstance(current_step_data, dict):
                    step_type = current_step_data.get("type", "message")

                # Get user variables, ensure it's a dictionary
                user_vars = user_progress.variables if isinstance(user_progress.variables, dict) else {}

                # --- Step Execution ---

                if step_type == "message":
                    content = substitute_variables(current_step_data.get("content"), user_vars)
                    if content:
                        line_bot_api.push_message(user_id, TextSendMessage(text=content))
                        auto_message = Message(user_id=user_id, text=content, type="auto", timestamp=int(time.time()))
                        db.session.add(auto_message)
                        socketio.emit('new_message', {"user_id": user_id, "text": content, "type": "auto", "timestamp": int(time.time())})
                    user_progress.step += 1
                    db.session.commit()

                elif step_type == "input_text":
                    prompt = substitute_variables(current_step_data.get("prompt"), user_vars)
                    if prompt:
                        line_bot_api.push_message(user_id, TextSendMessage(text=prompt))
                        auto_message = Message(user_id=user_id, text=prompt, type="auto", timestamp=int(time.time()))
                        db.session.add(auto_message)
                        socketio.emit('new_message', {"user_id": user_id, "text": prompt, "type": "auto", "timestamp": int(time.time())})
                    db.session.commit()
                    break # Wait for user's text input

                elif step_type == "api_call":
                    url = substitute_variables(current_step_data.get("url"), user_vars)
                    method = current_step_data.get("method", "GET").upper()
                    body = substitute_variables(current_step_data.get("body"), user_vars)
                    
                    try:
                        app.logger.info(f"Executing API call to {url} with method {method}")
                        if method == "POST":
                            response = requests.post(url, json=body)
                        else:
                            response = requests.get(url)
                        response.raise_for_status()
                        # TODO: Add logic to save response to a variable
                    except requests.RequestException as e:
                        app.logger.error(f"API call failed: {e}")
                    
                    user_progress.step += 1
                    db.session.commit()

                else:
                    app.logger.warning(f"Unknown or unimplemented step type: {step_type}")
                    user_progress.step += 1
                    db.session.commit()
            
            # --- End of Scenario ---
            if user_progress.step >= len(steps):
                notify_text = f"{user.display_name} がシナリオを完了しました。"
                try:
                    line_bot_api.push_message(OPERATOR_ID, TextSendMessage(text=notify_text))
                    db.session.add(Message(user_id=OPERATOR_ID, text=notify_text, type="notify", timestamp=int(time.time())))
                except Exception as e:
                    app.logger.error(f"Failed to send notification to operator: {e}")
                user_progress.step = 0
                user_progress.variables = {}
                db.session.commit()

    return "OK"

def load_initial_data():
    with app.app_context():
        if User.query.first() is not None:
            print("Database already has data. Skipping data loading.")
            return

        print("Loading initial data...")

        # Load users
        with open('users.json', 'r') as f:
            users_data = json.load(f)
            for user_id, user_info in users_data.items():
                user = User(line_user_id=user_id, display_name=user_info['name'], picture_url=user_info['picture'])
                db.session.add(user)

        # Load scenarios
        with open('scenarios.json', 'r') as f:
            scenarios_data = json.load(f)
            for name, steps in scenarios_data.items():
                scenario = Scenario(name=name, steps=steps)
                db.session.add(scenario)

        # Load messages
        with open('messages.json', 'r') as f:
            messages_data = json.load(f)
            for msg_data in messages_data:
                message = Message(user_id=msg_data['user_id'], text=msg_data['text'], type=msg_data['type'], timestamp=msg_data['timestamp'])
                db.session.add(message)

        # Load current scenario
        with open('current_scenario.json', 'r') as f:
            current_scenario_data = json.load(f)
            kv = KeyValueStore(key='current_scenario_name', value=current_scenario_data['current'])
            db.session.add(kv)
        
        db.session.commit()
        print("Initial data loaded.")

def init_database():
    """Creates the database tables if they don't exist."""
    with app.app_context():
        # Create the directory if it doesn't exist
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        db.create_all()
        print("Database initialized.")

if __name__ == "__main__":
    init_database()
    load_initial_data()
    socketio.run(app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), allow_unsafe_werkzeug=True)