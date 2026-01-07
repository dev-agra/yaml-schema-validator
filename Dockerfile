FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Install package
RUN pip install -e .

# Default command
ENTRYPOINT ["yaml-validate"]
CMD ["--help"]

# Usage:
#   docker build -t yaml-validator .
#   docker run -v $(pwd):/data yaml-validator /data/config.yaml
#   docker run -v $(pwd):/data yaml-validator /data/config.yaml --profile statement_only