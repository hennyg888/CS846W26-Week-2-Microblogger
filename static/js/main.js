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
        // Post like/unlike
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

        // Reply like/unlike
        if (e.target && e.target.classList.contains('reply-like-btn')) {
            const postId = e.target.getAttribute('data-post-id');
            const replyId = e.target.getAttribute('data-reply-id');
            const btn = e.target;
            const liked = btn.getAttribute('data-liked') === 'true';
            const endpoint = liked ? `/posts/${postId}/replies/${replyId}/unlike` : `/posts/${postId}/replies/${replyId}/like`;
            try {
                const res = await fetch(endpoint, { method: 'POST', credentials: 'same-origin' });
                const countSpan = document.querySelector(`.reply-likes-count[data-post-id="${postId}"][data-reply-id="${replyId}"]`);
                if (res.ok) {
                    const data = await res.json();
                    if (countSpan) countSpan.textContent = data.likes;
                    if (btn) {
                        btn.setAttribute('data-liked', data.liked ? 'true' : 'false');
                        btn.textContent = data.liked ? 'Unlike' : 'Like';
                    }
                } else if (res.status === 401) {
                    alert('Please login to like replies.');
                    window.location.href = '/login';
                } else if (res.status === 400) {
                    const err = await res.json();
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
                        alert(err.error || 'Error liking/unliking reply');
                    }
                } else {
                    const err = await res.json();
                    alert(err.error || 'Error liking/unliking reply');
                }
            } catch (err) {
                console.error('Reply like/unlike request failed', err);
            }
        }
    });

    // Reply form submission (event delegation)
    document.addEventListener('submit', async (e) => {
        if (e.target && e.target.classList.contains('reply-form')) {
            e.preventDefault();
            const form = e.target;
            const postId = form.getAttribute('data-post-id');
            const input = form.querySelector('input[name="content"]');
            const content = input.value;
            try {
                const res = await fetch(`/posts/${postId}/reply`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({ content })
                });
                if (res.ok) {
                    const data = await res.json();
                    const reply = data.reply;
                    // Append reply to the replies container for the post
                    const postEl = document.querySelector(`.post[data-post-id="${postId}"]`);
                    const repliesContainer = postEl.querySelector('.replies');
                    const replyHtml = document.createElement('div');
                    replyHtml.className = 'reply';
                    replyHtml.setAttribute('data-reply-id', reply.id);
                    replyHtml.innerHTML = `
                        <p>${reply.content}</p>
                        <p>Posted by: <a href="/users/${reply.username}">${reply.username}</a></p>
                        <p>Likes: <span class="reply-likes-count" data-post-id="${postId}" data-reply-id="${reply.id}">${reply.likes || 0}</span>
                            <button class="reply-like-btn" data-post-id="${postId}" data-reply-id="${reply.id}" data-liked="false">Like</button>
                        </p>
                    `;
                    if (repliesContainer) {
                        repliesContainer.appendChild(replyHtml);
                    }
                    input.value = '';
                } else if (res.status === 401) {
                    alert('Please login to reply.');
                    window.location.href = '/login';
                } else {
                    const err = await res.json();
                    alert(err.error || 'Error adding reply');
                }
            } catch (err) {
                console.error('Reply request failed', err);
            }
        }
    });
});