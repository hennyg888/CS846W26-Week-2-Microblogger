document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
                credentials: 'same-origin'
            });

            if (response.redirected) {
                // Redirect to the new location if the server sends a redirect
                window.location.href = response.url;
            } else {
                const result = await response.json();
                alert(result.error || 'Login failed');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
                credentials: 'same-origin'
            });

            if (response.redirected) {
                // Redirect to the new location if the server sends a redirect
                window.location.href = response.url;
            } else {
                const result = await response.json();
                alert(result.error || 'Registration failed');
            }
        });
    }

    // Like / Unlike button handler (event delegation)
    document.addEventListener('click', async (e) => {
        if (e.target && e.target.classList.contains('like-btn')) {
            const postId = e.target.getAttribute('data-post-id');
            const btn = e.target;
            const liked = btn.getAttribute('data-liked') === 'true';
            const endpoint = liked ? `/posts/${postId}/unlike` : `/posts/${postId}/like`;
            try {
                const res = await fetch(endpoint, { method: 'POST', credentials: 'same-origin' });
                const countSpan = document.querySelector(`.likes-count[data-post-id="${postId}"]`);
                if (res.ok) {
                    const data = await res.json();
                    if (countSpan) countSpan.textContent = data.likes;
                    if (btn) {
                        btn.setAttribute('data-liked', data.liked ? 'true' : 'false');
                        btn.textContent = data.liked ? 'Unlike' : 'Like';
                    }
                } else if (res.status === 401) {
                    alert('Please login to like posts.');
                    window.location.href = '/login';
                } else if (res.status === 400) {
                    const err = await res.json();
                    // If the user already liked/unliked, reflect the correct state
                    if (err.error === 'Already liked') {
                        if (btn) {
                            btn.setAttribute('data-liked', 'true');
                            btn.textContent = 'Unlike';
                        }
                    } else if (err.error === 'Not liked') {
                        if (btn) {
                            btn.setAttribute('data-liked', 'false');
                            btn.textContent = 'Like';
                        }
                    } else {
                        alert(err.error || 'Error liking/unliking post');
                    }
                } else {
                    const err = await res.json();
                    alert(err.error || 'Error liking/unliking post');
                }
            } catch (err) {
                console.error('Like/Unlike request failed', err);
            }
        }
    });
});