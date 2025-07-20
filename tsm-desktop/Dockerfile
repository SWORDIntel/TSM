# Use a minimal Debian image
FROM debian:slim

# Create a non-root user
RUN useradd -m tsmuser

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /home/tsmuser

# Copy the application files
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Set the user
USER tsmuser

# Run the application
CMD ["python3", "main.py"]
