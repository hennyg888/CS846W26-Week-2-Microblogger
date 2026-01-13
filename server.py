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
def landing_page():
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
    if 'username' not in session:
        return redirect(url_for('landing_page'))
    username = session['username']
    current_user = session.get('username')
    with lock, shelve.open(DB_FILE) as db:
        posts = [post for post in db.get('posts', []) if post['username'] == username]
    return render_template('profile.html', username=username, posts=posts, view_only=False, current_user=current_user)

# Serve the home page
@app.route('/home', methods=['GET', 'POST'])
def home_page():
    if 'username' not in session:
        return redirect(url_for('landing_page'))

    if request.method == 'POST':
        content = request.form.get('content')
        if not content or len(content) > 150:
            return render_template('home.html', username=session['username'], error="Post must be 150 characters or less.")

        with lock, shelve.open(DB_FILE) as db:
            posts = db.get('posts', [])
            next_id = max([p.get('id', 0) for p in posts], default=0) + 1
            post = {"id": next_id, "username": session['username'], "content": content, "likes": 0, "replies": [], "liked_by": []}
            posts.insert(0, post)  # Add the post to the top for chronological order
            db['posts'] = posts

    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        # Normalize post schema for older posts (ensure id, likes, replies, liked_by)
        updated = False
        next_id = max([p.get('id', 0) for p in posts], default=0)
        for p in posts:
            if 'id' not in p:
                next_id += 1
                p['id'] = next_id
                updated = True
            if 'likes' not in p:
                p['likes'] = 0
                updated = True
            if 'replies' not in p:
                p['replies'] = []
                updated = True
            if 'liked_by' not in p:
                p['liked_by'] = []
                updated = True
            # Normalize replies
            for idx, r in enumerate(p.get('replies', [])):
                if 'id' not in r:
                    # assign incremental reply ids per post starting from 1
                    r['id'] = idx + 1
                    updated = True
                if 'likes' not in r:
                    r['likes'] = 0
                    updated = True
                if 'liked_by' not in r:
                    r['liked_by'] = []
                    updated = True
        if updated:
            db['posts'] = posts

    return render_template('home.html', username=session['username'], posts=posts) 

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
        next_id = max([p.get('id', 0) for p in posts], default=0) + 1
        post = {"id": next_id, "username": username, "content": content, "likes": 0, "replies": [], "liked_by": []}
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
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        # Try to find by id using .get to avoid KeyError
        for post in posts:
            if post.get('id') == post_id:
                liked_by = post.get('liked_by', [])
                if username in liked_by:
                    return jsonify({"error": "Already liked"}), 400
                liked_by.append(username)
                post['liked_by'] = liked_by
                post['likes'] = post.get('likes', 0) + 1
                db['posts'] = posts
                return jsonify({"message": "Post liked successfully", "likes": post['likes'], "liked": True}), 200
        # If no match, attempt to migrate old posts by assigning ids, then retry
        updated = False
        next_id = max([p.get('id', 0) for p in posts], default=0)
        for p in posts:
            if 'id' not in p:
                next_id += 1
                p['id'] = next_id
                if 'likes' not in p:
                    p['likes'] = 0
                if 'replies' not in p:
                    p['replies'] = []
                if 'liked_by' not in p:
                    p['liked_by'] = []
                updated = True
        if updated:
            db['posts'] = posts
            # retry
            for post in posts:
                if post.get('id') == post_id:
                    liked_by = post.get('liked_by', [])
                    if username in liked_by:
                        return jsonify({"error": "Already liked"}), 400
                    liked_by.append(username)
                    post['liked_by'] = liked_by
                    post['likes'] = post.get('likes', 0) + 1
                    db['posts'] = posts
                    return jsonify({"message": "Post liked successfully", "likes": post['likes'], "liked": True}), 200
        return jsonify({"error": "Post not found"}), 404

