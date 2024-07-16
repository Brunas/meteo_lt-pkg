# Use the official Python image from the Docker Hub
FROM python:3.10

# Install Poetry
RUN pip install poetry

# Set the working directory in the container
WORKDIR /workspace

# Copy the project files into the container
COPY . .
COPY pyproject.toml /workspace/
COPY poetry.lock /workspace/
RUN ls -la /workspace/*

# Install dependencies using Poetry
RUN poetry install

# Install additional dependencies if needed
# RUN poetry add <additional-dependencies>

# Set the entrypoint for the container
#CMD ["poetry", "run", "python", "main.py"]

# Expose port if necessary
# EXPOSE 8000
