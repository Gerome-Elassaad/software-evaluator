# Installation and Quickstart Guide

This guide will help you set up and run the Product Evaluator tool for local development.

## Prerequisites

- Python 3.9 or newer
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

1. **Clone the repository (or download the code)**:
   ```
   git clone https://github.com/Gerome-Elassaad/product-evaluator.git
   cd product-evaluator
   ```

2. **Create a virtual environment**:
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   - Copy `.env.local` to `.env`:
     ```
     cp .env.local .env
     ```
   - Edit `.env` to configure your settings. At minimum, update:
     - `JWT_SECRET_KEY` with a secure random string
     - `GOOGLE_API_KEY` with your Google API key
     - Or `OPENAI_API_KEY` with your OpenAI API key

## Database Setup

By default, the application uses SQLite for local development, which requires no additional setup.

To create the initial database and seed it with an admin user:

1. **Run the application once to create the database**:
   ```
   python -m product_evaluator.main
   ```

2. **Create an admin user**:
   ```
   python scripts/create_admin.py --username admin --email admin@example.com --password your-secure-password
   ```

## Running the Application

1. **Start the application**:
   ```
   uvicorn product_evaluator.main:app --reload
   ```

2. **Access the application**:
   - API server will be running at: http://localhost:8000
   - API documentation available at: http://localhost:8000/docs

## Docker Setup (Alternative)

If you prefer using Docker:

1. **Install Docker and Docker Compose** (if not already installed)

2. **Configure environment variables**:
   - Edit `.env` with appropriate settings for Docker

3. **Build and start the containers**:
   ```
   docker-compose up -d
   ```

4. **Create an admin user inside the container**:
   ```
   docker-compose exec app python scripts/create_admin.py --username admin --email admin@example.com --password your-secure-password --db-url postgresql://postgres:postgres@db:5432/product_evaluator
   ```

5. **Access the application**:
   - API server will be running at: http://localhost:8000
   - API documentation available at: http://localhost:8000/docs

## Using the Application

1. **Login/Register**:
   - Use the `/api/auth/register` endpoint to create a new user
   - Use the `/api/auth/token` endpoint to login and get an access token

2. **Add Products**:
   - Use the `/api/products` endpoint to add products for evaluation
   - Provide a product URL to automatically extract information

3. **Create Evaluations**:
   - Use the `/api/evaluations` endpoint to create evaluations
   - Enable AI assistance to get an initial assessment

4. **View and Update Evaluations**:
   - Use the GET endpoints to view your evaluations
   - Use the PUT endpoints to update evaluations

## API Keys

The application requires API keys for AI features:

1. **Google API Key**:
   - Create an API key in the [Google AI Studio](https://makersuite.google.com/)
   - Enable the Gemini API

2. **OpenAI API Key** (Alternative):
   - Create an API key at [OpenAI](https://platform.openai.com/)