# Reply to a post
@app.route('/posts/<int:post_id>/reply', methods=['POST'])
def reply_to_post(post_id):
    print("Reply to post endpoint hit")  # Sanity test output
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    # Accept JSON or form data
    data = request.json or request.form
    content = data.get('content')

    if not content or len(content) > 150:
        return jsonify({"error": "Content required and must be 150 characters or less"}), 400

    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        for post in posts:
            if post.get('id') == post_id:
                replies = post.get('replies', [])
                next_rid = max([r.get('id', 0) for r in replies], default=0) + 1
                reply = {"id": next_rid, "username": username, "content": content, "likes": 0, "liked_by": []}
                replies.append(reply)
                post['replies'] = replies
                db['posts'] = posts
                return jsonify({"message": "Reply added successfully", "reply": reply}), 201
        return jsonify({"error": "Post not found"}), 404

# Fetch a user’s profile and posts (view-only)
@app.route('/users/<username>', methods=['GET'])
def get_user_profile(username):
    print("Get user profile endpoint hit")  # Sanity test output
    current_user = session.get('username')
    with lock, shelve.open(DB_FILE) as db:
        users = db.get('users', {})
        user = users.get(username)
        if not user:
            return "User not found", 404

        user_posts = [post for post in db.get('posts', []) if post['username'] == username]

    return render_template('profile.html', username=username, posts=user_posts, view_only=True, current_user=current_user)

# Add a route for logging out
@app.route('/logout', methods=['GET'])
def logout():
    print("Logout endpoint hit")  # Sanity test output
    session.pop('username', None)
    return redirect(url_for('landing_page'))

# Unlike a post
@app.route('/posts/<int:post_id>/unlike', methods=['POST'])
def unlike_post(post_id):
    print("Unlike post endpoint hit")  # Sanity test output
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        for post in posts:
            if post.get('id') == post_id:
                liked_by = post.get('liked_by', [])
                if username not in liked_by:
                    return jsonify({"error": "Not liked"}), 400
                liked_by.remove(username)
                post['liked_by'] = liked_by
                post['likes'] = max(post.get('likes', 1) - 1, 0)
                db['posts'] = posts
                return jsonify({"message": "Post unliked successfully", "likes": post['likes'], "liked": False}), 200
        return jsonify({"error": "Post not found"}), 404

# Like a reply
@app.route('/posts/<int:post_id>/replies/<int:reply_id>/like', methods=['POST'])
def like_reply(post_id, reply_id):
    print("Like reply endpoint hit")
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        for post in posts:
            if post.get('id') == post_id:
                for reply in post.get('replies', []):
                    if reply.get('id') == reply_id:
                        liked_by = reply.get('liked_by', [])
                        if username in liked_by:
                            return jsonify({"error": "Already liked"}), 400
                        liked_by.append(username)
                        reply['liked_by'] = liked_by
                        reply['likes'] = reply.get('likes', 0) + 1
                        db['posts'] = posts
                        return jsonify({"message": "Reply liked successfully", "likes": reply['likes'], "liked": True}), 200
                return jsonify({"error": "Reply not found"}), 404
        return jsonify({"error": "Post not found"}), 404

# Unlike a reply
@app.route('/posts/<int:post_id>/replies/<int:reply_id>/unlike', methods=['POST'])
def unlike_reply(post_id, reply_id):
    print("Unlike reply endpoint hit")
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session['username']
    with lock, shelve.open(DB_FILE) as db:
        posts = db.get('posts', [])
        for post in posts:
            if post.get('id') == post_id:
                for reply in post.get('replies', []):
                    if reply.get('id') == reply_id:
                        liked_by = reply.get('liked_by', [])
                        if username not in liked_by:
                            return jsonify({"error": "Not liked"}), 400
                        liked_by.remove(username)
                        reply['liked_by'] = liked_by
                        reply['likes'] = max(reply.get('likes', 1) - 1, 0)
                        db['posts'] = posts
                        return jsonify({"message": "Reply unliked successfully", "likes": reply['likes'], "liked": False}), 200
                return jsonify({"error": "Reply not found"}), 404
        return jsonify({"error": "Post not found"}), 404

# Run the app
if __name__ == '__main__':
    print("Starting Flask app...")  # Sanity test output
    app.run(debug=True, threaded=True)