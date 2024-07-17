# Use the official Python image from the Docker Hub
FROM python:3.10

# Install Poetry
RUN pip install poetry

# Set the working directory in the container
WORKDIR /workspace

# Copy the project files into the container
COPY . .
RUN ls -la /workspace/*

# Install dependencies using Poetry
RUN poetry install

# Set the entrypoint for the container
CMD ["poetry", "run", "python", "main.py"]

# Expose port if necessary
# EXPOSE 8000
