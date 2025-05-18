# Product Evaluator

<div align="center">
  <img src="https://via.placeholder.com/200x200?text=Product+Evaluator" alt="Product Evaluator Logo" width="200">
  <h3>AI-powered tool for evaluating software products and services</h3>
</div>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#ai-integration">AI Integration</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

Product Evaluator is a comprehensive tool designed to help software developers and founders make informed decisions when evaluating tools, services, and frameworks. It leverages AI to streamline the evaluation process and provide deeper insights.

## Features

### User Management
- 🔐 Secure user authentication and authorization
- 👤 User profiles with activity tracking
- 👑 Admin capabilities for user management

### Product Management
- 📊 Add and organize products by categories and vendors
- 🔍 Advanced search and filtering capabilities
- 🌐 Extract product information from websites automatically

### Evaluation System
- ⭐ Evaluate products using predefined or custom criteria
- 📝 Add detailed notes and justifications for each criterion
- 📈 Calculate weighted scores for comprehensive assessment

### AI-Powered Features
- 🤖 AI-assisted information gathering from product URLs
- 🧠 AI-powered initial assessment against criteria
- 📄 AI-generated evaluation summaries and recommendations

### Interface
- 💻 Responsive web interface for desktop and mobile
- 📱 Intuitive user experience with modern design
- 🔄 Real-time updates and notifications

## Installation

### Prerequisites
- Python 3.9+
- pip
- Optional: Docker and Docker Compose

### Standard Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/product-evaluator.git
cd product-evaluator

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.local .env
# Edit .env with your API keys and settings

# Initialize database and create admin user
python scripts/setup.py --username admin --password your-secure-password --demo-data

# Run the application
uvicorn product_evaluator.main:app --reload
```

### Docker Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/product-evaluator.git
cd product-evaluator

# Configure environment
cp .env.local .env
# Edit .env with your API keys and settings

# Build and start containers
docker-compose up -d

# Initialize database and create admin user
docker-compose exec app python scripts/setup.py --username admin --password your-secure-password --demo-data
```

## Usage

### Web Interface
1. Access the web application at http://localhost:8000
2. Login with your credentials or the admin account
3. Start adding products and creating evaluations

### Creating Evaluations
1. Navigate to the Products section and add a product
2. Use the "Extract from URL" feature to automatically gather information
3. Go to Evaluations and create a new evaluation for the product
4. Enable AI assistance for initial assessment
5. Review and adjust scores as needed
6. Generate AI summary of your evaluation
7. Publish or keep as draft

### API Usage
The application provides a comprehensive REST API for integration with other tools:

```python
import requests

# Get access token
response = requests.post(
    "http://localhost:8000/api/auth/token",
    data={"username": "your_username", "password": "your_password"}
)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# Create a product
product_data = {
    "name": "Example Product",
    "website_url": "https://example.com",
    "extract_content": True
}
response = requests.post(
    "http://localhost:8000/api/products",
    json=product_data,
    headers=headers
)
product_id = response.json()["id"]

# Create an evaluation
evaluation_data = {
    "title": "Example Evaluation",
    "product_id": product_id,
    "use_ai_analysis": True
}
requests.post(
    "http://localhost:8000/api/evaluations",
    json=evaluation_data,
    headers=headers
)
```

## AI Integration

Product Evaluator leverages AI for several key features:

### Web Content Extraction
- Automatically extracts relevant information from product websites
- Cleans and organizes the extracted content for analysis
- Identifies key product details like features, pricing, and technical specifications

### Criteria Analysis
- Analyzes product information against predefined evaluation criteria
- Provides suggested scores based on the extracted content
- Generates detailed assessments with strengths and weaknesses

### Summary Generation
- Creates comprehensive evaluation summaries
- Highlights key findings across all criteria
- Provides actionable recommendations based on the evaluation

### AI Configuration
The application can be configured to use different AI providers:

- **Google AI**: Set `GOOGLE_API_KEY` in your .env file
- **OpenAI**: Set `OPENAI_API_KEY` in your .env file

## Architecture

Product Evaluator follows a clean, modular architecture:

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
├── ui/                 # User interface
│   └── templates/      # HTML templates
├── tests/              # Test suite
└── utils/              # Utility functions
```

### Technologies Used
- **Backend**: Python with FastAPI
- **Database**: SQLAlchemy ORM (SQLite for development, PostgreSQL for production)
- **AI/NLP**: Google Generative AI, OpenAI (optional)
- **Frontend**: HTML, CSS (TailwindCSS), JavaScript
- **Authentication**: JWT-based token authentication
- **Containerization**: Docker and Docker Compose

## API Reference

### Authentication Endpoints
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/token` - Get JWT access token

### Product Endpoints
- `GET /api/products` - List all products
- `POST /api/products` - Create a new product
- `GET /api/products/{id}` - Get product details
- `PUT /api/products/{id}` - Update a product
- `DELETE /api/products/{id}` - Delete a product
- `POST /api/products/extract-content` - Extract content from URL

### Evaluation Endpoints
- `GET /api/evaluations` - List all evaluations
- `POST /api/evaluations` - Create a new evaluation
- `GET /api/evaluations/{id}` - Get evaluation details
- `PUT /api/evaluations/{id}` - Update an evaluation
- `DELETE /api/evaluations/{id}` - Delete an evaluation
- `POST /api/evaluations/{id}/publish` - Publish an evaluation
- `POST /api/evaluations/{id}/unpublish` - Unpublish an evaluation

### AI Endpoints
- `POST /api/ai/analyze` - Analyze product against criteria
- `POST /api/ai/summarize` - Generate evaluation summary

### Criteria Endpoints
- `GET /api/criteria` - List all criteria
- `GET /api/criteria/{id}` - Get criterion details
- `GET /api/criteria/categories` - List criterion categories

For complete API documentation, visit http://localhost:8000/docs when the application is running.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linters
flake8
black .
isort .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Google Generative AI](https://ai.google.dev/) - AI capabilities
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
- [Font Awesome](https://fontawesome.com/) - Icons