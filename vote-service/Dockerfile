# ==========================================
# STAGE 1: Builder
# Load the base Python image to install dependencies
# ==========================================
FROM python:3.9-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies into the user directory to keep them isolated
# --user flag installs to ~/.local
RUN pip install --user -r requirements.txt

# Copy the rest of the application code
COPY . .

# ==========================================
# STAGE 2: Tester
# Run unit tests to ensure code quality before release
# ==========================================
FROM builder AS tester

# Run the pytest framework on our test file
# If this fails, the Docker build stops here!
RUN python -m pytest test_app.py

# ==========================================
# STAGE 3: Runtime
# Create a fresh, small image for production
# ==========================================
FROM python:3.9-slim AS runtime

# Set the working directory
WORKDIR /app

# Copy the installed dependencies from the builder stage
# This keeps the image size small (no build tools included)
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Update the PATH to include the installed binaries
ENV PATH=/root/.local/bin:$PATH

# Expose port 80 for the application
EXPOSE 80

# Command to run the application using Gunicorn (Production Server)
CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]
