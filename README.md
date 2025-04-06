# Conference Monitor Agent

An AI-powered agent for tracking academic conferences, papers, and research trends in your field of interest.

## Features

- **Track Conferences**: Monitor upcoming academic conferences in various research areas
- **Conference Deadlines**: Keep track of call for papers and submission deadlines
- **Paper Monitoring**: Find and summarize recently published papers in specific research areas
- **Trend Analysis**: Identify trending topics and emerging research directions
- **Report Generation**: Generate comprehensive reports on conferences, papers, and trends
- **REST API**: Access all functionality through a clean HTTP API interface

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API keys in the `.env` file:

```
# Google API Key (for Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI API Key (alternative)
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Command Line Interface

The agent can be used through a command-line interface:

```bash
# Run the API server
python -m conference_monitor.main api

# Monitor conferences and papers
python -m conference_monitor.main monitor --areas "artificial intelligence" "machine learning"

# Run a one-time refresh of data
python -m conference_monitor.main monitor --once

# Generate reports
python -m conference_monitor.main report conferences
python -m conference_monitor.main report papers --area "machine learning"
python -m conference_monitor.main report trends
```

### REST API

The agent provides a RESTful API that can be accessed at `http://localhost:5000`:

```bash
# Start the API server
python -m conference_monitor.main api
```

#### API Endpoints

- `GET /api/status` - Get API server status
- `GET /api/conferences` - List all tracked conferences
- `POST /api/conferences/refresh` - Refresh conference data
- `GET /api/papers` - List all tracked papers
- `POST /api/papers/refresh` - Refresh paper data
- `GET /api/trends` - Get trending topics in research areas
- `POST /api/query` - Run direct queries against the AI model
- `GET /api/research-areas` - List tracked research areas
- `POST /api/research-areas` - Update tracked research areas

For full API documentation, see `conference_monitor/api/swagger.yaml`.

### Testing the API

Run the included test script to verify the API is working correctly:

```bash
python -m conference_monitor.api.test_api
```

## Architecture

The system is structured as follows:

- **Core**: Base agent functionality, browser interface, and memory management
- **Tools**: Specialized tools for searching conferences, papers, and analyzing trends
- **Models**: Data models for conferences, papers, and trends
- **Services**: Higher-level services for monitoring and report generation
- **API**: Flask-based REST API for accessing functionality

## Extending

To add support for new sources or features:

1. Add new tools in the `tools` directory
2. Update the relevant services in the `services` directory
3. Add new API endpoints to the Flask app if needed

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
