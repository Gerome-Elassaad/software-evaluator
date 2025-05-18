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
   - Edit `.env` to configure your settings. You'll need to update:
     - `JWT_SECRET_KEY` with a secure random string
     - `GOOGLE_API_KEY` or `OPENAI_API_KEY` for AI features

## Running the Application

1. **Initialize the database and create a demo admin user**:
   ```
   python scripts/setup.py --username admin --password your-secure-password --demo-data
   ```

2. **Start the application**:
   ```
   uvicorn product_evaluator.main:app --reload
   ```

3. **Access the application**:
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs

4. **Login with demo credentials**:
   - Username: `admin`
   - Password: `your-secure-password` (the one you set in step 1)

## Docker Setup (Alternative)

If you prefer using Docker:

1. **Install Docker and Docker Compose** (if not already installed)

2. **Configure environment variables**:
   - Edit `.env` with appropriate settings for Docker

3. **Build and start the containers**:
   ```
   docker-compose up -d
   ```

4. **Initialize the database and create a demo admin user**:
   ```
   docker-compose exec app python scripts/setup.py --username admin --password your-secure-password --demo-data
   ```

5. **Access the application**:
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs

## Application Features

### User Management
- User registration and authentication
- User profiles with activity tracking
- Admin capabilities for user management

### Product Management
- Add products manually or extract data from websites
- Organize products by categories and vendors
- View and filter products

### Evaluation System
- Evaluate products using predefined criteria
- Score products on a scale of 1-10
- Add notes and comments to evaluations

### AI-Powered Features
- AI-assisted information gathering from product URLs
- AI-powered initial assessment against criteria
- AI-generated evaluation summaries

## API Usage

The application provides a comprehensive REST API:

1. **Authentication**:
   - `POST /api/auth/register` - Register a new user
   - `POST /api/auth/token` - Get access token

2. **Products**:
   - `GET /api/products` - List all products
   - `POST /api/products` - Create a new product
   - `GET /api/products/{id}` - Get product details
   - `PUT /api/products/{id}` - Update a product
   - `DELETE /api/products/{id}` - Delete a product

3. **Evaluations**:
   - `GET /api/evaluations` - List all evaluations
   - `POST /api/evaluations` - Create a new evaluation
   - `GET /api/evaluations/{id}` - Get evaluation details
   - `PUT /api/evaluations/{id}` - Update an evaluation
   - `DELETE /api/evaluations/{id}` - Delete an evaluation

4. **AI Features**:
   - `POST /api/ai/analyze` - Analyze product against criteria
   - `POST /api/ai/summarize` - Generate evaluation summary

For complete API documentation, visit http://localhost:8000/docs when the application is running.

## Project Structure

```
product_evaluator/
├── api/                # API endpoints
│   ├── middleware/     # Request middleware
│   └── routes/         # API route definitions
├── data/               # Data storage and knowledge base
│   ├── embeddings/     # Vector embeddings storage
│   └── knowledge_base/ # Structured knowledge for AI
├── models/             # Database models
│   ├── evaluation/     # Evaluation related models
│   ├── product/        # Product related models
│   └── user/           # User related models
├── services/           # Business logic services
│   ├── ai/             # AI-related services
│   ├── auth/           # Authentication services
│   └── extraction/     # Web content extraction
├── static/             # Static files (CSS, JS)
│   ├── css/            # CSS files
│   └── js/             # JavaScript files
├── ui/                 # User interface
│   └── templates/      # HTML templates
├── tests/              # Test suite
│   ├── integration/    # Integration tests
│   └── unit/           # Unit tests
└── utils/              # Utility functions
```

## AI Integration

The application integrates with AI services for various features:

1. **Content Extraction**:
   - Uses a combination of libraries to extract relevant information from websites
   - Cleans and processes the text for AI analysis

2. **Product Analysis**:
   - Uses AI to analyze products against predefined criteria
   - Provides suggested scores and assessments

3. **Summary Generation**:
   - Uses AI to generate comprehensive evaluation summaries
   - Includes strengths, weaknesses, and recommendations

## Troubleshooting

### Application Won't Start
- Check that `.env` file is configured correctly
- Ensure all dependencies are installed
- Verify database file permissions

### AI Features Not Working
- Verify API keys are set correctly in `.env`
- Check logs for API rate limit errors
- Ensure extracted content is sufficient for analysis

### Database Issues
- Delete the database file and run the setup script again
- Check for migration errors in the logs

## Next Steps

After setting up the basic application, you might want to:

1. **Customize Evaluation Criteria**:
   - Edit `data/knowledge_base/evaluation_criteria.json`
   - Restart the application to apply changes

2. **Enhance AI Prompts**:
   - Modify prompt templates in the service files for better results
   - Experiment with different temperature settings

3. **Add Custom Styling**:
   - Edit `static/css/custom.css` to match your brand
   - Update templates with specific design elements

4. **Deploy to Production**:
   - Set appropriate security settings in `.env`
   - Configure a proper database like PostgreSQL
   - Set up HTTPS using a reverse proxy