# Conference Monitor Agent

An AI-powered agent for tracking academic conferences, papers, and research trends in your field of interest.

## Features

- **Track Conferences**: Monitor upcoming academic conferences in various research areas
- **Conference Deadlines**: Keep track of call for papers and submission deadlines
- **Paper Monitoring**: Find and summarize recently published papers in specific research areas
- **Trend Analysis**: Identify trending topics and emerging research directions
- **Report Generation**: Generate comprehensive reports on conferences, papers, and trends

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API keys:

```bash
# For OpenAI API
export OPENAI_API_KEY=your_api_key_here

# For Semantic Scholar (optional)
export SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

## Usage

### Command Line Interface

The agent can be used through a command-line interface:

```bash
# Run the UI
python -m conference_monitor.main ui

# Monitor conferences and papers
python -m conference_monitor.main monitor --areas "artificial intelligence" "machine learning"

# Run a one-time refresh of data
python -m conference_monitor.main monitor --once

# Generate reports
python -m conference_monitor.main report conferences
python -m conference_monitor.main report papers --area "machine learning"
python -m conference_monitor.main report trends
```

### Streamlit UI

The agent includes a Streamlit-based user interface:

```bash
# Start the UI
python -m conference_monitor.main ui
```

Or directly:

```bash
streamlit run conference_monitor/ui/streamlit_app.py
```

## Architecture

The system is structured as follows:

- **Core**: Base agent functionality, browser interface, and memory management
- **Tools**: Specialized tools for searching conferences, papers, and analyzing trends
- **Models**: Data models for conferences, papers, and trends
- **Services**: Higher-level services for monitoring and report generation
- **UI**: Streamlit-based user interface

## Extending

To add support for new sources or features:

1. Add new tools in the `tools` directory
2. Update the relevant services in the `services` directory
3. Add UI components to the Streamlit app if needed

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
