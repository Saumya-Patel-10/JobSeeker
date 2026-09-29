FROM python:3.12-slim

# Install system deps for Playwright + PDF tools
RUN apt-get update && apt-get install -y \
    wget curl gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libpango-1.0-0 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

COPY . .
