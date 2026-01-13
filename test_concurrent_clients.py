import requests
import threading

def register_user(base_url, username, password):
    response = requests.post(f"{base_url}/auth/register", json={
        "username": username,
        "password": password
    })
    print(f"Register {username}: {response.status_code}, {response.json()}")

def create_post(base_url, username, content):
    response = requests.post(f"{base_url}/posts", json={
        "username": username,
        "content": content
    })
    print(f"Create Post by {username}: {response.status_code}, {response.json()}")

def simulate_client(base_url, username, password, content):
    # Register the user
    register_user(base_url, username, password)

    # Create a post
    create_post(base_url, username, content)

def main():
    base_url = "http://127.0.0.1:5000"

    # Define clients
    clients = [
        {"username": "user1", "password": "password1", "content": "Hello from user1!"},
        {"username": "user2", "password": "password2", "content": "Hello from user2!"},
        {"username": "user3", "password": "password3", "content": "Hello from user3!"},
    ]

    threads = []

    # Start threads for each client
    for client in clients:
        thread = threading.Thread(
            target=simulate_client,
            args=(base_url, client['username'], client['password'], client['content'])
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()