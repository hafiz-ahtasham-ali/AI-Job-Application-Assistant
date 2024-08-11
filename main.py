from flask import Flask, request, g, jsonify
from urls import DATABASE, msgs_file, cvs_folder, imgs_folder
import helpers
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
            job_details TEXT,
            draft_email TEXT,
            cost REAL DEFAULT 0.0
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
                                user_balance = user_data[7]
                                user_state = user_data[1]

                                if user_balance > 0.0166666: # 300 users can be served with 5 USD
                                    cloudapi.send_msg(from_number, 'You have insufficient balance to proceed. Please contact support at +923186491240.')
                                elif user_state == 1:
                                    if message.get("type") == "document":
                                        if message.get('document').get('mime_type') == 'application/pdf':
                                            MEDIA_ID = message.get('document').get('id')
                                            media_received = cloudapi.fetch_media_data(MEDIA_ID, from_number)
                                            if media_received:
                                                extracted_text = helpers.extract_pdf_text(f'{cvs_folder}/{from_number}.pdf')
                                                cloudapi.send_msg(from_number, 'Processing your request...')
                                                validate_cv_response = helpers.validate_cv(extracted_text)
                                                if validate_cv_response:
                                                    validate_cv_response_cost = validate_cv_response
                                                    cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(validate_cv_response_cost, from_number))
                                                    cursor.execute('UPDATE users SET cv = ? WHERE WhatsAppNumber = ?', (extracted_text, from_number))
                                                    cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (2, from_number))
                                                    cloudapi.send_btn_msg(from_number, f"Got your CV! 📄 We’re ready to help you with your job applications.", ['Upload Job Details'])
                                                else:
                                                    cloudapi.send_msg(from_number, 'It seems the uploaded file is not a CV. Please upload a CV in PDF format.')
                                            else:
                                                cloudapi.send_msg(from_number, 'Please upload a CV in PDF format.')
                                        else:
                                            cloudapi.send_msg(from_number, 'Please upload a CV in PDF format.')
                                    else:
                                        cloudapi.send_msg(from_number, 'Please upload a CV in PDF format.')
                                elif user_state == 2:
                                    if message.get("type") == 'interactive':
                                        if message.get("interactive").get("type") == 'button_reply':
                                            button_msg_id = message.get("interactive").get("button_reply").get("id")
                                            if button_msg_id == 'btn_id_1':
                                                cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (3, from_number))
                                                cloudapi.send_msg(from_number, """📥 Great! Please provide the job details so I can help create your application email.

You can type these details directly, upload an image, or upload a document with the information.""")
                                elif user_state == 3:
                                    if message.get("type") == 'image':
                                        MEDIA_ID = message.get("image").get("id")
                                        media_received = cloudapi.fetch_image_data(MEDIA_ID, from_number)
                                        if media_received:
                                            cloudapi.send_msg(from_number, 'Processing your request...')
                                            extract_text_from_img_response = helpers.extract_text_from_img(f'{imgs_folder}/{from_number}.jpg')
                                            job_details = extract_text_from_img_response.get('content')
                                            extract_text_from_img_cost = extract_text_from_img_response.get('cost')
                                            cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(extract_text_from_img_cost, from_number))
                                            validate_job_response = helpers.validate_job(job_details)
                                            if validate_job_response:
                                                validate_job_response_cost = validate_job_response
                                                cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(validate_job_response_cost, from_number))
                                                cursor.execute('UPDATE users SET job_details = ? WHERE WhatsAppNumber = ?', (job_details, from_number))
                                                cloudapi.send_msg(from_number, """Great! I’m preparing your application email based on the job details provided. 🛠️ You’ll get a draft soon. You can:

    1. *Make Adjustments:* Type any changes you'd like to make to the draft.
    2. *Confirm Draft:* Press the 'Confirm' button if everything looks good.""")
                                                create_draft_email_response = helpers.create_draft_email(user_data[4], job_details)
                                                darft_email = create_draft_email_response.get('content')
                                                create_draft_email_cost = create_draft_email_response.get('cost')
                                                cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(create_draft_email_cost, from_number))
                                                cursor.execute('UPDATE users SET draft_email = ? WHERE WhatsAppNumber = ?', (darft_email, from_number))
                                                cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (4, from_number))
                                                cloudapi.send_msg(from_number, darft_email)
                                                cloudapi.send_btn_msg(from_number, "Type any changes you'd like to make to the draft or press the 'Confirm' button below if everything looks good.", ['Confirm Draft'])
                                            else:
                                                cloudapi.send_msg(from_number, '⚠️ It looks like your message didn’t include the job details. Please share the job details either in text or as an image.')
                                        else:
                                            cloudapi.send_msg(from_number, 'Error processing image. Please upload a clear image of the job details.')
                                    elif message.get("type") == 'text':
                                        job_details = message.get("text").get("body")
                                        validate_job_response = helpers.validate_job(job_details)
                                        if validate_job_response:
                                            validate_job_response_cost = validate_job_response
                                            cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(validate_job_response_cost, from_number))
                                            cursor.execute('UPDATE users SET job_details = ? WHERE WhatsAppNumber = ?', (job_details, from_number))
                                            cloudapi.send_msg(from_number, """Great! I’m preparing your application email based on the job details provided. 🛠️ You’ll get a draft soon. You can:

1. *Make Adjustments:* Type any changes you'd like to make to the draft.
2. *Confirm Draft:* Press the 'Confirm' button if everything looks good.""")
                                            create_draft_email_response = helpers.create_draft_email(user_data[4], job_details)
                                            darft_email = create_draft_email_response.get('content')
                                            create_draft_email_cost = create_draft_email_response.get('cost')
                                            cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(create_draft_email_cost, from_number))
                                            cursor.execute('UPDATE users SET draft_email = ? WHERE WhatsAppNumber = ?', (darft_email, from_number))
                                            cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (4, from_number))
                                            cloudapi.send_msg(from_number, darft_email)
                                            cloudapi.send_btn_msg(from_number, "Type any changes you'd like to make to the draft or press the 'Confirm' button below if everything looks good.", ['Confirm Draft'])
                                        else:
                                            cloudapi.send_msg(from_number, '⚠️ It looks like your message didn’t include the job details. Please share the job details either in text or as an image.')
                                    else:
                                        cloudapi.send_msg(from_number, '⚠️ It looks like your message didn’t include the job details. Please share the job details either in text or as an image.')
                                elif user_state == 4:
                                    if message.get("type") == 'text':
                                        cloudapi.send_msg(from_number, 'Processing your request...')
                                        user_prompt = message.get("text").get("body")
                                        adjust_email_draft_response = helpers.adjust_email_draft(user_data[6], user_prompt)
                                        darft_email = adjust_email_draft_response.get('content')
                                        adjust_email_draft_cost = adjust_email_draft_response.get('cost')
                                        cursor.execute('''UPDATE users SET cost = cost + ? WHERE WhatsAppNumber = ?''',(adjust_email_draft_cost, from_number))
                                        cloudapi.send_msg(from_number, darft_email)
                                        cloudapi.send_btn_msg(from_number, "Type any changes you'd like to make to the draft or press the 'Confirm' button below if everything looks good.", ['Confirm Draft'])
                                        cursor.execute('UPDATE users SET draft_email = ? WHERE WhatsAppNumber = ?', (darft_email, from_number))
                                        cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (4, from_number))
                                    if message.get("type") == 'interactive':
                                        if message.get("interactive").get("type") == 'button_reply':
                                            button_msg_id = message.get("interactive").get("button_reply").get("id")
                                            if button_msg_id == 'btn_id_1':
                                                cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (5, from_number))
                                                cloudapi.send_msg(from_number, "Your draft has been finalized! 🎉 You can copy this draft and send it. Say '*Hi*' to share more job details.")
                                elif user_state == 5:
                                    cursor.execute('UPDATE users SET UserState = ? WHERE WhatsAppNumber = ?', (2, from_number))
                                    cloudapi.send_btn_msg(from_number, '👋 Hi again! How can I assist you today?', ['Upload Job Details'])
                            else:
                                query = 'INSERT INTO users (UserState, WhatsAppNumber, name) VALUES (?, ?, ?)'
                                cursor.execute(query, (1, from_number, full_name))
                                cloudapi.send_msg(from_number, f"👋 Hello *{first_name}*! I’m your Job Application Email Bot. To get started, I’ll need to create an account for you. Please upload your CV first, and then I’ll guide you through setting up your profile.")

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