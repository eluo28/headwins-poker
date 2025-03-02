FROM python:3.12-slim

# Install system dependencies required by Kaleido
RUN apt-get update && apt-get install -y \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Create and set working directory
WORKDIR /app

# Set environment to production
ENV ENVIRONMENT=production

# Copy ALL code first (including src directory)
COPY . .

# Then install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Run the bot
CMD ["poetry", "run", "python", "-m", "src.discordbot.run_bot"]
