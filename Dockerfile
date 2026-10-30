# CSC418 DevOps Lab - Selenium News API (FA23-BDS-064, ProPakistani)
FROM --platform=linux/amd64 python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    REGISTRATION=FA23-BDS-064

# Google Chrome + matching ChromeDriver
RUN apt-get update \
 && apt-get install -y --no-install-recommends wget curl unzip ca-certificates gnupg fonts-liberation \
 && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y --no-install-recommends /tmp/chrome.deb \
 && CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+') \
 && ( wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
      || ( MAJOR=${CHROME_VERSION%%.*} \
           && DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${MAJOR}") \
           && wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" ) ) \
 && unzip -q /tmp/chromedriver.zip -d /tmp \
 && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
 && chmod +x /usr/local/bin/chromedriver \
 && rm -rf /tmp/* /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

EXPOSE 7000
CMD ["gunicorn", "--bind", "0.0.0.0:7000", "--workers", "1", "--timeout", "180", "app:app"]
