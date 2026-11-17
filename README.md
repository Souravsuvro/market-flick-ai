# Market Flick AI 🚀

Market Flick AI is a business analysis platform for market research, competitor analysis, and strategic recommendations.

## Features
- Market and sector analysis
- Competitor landscape and positioning
- TAM, SAM, and SOM estimates
- SWOT, PESTLE, and Porter's Five Forces
- Market trends, strategic recommendations, and exportable reports

## Technical Documentation
See [Technical Documentation](./Technical_Documentation.md).

## Video Demo
[Watch the demo](https://www.loom.com/share/145e85e6659d47f2b00a0f2ef0703586).

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.8+
- MongoDB
- Required AI/search provider API keys

### Frontend
```bash
cd client
npm install
npm run dev
```

### Backend
```bash
cd server
python -m venv venv
# Activate the virtual environment for your operating system
pip install -r requirements.txt
# Create server/.env from server/.env.example and set real values securely
uvicorn main:app --reload
```

### Backend environment
Copy `server/.env.example` to `server/.env`. Configure each required value using your secret manager or local environment. Never commit real credentials.

Required security configuration:
- `MONGODB_URI`: a newly rotated MongoDB connection string
- `JWT_SECRET_KEY`: a cryptographically random secret (at least 32 bytes)
- `CORS_ORIGINS`: comma-separated exact frontend origins, including the production origin

Provider API keys and email settings should be configured only where the corresponding features are enabled. Do not put credentials in documentation, source code, screenshots, or issue comments.

## Contributing
1. Fork the repository.
2. Create a feature branch.
3. Commit focused changes with tests.
4. Open a pull request.

## Development guidelines
- Use TypeScript for frontend development.
- Follow PEP 8 for Python code.
- Add tests for security-sensitive and critical business logic.
- Keep documentation aligned with the current implementation.

## License
MIT. See [LICENSE](./LICENSE).

## Support
For support, contact support@marketflickai.com.

---
Made with ❤️ by Team Define Coders
