# Quick Start Guide

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and Start Ollama

Visit [https://ollama.ai/](https://ollama.ai/) and download Ollama for macOS.

After installation, start Ollama:

```bash
ollama serve
```

### 3. Pull a Model

For your M1 Pro Mac, these models work great:

```bash
# Recommended: Fast and capable
ollama pull llama3:8b

# Alternative options:
ollama pull mistral:7b
ollama pull phi3:medium
ollama pull gemma2:9b
```

Or use the CLI:

```bash
python main.py models --recommended  # See all recommended models
python main.py models --pull llama3  # Pull a specific model
```

## Basic Workflow

### 1. Check Your Setup

```bash
python main.py status
```

### 2. Run Your First Test

```bash
python main.py test \
    --persona personas/example_tech_enthusiast.yaml \
    --questions questions/product_choices.yaml \
    --model llama3
```

This will:
- Load the tech enthusiast persona
- Ask the LLM to respond to product choice questions as that persona
- Save results with a unique session ID

### 3. Review Results Interactively

```bash
python main.py review
```

This launches an interactive terminal UI where you:
1. See each question and the LLM's response
2. Enter the **actual response** from the real person (from your survey)
3. Rate similarity (1-5 scale)
4. Optionally add notes

### 4. Analyze Results

```bash
python main.py analyze <session_id>
```

View:
- Average similarity scores
- Accuracy percentages
- Performance by question type
- Generation time metrics

### 5. Compare Multiple Models

Test the same persona with different models:

```bash
# Test with llama3
python main.py test -p personas/example_tech_enthusiast.yaml \
    -q questions/product_choices.yaml -m llama3

# Test with mistral
python main.py test -p personas/example_tech_enthusiast.yaml \
    -q questions/product_choices.yaml -m mistral

# Compare results
python main.py analyze <session_id_1> -c <session_id_2>
```

## Creating Your Own Personas

Edit or create YAML files in the `personas/` directory:

```yaml
name: "Your Person Name"
id: "unique_id"

demographics:
  age: 30
  occupation: "Job Title"
  location: "City, State"
  income_level: "middle"

personality:
  traits:
    - trait1
    - trait2
  values:
    - value1
    - value2

shopping_behavior:
  price_sensitivity: "medium"
  decision_factors:
    - factor1
    - factor2

behavioral_notes: |
  Describe how this person makes decisions, what influences them,
  and any relevant background information.
```

## Testing Different Scenarios

### Use Different Model Configurations

```bash
# More creative responses
python main.py test -p personas/example_tech_enthusiast.yaml \
    -q questions/product_choices.yaml -m llama3 --config creative

# More precise/deterministic
python main.py test -p personas/example_tech_enthusiast.yaml \
    -q questions/product_choices.yaml -m llama3 --config precise

# Custom temperature
python main.py test -p personas/example_tech_enthusiast.yaml \
    -q questions/product_choices.yaml -m llama3 --temperature 0.5
```

### Export Results

```bash
# Export to CSV for spreadsheet analysis
python main.py analyze <session_id> --export-csv results.csv

# Export full report to JSON
python main.py analyze <session_id> --export-json report.json
```

## Tips for Best Results

1. **Persona Detail**: The more detailed your persona description, the better the LLM can role-play
2. **Survey Real People**: Get actual responses from people matching your personas for accurate comparison
3. **Test Multiple Models**: Different models may capture different aspects of behavior
4. **Try Various Configs**: Temperature and other settings can significantly affect responses
5. **Iterate**: Use results to refine your persona descriptions and questions

## Troubleshooting

### "Cannot connect to Ollama"

Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found"

Pull the model first:
```bash
python main.py models --pull llama3
```

### View All Sessions

```bash
python main.py review --list
```

### Check Results

```bash
python main.py results <session_id>
```

## Full Command Reference

```bash
python main.py --help              # Show all commands
python main.py test --help         # Show test options
python main.py review --help       # Show review options
python main.py analyze --help      # Show analyze options
python main.py quickstart          # Show quick start in terminal
```

## Example Workflow

```bash
# 1. Check setup
python main.py status

# 2. Run test
python main.py test -p personas/example_tech_enthusiast.yaml \
    -q questions/product_choices.yaml -m llama3

# 3. Note the session ID from output, then review
python main.py review <session_id>

# 4. Analyze
python main.py analyze <session_id>

# 5. Export
python main.py analyze <session_id> --export-csv results.csv
```

