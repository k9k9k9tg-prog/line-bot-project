# LINE Chatbot Setup Guide (Docker)

This guide provides instructions to set up and run the LINE Chatbot application using Docker and Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed on your machine:
*   **Git**: For cloning the repository.
*   **Docker**: [Install Docker](https://docs.docker.com/get-docker/) (includes Docker Compose).

## 1. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone YOUR_REPOSITORY_URL # Replace with your actual repository URL
cd line-bot-project # Or the name of your cloned directory
```

## 2. Environment Variables Configuration

The application requires several environment variables for LINE API access and admin authentication. An `.env` file has been created for you at `./app/.env`.

**Important:** You must update the placeholder values in `./app/.env` with your actual LINE Channel Access Token, Channel Secret, and Operator ID.

```ini
# ./app/.env
LINE_CHANNEL_ACCESS_TOKEN="YOUR_LINE_CHANNEL_ACCESS_TOKEN" # Replace with your LINE Channel Access Token
LINE_CHANNEL_SECRET="YOUR_LINE_CHANNEL_SECRET"         # Replace with your LINE Channel Secret
OPERATOR_ID="YOUR_OPERATOR_ID"                         # Replace with the LINE User ID of the operator

# Admin credentials (optional, defaults to admin/password)
ADMIN_USER="admin"
ADMIN_PASS="password"
```

## 3. Build and Run the Application

Navigate to the root directory of the cloned project (where `docker-compose.yml` is located) and run the following command to build the Docker image and start the containers:

```bash
docker-compose up -d --build
```
*   `-d`: Runs the containers in detached mode (in the background).
*   `--build`: Rebuilds the Docker images. Use this if you've made changes to the `Dockerfile` or any of the application files.

## 4. Accessing the Web Interfaces

Once the containers are running, the application will be accessible via your web browser:

*   **Main Application/LINE Webhook Callback**: `http://localhost:8000`
*   **Admin Panel**: `http://localhost:8000/admin`
*   **Operator View**: `http://localhost:8000/operator`
*   **Scenario Editor**: `http://localhost:8000/editor`

Use the `ADMIN_USER` and `ADMIN_PASS` credentials (default: `admin`/`password`) to log into the admin-protected pages.

## 5. LINE Webhook Setup (for receiving messages)

To enable your LINE Bot to receive messages, you need to configure the Webhook URL in your LINE Developers console.

If you are running the bot on a local machine and want to expose it to the internet, you can use a tunneling service like `ngrok`:

```bash
ngrok http 8000
```

`ngrok` will provide a public URL (e.g., `https://xxxx.ngrok.io`). Copy this URL and set it as the **Webhook URL** in your LINE Developers console, appending `/callback` to it (e.g., `https://xxxx.ngrok.io/callback`). Ensure **"Use webhook"** is enabled.

**For corporate PC environments without ngrok:**
If you need to expose your bot within a company LAN without external tunneling, you might need to configure port forwarding or use an internal proxy, depending on your company's network policies. Consult your IT department for assistance.

## 6. Browser Notifications

The application supports browser notifications. For these to work, you may need to explicitly allow notifications in your browser settings (e.g., Chrome, Edge) when prompted by the application.

## 7. Demo Operations

1.  Access the **Admin Panel** (`http://localhost:8000/admin`).
2.  Log in with your admin credentials.
3.  From the admin panel, you can manage users, view message logs, and switch active scenarios.
4.  Navigate to the **Scenario Editor** (`http://localhost:8000/editor`) to create or modify conversation flows.
5.  After making changes, remember to update or switch the active scenario in the Admin Panel if necessary.

## Troubleshooting "This page can't be reached"

If you are unable to access the application via `http://localhost:8000`, consider the following:

1.  **Check Docker Container Status**: Ensure the `line-bot` container is running:
    ```bash
    docker ps
    ```
    If it's not running, check `docker-compose logs line-bot` for errors.

2.  **Firewall**: Your host machine's firewall might be blocking access to port 8000.
    *   **Action**: Configure your firewall to allow incoming connections on port 8000.

3.  **Port Conflict**: Another application on your host might be using port 8000.
    *   **Action**: Check for processes using port 8000 (e.g., `sudo lsof -i :8000` on Linux/macOS, `netstat -ano | findstr :8000` on Windows). If a conflict exists, stop the other process or modify the port mapping in `docker-compose.yml` (e.g., change `ports: - "8000:8000"` to `ports: - "8001:8000"` and access via `http://localhost:8001`).