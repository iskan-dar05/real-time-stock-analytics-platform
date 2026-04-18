FROM python:3.11-slim

WORKDIR /app


# Install Java (REQUIRED for Spark)
RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    && apt-get clean

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# 1. Copy ONLY requirements first
COPY requirements.txt .

# 2. Install dependencies (this layer gets cached)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your code
COPY . .

ENV PYTHONPATH=/app

CMD ["python", "training/train_model.py"]