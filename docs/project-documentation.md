# Project Documentation: Dockerized Polling App

## 1. Current Architecture

This project is a multi-service web application orchestrated with Docker Compose. It consists of three main services:

*   **Frontend**: A static web application built with HTML, CSS, and JavaScript, served by an **Nginx** container. This service is responsible for rendering the user interface and sending requests to the backend.
*   **Backend**: A RESTful API built with **Python (Flask)**. It handles business logic, processes votes, and communicates with the database.
*   **Database**: A **PostgreSQL** database that stores poll questions and vote counts. Data is persisted using a named Docker volume.

### 1.1. Service Communication

The services are connected via a user-defined bridge network created by Docker Compose, allowing them to communicate with each other using their service names as hostnames.

*   The **frontend** communicates with the **backend** over HTTP.
*   The **backend** connects to the **database** using the PostgreSQL protocol.

## 2. Increasing Technical Complexity

To demonstrate a deeper understanding of Docker and related concepts, the following enhancements can be implemented.

### 2.1. Introduce a Caching Layer with Redis

**Concept**: Add a Redis cache to reduce database load and improve response times.

**Implementation**:

1.  **Add a Redis Service**: Add a `redis` service to the `docker-compose.yml` file using the official `redis:alpine` image.
2.  **Update Backend Logic**:
    *   Modify the backend application to first check the Redis cache for results.
    *   If the results are not in the cache, query the database, store the results in Redis, and then return them.
    *   When a new vote is cast, update the database and either invalidate the cache or update the cached results.
3.  **Update `requirements.txt`**: Add the `redis` Python library.

### 2.2. Add a Real-Time Results Dashboard with WebSockets

**Concept**: Create a separate, real-time dashboard that updates vote counts instantly without needing to refresh the page.

**Implementation**:

1.  **Add a WebSocket Service**: Create a new service (e.g., a Node.js server with Socket.IO) that communicates with the backend and frontend.
2.  **Update Backend**: When a vote is cast, the backend should publish an event to a message queue (like Redis Pub/Sub).
3.  **WebSocket Server**: The WebSocket server subscribes to the message queue and pushes updates to connected clients (the dashboard).
4.  **Create a Dashboard**: A new HTML page that establishes a WebSocket connection and updates the UI in real-time.

### 2.3. Implement a Load Balancer and Scale the Backend

**Concept**: Demonstrate horizontal scaling by running multiple instances of the backend service and distributing traffic between them.

**Implementation**:

1.  **Use Nginx as a Reverse Proxy**: Instead of having the frontend communicate directly with the backend, route traffic through an Nginx reverse proxy. This Nginx instance will act as a load balancer.
2.  **Scale the Backend**: In the `docker-compose.yml` file, use the `deploy` key with a `replicas` value greater than 1 for the backend service.
    ```yaml
    backend:
      build: ./backend
      deploy:
        replicas: 3
    ```
3.  **Configure Nginx**: Update the Nginx configuration to load balance requests across the backend replicas.

### 2.4. Enhance Observability with Logging and Monitoring

**Concept**: Implement a centralized logging and monitoring solution to provide insights into the application's performance and health.

**Implementation**:

1.  **Centralized Logging**: Use the **ELK stack** (Elasticsearch, Logstash, Kibana) or a similar solution like **Grafana Loki**.
    *   Configure the application containers to send their logs to a logging driver.
    *   Add the necessary services to your `docker-compose.yml` file.
2.  **Monitoring**: Use **Prometheus** and **Grafana** to monitor container metrics.
    *   Instrument the backend application to expose metrics (e.g., using a Flask-Prometheus library).
    *   Configure Prometheus to scrape these metrics and Grafana to visualize them in a dashboard.
