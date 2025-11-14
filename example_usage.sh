#!/bin/bash
# Example usage script for the LLM Persona Testing Pipeline

# This script demonstrates a typical workflow

echo "=== LLM Persona Testing Pipeline - Example Workflow ==="
echo ""

# 1. Check status
echo "1. Checking system status..."
python main.py status
echo ""

# 2. List available models
echo "2. Listing available models..."
python main.py models --list
echo ""

# 3. Show recommended models for M1 Mac
echo "3. Recommended models for M1 Mac:"
python main.py models --recommended
echo ""

# Uncomment to pull a model if needed:
# echo "Pulling llama3 model..."
# python main.py models --pull llama3

# 4. Run a test with tech enthusiast persona
echo "4. Running test with tech enthusiast persona..."
python main.py test \
    --persona personas/example_tech_enthusiast.yaml \
    --questions questions/product_choices.yaml \
    --model llama3 \
    --config balanced
echo ""

# 5. Review results (interactive - this would need manual input)
# python main.py review
# echo ""

# 6. Analyze results (replace SESSION_ID with actual session ID from step 4)
# python main.py analyze SESSION_ID
# echo ""

# 7. Compare multiple sessions
# python main.py analyze SESSION_ID_1 -c SESSION_ID_2 -c SESSION_ID_3
# echo ""

# 8. Export results
# python main.py analyze SESSION_ID --export-csv results.csv --export-json report.json

echo "=== Example workflow commands shown above ==="
echo "Run 'python main.py quickstart' for the quick start guide"

