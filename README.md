# Pexos

Pexos is a service that enables customers to execute arbitrary Python code on a cloud server.

## Overview

This service allows users to submit Python scripts via an API, which are then executed securely in a sandboxed environment using nsjail. The service returns both the result of the script's `main()` function and any output written to stdout.

## Requirements

- The script must contain a `main()` function with no parameters
- The `main()` function must return a JSON-serializable value
- Basic libraries like `os`, `pandas`, and `numpy` are available

## API Usage

### Execute Endpoint

Send a POST request to the `/execute` endpoint with a JSON body containing a Python script:

```json
{
  "script": "def main():\n    import numpy as np\n    return {'message': 'Hello, World!', 'random': np.random.rand().tolist()}"
}
```

### Response Format

The service will execute the script and return the result:

```json
{
  "result": {
    "message": "Hello, World!",
    "random": 0.123456789
  },
  "stdout": ""
}
```

### Error Handling

If there is an error in the script or during execution, the service will return an error message:

```json
{
  "error": "Error message details"
}
```

## Running Locally

To run the service locally, use Docker:

```bash
docker build -t pexos .
docker run -p 8080:8080 pexos
```

Then access the API at http://localhost:8080/execute

## Security

This service uses nsjail to create a secure sandbox for executing Python code. The following security measures are in place:

- Isolation of the execution environment
- Limited system access
- Resource limits
- Timeout for script execution (30 seconds)
- Memory constraints
- Restricted filesystem access

## Deployment to Google Cloud Run

Google Cloud Run is a fully managed platform that automatically scales your containerized applications. It's ideal for this service as it provides:

- Automatic scaling based on demand (including scaling to zero when not in use)
- Pay-per-use billing model (you only pay for the resources you consume)
- HTTPS endpoint with automatic certificate management
- Easy integration with other Google Cloud services

### Deployment Steps

1. Install the Google Cloud SDK and authenticate:
   ```bash
   gcloud auth login
   ```

2. Create a project or select an existing one:
   ```bash
   gcloud projects create [PROJECT_ID] --name="Python Executor"
   gcloud config set project [PROJECT_ID]
   ```

3. Enable the required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   ```

4. Build and tag your Docker image:
   ```bash
   docker build -t gcr.io/[PROJECT_ID]/pexos .
   ```

5. Configure Docker to use Google Cloud credentials:
   ```bash
   gcloud auth configure-docker
   ```

6. Push the image to Google Container Registry:
   ```bash
   docker push gcr.io/[PROJECT_ID]/pexos
   ```

7. Deploy to Cloud Run:
   ```bash
   gcloud run deploy pexos \
     --image gcr.io/[PROJECT_ID]/pexos \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

8. The command will output your service URL which you can use for API requests.

## Example Test Cases

Here are some test cases you can run against the deployed service.

### 1. Basic Hello World

```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Hello, World!\"}"
  }'
```

Expected response:
```json
{
  "result": {
    "message": "Hello, World!"
  },
  "stdout": ""
}
```

### 2. Working with NumPy

```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\n\ndef main():\n    array = np.array([1, 2, 3, 4, 5])\n    return {\"mean\": float(np.mean(array)), \"std\": float(np.std(array))}"
  }'
```

Expected response:
```json
{
  "result": {
    "mean": 3.0,
    "std": 1.4142135623730951
  },
  "stdout": ""
}
```

### 3. Working with Pandas

```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\n\ndef main():\n    df = pd.DataFrame({\"A\": [1, 2, 3], \"B\": [4, 5, 6]})\n    stats = df.describe().to_dict()\n    # Convert numpy types to native Python for JSON serialization\n    return {k: {kk: float(vv) for kk, vv in v.items()} for k, v in stats.items()}"
  }'
```

### 4. Capturing stdout

```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"This will be captured in stdout\")\n    print(\"Multiple lines\")\n    print(\"of output\")\n    return {\"status\": \"completed\"}"
  }'
```

Expected response:
```json
{
  "result": {
    "status": "completed"
  },
  "stdout": "This will be captured in stdout\nMultiple lines\nof output"
}
```

### 5. Testing Error Cases

Missing main function:
```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "print(\"This script has no main function\")"
  }'
```

Syntax error:
```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"broken\": True"
  }'
```

## Live Service

A live implementation of this service is available at:

```bash
https://pexos-331287429127.us-central1.run.app
```

Example:
```bash
curl -X POST https://pexos-331287429127.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Hello, World!\"}"
  }'
```

## Built With

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [nsjail](https://nsjail.dev/) - Sandbox environment
- [Docker](https://www.docker.com/) - Containerization
- [Google Cloud Run](https://cloud.google.com/run) - Serverless container platform
