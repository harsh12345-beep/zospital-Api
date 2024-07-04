# Use an official Python runtime as a parent image
FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/bin \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/bin/chromedriver

# Set ChromeDriver path as an environment variable
ENV PATH="/usr/bin/chromedriver:${PATH}"

# Set up the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

