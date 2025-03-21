from flask import Flask, request, render_template_string
import requests
import random
import time
import threading

app = Flask(__name__)

# ✅ **Random User-Agents**
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36"
]

# ✅ **HTML Form**
HTML_FORM = '''
<html>
    <head>
        <title>Facebook Auto Comment & Message</title>
    </head>
    <body>
        <h2>Facebook Auto Comment & Message (Multi-Token)</h2>
        <form action="/submit" method="post" enctype="multipart/form-data">
            Token File: <input type="file" name="token_file" required><br>
            Comment File: <input type="file" name="comment_file" required><br>
            Message File: <input type="file" name="message_file" required><br>
            Post URL: <input type="text" name="post_url" required><br>
            Convo ID: <input type="text" name="convo_id" required><br>
            Interval (Seconds): <input type="number" name="interval" value="400" required><br>
            <input type="submit" value="Start">
        </form>
        <br>
        {% if message %}
            <p>{{ message }}</p>
        {% endif %}
    </body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

@app.route('/submit', methods=['POST'])
def submit():
    token_file = request.files['token_file']
    comment_file = request.files['comment_file']
    message_file = request.files['message_file']
    post_url = request.form['post_url']
    convo_id = request.form['convo_id']
    interval = int(request.form['interval'])

    tokens = token_file.read().decode('utf-8').splitlines()
    comments = comment_file.read().decode('utf-8').splitlines()
    messages = message_file.read().decode('utf-8').splitlines()

    if not tokens or not comments or not messages:
        return render_template_string(HTML_FORM, message="❌ Files Empty!")

    try:
        post_id = post_url.split("posts/")[1].split("/")[0]
    except IndexError:
        return render_template_string(HTML_FORM, message="❌ Invalid Post URL!")

    comment_url = f"https://graph.facebook.com/{post_id}/comments"
    message_url = f"https://graph.facebook.com/{convo_id}/messages"
    blocked_tokens = set()

    def post_comment(token, comment):
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        payload = {'message': comment, 'access_token': token}

        response = requests.post(comment_url, data=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Comment Success - {comment}")
        elif "error" in response.json() and "OAuthException" in response.text:
            blocked_tokens.add(token)
            print(f"❌ Token Blocked! Skipping... ({token[:10]}...)")
        else:
            print(f"❌ Failed - {response.text}")

    def send_message(token, message):
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        payload = {'message': message, 'access_token': token}

        response = requests.post(message_url, data=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Message Sent - {message}")
        else:
            print(f"❌ Message Failed - {response.text}")

    def start_commenting():
        while True:
            for token in tokens:
                if token in blocked_tokens:
                    continue  
                comment = random.choice(comments)
                post_comment(token, comment)
                time.sleep(interval)

    def start_messaging():
        while True:
            for token in tokens:
                if token in blocked_tokens:
                    continue
                message = random.choice(messages)
                send_message(token, message)
                time.sleep(interval)

    threading.Thread(target=start_commenting).start()
    threading.Thread(target=start_messaging).start()

    return render_template_string(HTML_FORM, message="✅ Process Started!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
