from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app)

DATABASE = 'messages.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id TEXT,
                        customer_name TEXT,
                        customer_message TEXT
                    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message')
def send_message_page():
    return render_template('send_message.html')

@app.route('/messages')
def messages():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages')
    messages = cursor.fetchall()
    conn.close()

    messages_list = []
    for message in messages:
        messages_list.append({
            'id': message[0],
            'customer_id': message[1],
            'customer_name': message[2],
            'customer_message': message[3]
        })
    
    return render_template('messages.html', messages=messages_list)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    customer_id = data['customer_id']
    customer_name = data['customer_name']
    customer_message = data['customer_message']

    if not (customer_id and customer_name and customer_message):
        return jsonify({'error': 'Invalid data'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (customer_id, customer_name, customer_message) VALUES (?, ?, ?)',
                   (customer_id, customer_name, customer_message))
    conn.commit()
    conn.close()

    socketio.emit('new_message', {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'customer_message': customer_message
    })

    return jsonify({'status': 'Message received'}), 200

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
