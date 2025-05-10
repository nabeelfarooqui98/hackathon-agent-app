# AI Question Answering Web App

A Flask-based web application that uses the Groq API to answer questions using AI.

## Prerequisites

- Docker and Docker Compose
- Pipenv (for local development)
- Groq API key (get it from [Groq's website](https://console.groq.com/))

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Running the Application

### Using Docker (Recommended)

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

2. Access the application at `http://localhost:5000`

### Running Locally with Pipenv

1. Install dependencies using Pipenv:
   ```bash
   pipenv install
   ```

2. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the application at `http://localhost:5000`

## Features

- Simple and clean user interface
- Real-time AI responses using Groq's API
- Loading indicators for better UX
- Error handling and display
- Docker support for easy deployment

## API Endpoints

- `GET /`: Serves the main page
- `POST /ask`: Accepts questions and returns AI responses
  - Request body: `{"question": "your question here"}`
  - Response: `{"response": "AI's answer"}`

## Technologies Used

- Flask
- Groq API
- Bootstrap 5
- Docker
- Gunicorn 