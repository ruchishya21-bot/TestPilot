document.addEventListener("DOMContentLoaded", () => {

    // Registration
    const registerForm = document.getElementById("registerForm");

    if (registerForm) {

        registerForm.addEventListener("submit", async (event) => {

            event.preventDefault();

            const message = document.getElementById("registerMessage");

            const payload = {
                username: document.getElementById("username").value.trim(),
                email: document.getElementById("email").value.trim(),
                password: document.getElementById("password").value
            };

            message.textContent = "Creating your account...";
            message.className = "message";

            try {

                const response = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || "Registration failed");
                }

                message.textContent = "Account created successfully! Redirecting...";
                message.className = "message success";

                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);

            } catch (error) {

                message.textContent = error.message;
                message.className = "message error";

            }

        });

    }


    // Login
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {

        loginForm.addEventListener("submit", async (event) => {

            event.preventDefault();

            const message = document.getElementById("loginMessage");

            const payload = {
                email: document.getElementById("email").value.trim(),
                password: document.getElementById("password").value
            };

            message.textContent = "Signing you in...";
            message.className = "message";

            try {

                const response = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || "Login failed");
                }

                message.textContent = "Login successful! Redirecting...";
                message.className = "message success";

                setTimeout(() => {
                    window.location.href = "/dashboard";
                }, 700);

            } catch (error) {

                message.textContent = error.message;
                message.className = "message error";

            }

        });

    }


    // Logout
    const logoutButton = document.getElementById("logoutButton");

    if (logoutButton) {

        logoutButton.addEventListener("click", async () => {

            try {

                const response = await fetch("/api/auth/logout", {
                    method: "POST"
                });

                if (!response.ok) {
                    throw new Error("Logout failed");
                }

                window.location.href = "/login";

            } catch (error) {

                alert(error.message);

            }

        });

    }

});