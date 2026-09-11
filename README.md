# Market Flick AI 🚀

Market Flick AI is a comprehensive business analysis platform that helps entrepreneurs and businesses make data-driven decisions through AI-powered market analysis. The platform provides real-time market insights, competitive analysis, and strategic recommendations powered by advanced AI agents.

## Features

### 1. Real-time Market Analysis
- **Business Sector Analysis**: In-depth analysis of 20+ business sectors
- **Location-based Insights**: Global market analysis with local market focus
- **Competitor Landscape**: Detailed competitor profiling and market positioning
- **Market Size Estimation**: TAM, SAM, and SOM calculations with projections

### 2. Strategic Analysis Tools
- **SWOT Analysis**: Comprehensive strengths, weaknesses, opportunities, and threats analysis
- **PESTLE Analysis**: Political, Economic, Social, Technological, Legal, and Environmental factor analysis
- **Porter's Five Forces**: Industry competition and market attractiveness assessment
- **Market Gap Analysis**: AI-powered identification of market opportunities

### 3. Advanced Analytics
- **Market Trends**: Real-time trend analysis and future projections
- **Competitive Intelligence**: Detailed competitor profiling and benchmarking
- **Strategic Recommendations**: AI-generated actionable insights
- **Custom Reports**: Exportable reports in multiple formats (PDF, Excel, CSV)

## Technical Documentation
Link to our [Technical Documentation](./Technical_Documentation.md)

## Video Demo
Link to our [Video Demo](https://www.loom.com/share/145e85e6659d47f2b00a0f2ef0703586)

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.8+
- MongoDB
- OpenAI API key

### Frontend Setup
```bash
# Navigate to client directory
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

### Backend Setup
```bash
# Navigate to server directory
cd server

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize required directories
./init.sh

# Start server
uvicorn main:app --reload
```

### Environment Variables

#### Backend (.env)

⚠️ **IMPORTANT**: Never commit `.env` files with real credentials to version control.

Copy `.env.example` to `.env` and populate with your actual values:

```bash
cp .env.example .env
```

Required environment variables:

```env
# Database Configuration
MONGODB_URI=your_mongodb_connection_string

# API Keys
OPENAI_API_KEY=your_openai_api_key
PPLX_API_KEY=your_perplexity_api_key
TAVILY_API_KEY=your_tavily_api_key
NVIDIA_API_KEY=your_nvidia_api_key

# Authentication
JWT_SECRET_KEY=your_secure_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Service (for authentication)
EMAIL_PROVIDER=smtp  # Options: "smtp" or "ses"
EMAIL_SENDER=no-reply@marketflick.ai
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_email_password
```

### Environment File Template

A `.env.example` file is included in the repository. Use it as a template for your local configuration:

```bash
cp server/.env.example server/.env
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Development Guidelines

### Code Style
- Use TypeScript for frontend development
- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Write unit tests for critical functions

### Component Structure
- Create reusable components
- Follow atomic design principles
- Implement proper error handling
- Use proper type definitions
- Follow Material-UI best practices

### Security Best Practices
- Never commit credentials or secrets to version control
- Use environment variables for sensitive configuration
- Validate and sanitize all user inputs
- Implement CORS restrictions appropriately
- Use HTTPS in production
- Keep dependencies updated

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@marketflickai.com or join our Slack channel.

## Acknowledgments

- OpenAI for GPT-4 API
- Material-UI team for the component library
- FastAPI team for the backend framework
- All contributors who have helped shape Market Flick AI

---

Made with ❤️ by the Team Define Coders

Team Members
1. Ovishek Paul
2. Shawon Majid
3. Nafi Ullah Shafin
4. Sourav Suvra
