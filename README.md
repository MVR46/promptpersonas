


<img width="1000" height="500" alt="ChatGPT Image Nov 14, 2025, 07_40_29 PM" src="https://github.com/user-attachments/assets/8fbe6eae-e2e3-4ed7-91bd-d481082da87a" />


# LLM Persona Testing Pipeline

A Python pipeline for testing the accuracy of LLM-based behavioral predictions using local open source models.

## Overview

This tool allows you to:
- Define personas in simple YAML files
- Test how well LLMs predict their behavior on product reviews
- Compare predictions with actual survey responses
- Analyze accuracy across different models and settings

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Recommended models: `llama3`, `mistral`, `phi3`

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Install Ollama models:**
```bash
ollama pull llama3
ollama pull mistral
```

2. **Create or edit a persona:**
Edit `personas/example_persona.yaml` or create your own

3. **Run a test:**
```bash
python main.py test --persona personas/example_persona.yaml --model llama3
```

4. **Review results interactively:**
```bash
python main.py review
```

5. **Generate analytics:**
```bash
python main.py analyze
```

## Usage

### Commands

- `test` - Run LLM predictions on a persona
- `review` - Interactive interface to compare with actual responses
- `analyze` - Generate accuracy metrics and reports
- `export` - Export results to CSV

### Testing with Different Settings

```bash
python main.py test --persona personas/tech_savvy.yaml \
                     --model llama3 \
                     --temperature 0.7 \
                     --top-p 0.9
```

## Project Structure

```
promptpersonas/
├── personas/          # Persona definitions (YAML)
├── questions/         # Test scenarios (YAML)
├── results/          # Test results (JSON)
├── src/              # Core modules
├── main.py           # CLI entry point
└── requirements.txt
```

## How It Works

1. **Persona Definition:** Describe a person's demographics, preferences, and behavior patterns
2. **LLM Testing:** The system constructs prompts combining persona context with product questions
3. **Interactive Review:** Compare LLM predictions with actual survey responses
4. **Analytics:** Calculate accuracy metrics across models and settings

## License

MIT

