# Market Flick AI 🚀

Market Flick AI is an AI-powered business analysis platform that helps entrepreneurs and businesses make data-driven decisions through market research, competitor intelligence, and strategic recommendations.

## Features

### Market analysis
- Business sector analysis across 20+ sectors
- Location-based insights with local market focus
- Competitor landscape and market positioning
- TAM, SAM, and SOM estimates with projections

### Strategic analysis
- SWOT analysis
- PESTLE analysis
- Porter's Five Forces
- Market gap analysis and opportunity discovery

### Advanced analytics
- Market trends and projections
- Competitor profiling and benchmarking
- AI-generated strategic recommendations
- Exportable reports in multiple formats

## Technical documentation
See [Technical Documentation](./Technical_Documentation.md).

## Video demo
[Watch the demo](https://www.loom.com/share/145e85e6659d47f2b00a0f2ef0703586).

## Getting started

### Prerequisites
- Node.js 18+
- Python 3.8+
- MongoDB
- Required AI/search provider API keys

### Frontend setup
```bash
cd client
npm install
npm run dev
```

### Backend setup
```bash
cd server
python -m venv venv
# Activate the virtual environment for your operating system
pip install -r requirements.txt
# Copy .env.example to .env and configure local secrets securely
uvicorn main:app --reload
```

### Backend environment
Copy `server/.env.example` to `server/.env`. Configure values using a secret manager or local environment. Never commit real credentials.

Required security configuration:
- `MONGODB_URI`: a newly rotated MongoDB connection string
- `JWT_SECRET_KEY`: a cryptographically random secret of at least 32 bytes
- `CORS_ORIGINS`: comma-separated exact frontend origins, including the production origin

Configure provider API keys and email settings only where the corresponding features are enabled. Never place credentials in documentation, source code, screenshots, or issue comments.

## Contributing
1. Fork the repository.
2. Create a feature branch.
3. Commit focused changes with tests.
4. Push your branch and open a pull request.

## Development guidelines
- Use TypeScript for frontend development.
- Follow PEP 8 for Python code.
- Use meaningful names and comments for complex logic.
- Add tests for security-sensitive and critical business logic.
- Keep documentation aligned with the implementation.

## License
This project is licensed under the MIT License. See [LICENSE](./LICENSE).

## Support
For support, email support@marketflickai.com.

## Acknowledgments
- OpenAI for language model APIs
- The Material UI team
- The FastAPI team
- All contributors who helped shape Market Flick AI

---
Made with ❤️ by Team Define Coders

Team members:
1. Ovishek Paul
2. Shawon Majid
3. Nafi Ullah Shafin
4. Sourav Suvra
