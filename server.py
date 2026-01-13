from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import shelve
import threading

# Initialize Flask app
app = Flask(__name__)

# Lock for thread-safe operations
lock = threading.Lock()

# Shelve database file
DB_FILE = 'data.db'

# Set a secret key for session management
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# Sanity test print
print("Server is starting...")

# API Routes

# Serve the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Serve the login page
@app.route('/login')
def login_page():
    return render_template('login.html')

# Serve the register page
@app.route('/register')
def register_page():
    return render_template('register.html')

# Serve the profile page
@app.route('/profile')
def profile_page():
    return render_template('profile.html')

# Serve the home page
@app.route('/home')
def home_page():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('home.html', username=session['username'])

# Register a new user
@app.route('/auth/register', methods=['POST'])
def register():
    print("Register endpoint hit")  # Sanity test output
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    with lock, shelve.open(DB_FILE) as db:
        if username in db.get('users', {}):
            return jsonify({"error": "User already exists"}), 400

        users = db.get('users', {})
        users[username] = {"password": password, "posts": []}
        db['users'] = users

    return redirect(url_for('home_page'))

# Log in a user
@app.route('/auth/login', methods=['POST'])
def login():
    print("Login endpoint hit")  # Sanity test output
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    with lock, shelve.open(DB_FILE) as db:
        users = db.get('users', {})
        user = users.get(username)
        if not user or user['password'] != password:
            return jsonify({"error": "Invalid credentials"}), 401

    # Set session cookie
    session['username'] = username
    return redirect(url_for('home_page'))

# Create a new post
@app.route('/posts', methods=['POST'])
def create_post():
    print("Create post endpoint hit")  # Sanity test output
    data = request.json
    username = data.get('username')
    content = data.get('content')

    if not username or not content:
        return jsonify({"error": "Username and content are required"}), 400

    with lock, shelve.open(DB_FILE) as db:
        users = db.get('users', {})
        if username not in users:
            return jsonify({"error": "User does not exist"}), 404

        posts = db.get('posts', [])
        post_id = len(posts) + 1
        post = {"id": post_id, "username": username, "content": content, "likes": 0, "replies": []}
        posts.append(post)
        db['posts'] = posts

    return jsonify({"message": "Post created successfully", "post": post}), 201

# Fetch the global feed
@app.route('/posts', methods=['GET'])
def get_posts():
    print("Get posts endpoint hit")  # Sanity test output
    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
    return jsonify(posts), 200

# Like a post
@app.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    print("Like post endpoint hit")  # Sanity test output
    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        for post in posts:
            if post['id'] == post_id:
                post['likes'] += 1
                db['posts'] = posts
                return jsonify({"message": "Post liked successfully"}), 200
        return jsonify({"error": "Post not found"}), 404

# Reply to a post
@app.route('/posts/<int:post_id>/reply', methods=['POST'])
def reply_to_post(post_id):
    print("Reply to post endpoint hit")  # Sanity test output
    data = request.json
    username = data.get('username')
    content = data.get('content')

    if not username or not content:
        return jsonify({"error": "Username and content are required"}), 400

    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        for post in posts:
            if post['id'] == post_id:
                reply = {"username": username, "content": content}
                post['replies'].append(reply)
                db['posts'] = posts
                return jsonify({"message": "Reply added successfully"}), 200
        return jsonify({"error": "Post not found"}), 404

# Fetch a user’s profile and posts
@app.route('/users/<username>', methods=['GET'])
def get_user_profile(username):
    print("Get user profile endpoint hit")  # Sanity test output
    with lock, shelve.open(DB_FILE) as db:
        users = db.get('users', {})
        user = users.get(username)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_posts = [post for post in db.get('posts', []) if post['username'] == username]

    return jsonify({"user": user, "posts": user_posts}), 200

# Add a route for logging out
@app.route('/auth/logout', methods=['GET'])
def logout():
    print("Logout endpoint hit")  # Sanity test output
    session.pop('username', None)
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    print("Starting Flask app...")  # Sanity test output
    app.run(debug=True, threaded=True)