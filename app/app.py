from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app)

DATABASE = 'messages.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Create the messages table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id TEXT,
                        customer_name TEXT,
                        customer_message TEXT
                    )''')
    
    # Check if the 'direction' column exists
    cursor.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'direction' not in columns:
        # Add the 'direction' column if it doesn't exist
        cursor.execute("ALTER TABLE messages ADD COLUMN direction TEXT")
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message')
def send_message_page():
    return render_template('send_message.html')

@app.route('/customers')
def customer_page():
    return render_template('messages.html')

@app.route('/customers_list')
def customers():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT customer_id, customer_name FROM messages WHERE customer_name != "Server"')
    customers = cursor.fetchall()
    conn.close()
    print(customers)
    return jsonify(customers)

@app.route('/messages')
def messages():
    customer_id = request.args.get('customer_id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    if customer_id:
        cursor.execute('SELECT * FROM messages WHERE customer_id = ?', (customer_id,))
    else:
        cursor.execute('SELECT * FROM messages')
    messages = cursor.fetchall()
    conn.close()

    messages_list = []
    for message in messages:
        messages_list.append({
            'id': message[0],
            'customer_id': message[1],
            'customer_name': message[2],
            'customer_message': message[3],
            'direction': message[4]
        })
    
    return jsonify(messages_list)

@app.route('/receive_message', methods=['POST'])
def receive_message():
    data = request.json
    customer_id = data['customer_id']
    customer_name = data['customer_name']
    customer_message = data['customer_message']

    if not (customer_id and customer_name and customer_message):
        return jsonify({'error': 'Invalid data'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (customer_id, customer_name, customer_message, direction) VALUES (?, ?, ?, ?)',
                   (customer_id, customer_name, customer_message, 'received'))
    conn.commit()
    conn.close()
    print('Message received')
    socketio.emit('new_message', {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'customer_message': customer_message,
        'direction': 'received'
    })

    return jsonify({'status': 'Message received'}), 200

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    customer_id = data['customer_id']
    customer_name = data['customer_name']
    customer_message = data['customer_message']

    if not (customer_id and customer_message):
        return jsonify({'error': 'Invalid data'}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (customer_id, customer_name, customer_message, direction) VALUES (?, ?, ?, ?)',
                   (customer_id, "Server", customer_message, 'sent'))  # Leave customer_name empty for server messages
    conn.commit()
    conn.close()

    socketio.emit('new_message', {
        'customer_id': customer_id,
        'customer_name': "Server",  # Send 'Server' as the name in the emit message
        'customer_message': customer_message,
        'direction': 'sent'
    })

    return jsonify({'status': 'Message sent'}), 200



@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# if __name__ == '__main__':
#     init_db()
#     socketio.run(app, debug=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=False, host='0.0.0.0')