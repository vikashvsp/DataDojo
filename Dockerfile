# Use the official Apify Python 3.11 image
FROM apify/actor-python:3.11

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the source code
COPY src ./src

# Run the actor
CMD ["python3", "-m", "src.main"]
