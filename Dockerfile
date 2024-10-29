FROM python:3.9

# Create and set the working directory
RUN mkdir /app
WORKDIR /app

# Copy the requirements file first to install dependencies
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get update && apt-get install -y ./google-chrome-stable_current_amd64.deb

# Copy the rest of the app files into the container
COPY app /app

# Run the application
CMD ["python", "main.py"]
