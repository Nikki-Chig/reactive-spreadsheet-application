# Reactive Spreadsheet Application

A real-time, distributed, collaborative spreadsheet application built with Python, DuckDB, Redis, Tornado, and Svelte. This project demonstrates real-time updates, persistent data storage, and a reactive UI—all deployed locally and containerized with Docker.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Docker Setup](#docker-setup)
- [Usage](#usage)

## Introduction

Reactive Spreadsheet is designed to allow multiple users to collaborate on a single spreadsheet in real-time. The application leverages:

- **Python/Tornado:** For a lightweight WebSocket server to handle real-time connections.
- **DuckDB:** As an embedded SQL database for efficient data storage and querying.
- **Redis Streams:** To manage and broadcast real-time cell updates among connected clients.
- **Svelte:** For building a reactive and user-friendly frontend.
- **AWS:** For deploying and managing the application infrastructure.

## Features

- **Real-Time Collaboration:** Multiple users can view and edit the same spreadsheet concurrently.
- **Live Updates:** Cell updates are broadcast immediately to all connected clients.
- **Data Persistence:** All cell data is stored persistently in DuckDB.
- **Redis Integration:** Updates are published to Redis Streams to decouple and manage real-time messaging.
- **Containerized Deployment:** Both backend and frontend can run in Docker containers orchestrated by Docker Compose.
- **Scalable Architecture:** Built with modular components for future enhancements such as conflict resolution and advanced user management.

## Architecture

Current system design of the application (soon to be deprecated):

![Architecture Diagram](./system_design.jpeg)

New System Design (soon to be implemented):
```mermaid
sequenceDiagram
    autonumber
    Client(Frontend-Svelte)->>Backend(Tornado): Connect to websocket and request spreadsheet data
    Backend(Tornado)->>DuckDB Manager(Flask): Forward request (read_only)
    DuckDB Manager(Flask)->>DuckDB: Fetch spreadsheet data
    DuckDB-->>DuckDB Manager(Flask): Return spreadsheet data
    DuckDB Manager(Flask)-->>Backend(Tornado): Forward Spreadsheet data 
    Backend(Tornado)-->>Client(Frontend-Svelte): Return spreadsheet data

    Client(Frontend-Svelte)->>Backend(Tornado): Update cell data
    Backend(Tornado)->>Redis: Push update to `redis_to_duckdb_stream`
    Redis-->>DuckDB Manager(Flask): Listen and pull updated data
    DuckDB Manager(Flask)->>DuckDB: Write update to database
    DuckDB Manager(Flask)->>Redis: Push update to `redis_to_websocket_stream`
    Redis-->>Backend(Tornado): Notify with updated cell
    Backend(Tornado)-->>Client(Frontend-Svelte): Broadcast update to all connected clients
```

## Setup and Installation

### Backend Setup without Docker

1. **Clone the Repository:** <br>
    git clone https://github.com/Nikki-Chig/LiquidDuck.git <br>
    cd LiquidDuck <br>

2. **Set Up Python Virtual Environment:** <br>
    python -m venv venv_reactive_spreadsheet <br>
    source venv_reactive_spreadsheet/bin/activate   # On Windows: venv_reactive_spreadsheet\Scripts\activate <br>

3. **Install Dependencies:** <br>
    pip install -r requirements.txt <br>

4. **Configuration:** <br>
    Ensure that you have installed Redis and Redis server is accessible at the correct host. When running locally, the application defaults to connecting to Redis at localhost:6379.<br>

5. **Run the backend:** <br>
    To run the backend: <br>
    python src/server.py <br>

### Front Setup without Docker
1. **Navigate to the Frontend Directory:** <br>
    cd frontend <br>

2. **Install Node Dependencies:** <br>
    npm install <br>

3. **Run the Development Server:** <br>
    npm run dev <br>

4. **Run the Development Server:** <br>
    npm run dev <br>
    The frontend will run at http://localhost:5173. <br>

### Entire Project Setup with Docker
The project is containerized using Docker Compose. <br>

1. **Ensure Docker is Installed:** <br>
    Download and install Docker Desktop. <br>

2. **Build and Run Containers:** <br>
    From the project root (reactive_spreadsheet), run: <br>
        docker compose build <br>
        docker compose up <br>

    This starts:<br>
    Backend Container: Accessible at http://localhost:8888. <br>
    Frontend Container: Available at http://localhost:5173. <br>
    Redis Container: Running on port 6379. <br>

3. **Environment Variables:** <br>
The backend container uses the environment variable REDIS_HOST=redis (set in docker-compose.yml) to connect to the Redis container.

## Usage
- **Real-Time Editing:** <br>
    - Open the frontend URL in multiple browser tabs. Edit a cell (double-click to edit) and observe real-time updates across all sessions.

- **Monitoring:** <br>
    - Check the backend logs for important events such as connection status, error messages, and update broadcasts.This can be useful for debugging and performance monitoring.







