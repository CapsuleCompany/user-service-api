FROM ubuntu:22.04

# Set environment variables to make tzdata non-interactive
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install system dependencies and Python 3.12
RUN apt-get update && apt-get install -y \
    software-properties-common wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 python3.12-dev libpq-dev build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pip manually using get-pip.py
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.12 get-pip.py && rm get-pip.py

# Set up aliases for convenience
RUN echo "alias python=python3.12" >> ~/.bashrc && \
    echo "alias makemigrations='python manage.py makemigrations'" >> ~/.bashrc && \
    echo "alias migrate='python manage.py migrate'" >> ~/.bashrc

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN python3.12 -m pip install --upgrade pip && python3.12 -m pip install -r requirements.txt

# Copy application code
COPY . /app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python3.12", "manage.py", "runserver", "0.0.0.0:8000"]

# Set the default shell to bash to ensure aliases work
SHELL ["/bin/bash", "-c"]
