from flask import Flask, request, g, jsonify
from urls import DATABASE, msgs_file
import json
import sqlite3
import cloudapi

app = Flask(__name__)

# Load messages from msg.json
try:
    with open(msgs_file, encoding='utf-8') as f:
        messages = json.load(f)
except FileNotFoundError:
    print("Error: msg.json or instructor.json_msgs not found.")
    messages = {}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def incoming():
    # print(request.json['entry'])
    # return jsonify({'message': 'success'}), 200
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            UserState INTEGER,
            WhatsAppNumber TEXT,
            name TEXT,
            cv TEXT,
            temp_job_details TEXT,
            draft_email TEXT
        )
    ''')

    if request.method == 'POST':
        entries = request.json['entry']
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value")
                if value is not None:
                    if value.get("messages") is not None:
                        for msg_idx, message in enumerate(value.get("messages")):
                            full_name = value.get("contacts")[msg_idx].get("profile").get("name")
                            first_name = full_name.split(' ')[0]
                            from_number = message.get("from")

                            # Check if user is already in the database
                            cursor.execute('SELECT * FROM users WHERE WhatsAppNumber = ?', (from_number,))
                            user_data = cursor.fetchone()
                            
                            if user_data is not None:
                                pass
                            else:
                                pass

        db.commit()
        cursor.close()
        return jsonify({'message': 'success'}), 200
    else:
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == 'token':
            return request.args.get('hub.challenge')
        else:
            return 'Invalid verification token'

if __name__ == '__main__':
    app.run(debug=True)

# git add .
# git commit -m "Your commit message here"
# git push origin active