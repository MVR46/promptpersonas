#!/usr/bin/env python3
"""Main CLI entry point for LLM Persona Testing Pipeline."""

import click
from pathlib import Path
from rich.console import Console

from src.llm_interface import OllamaInterface
from src.test_runner import TestRunner
from src.review_ui import ReviewUI
from src.analytics import Analytics
from src.config import ModelConfig, DEFAULT_CONFIGS, RECOMMENDED_MODELS


console = Console()


@click.group()
def cli():
    """LLM Persona Testing Pipeline - Test behavioral predictions with local LLMs."""
    pass


@cli.command()
@click.option('--persona', '-p', required=True, type=click.Path(exists=True),
              help='Path to persona YAML file')
@click.option('--questions', '-q', required=True, type=click.Path(exists=True),
              help='Path to questions YAML file')
@click.option('--model', '-m', required=True, help='Ollama model name (e.g., llama3, mistral)')
@click.option('--config', '-c', type=click.Choice(['balanced', 'creative', 'precise', 'deterministic']),
              default='balanced', help='Model configuration preset')
@click.option('--temperature', '-t', type=float, help='Override temperature (0.0-1.0)')
@click.option('--top-p', type=float, help='Override top_p sampling parameter')
def test(persona, questions, model, config, temperature, top_p):
    """Run LLM predictions on a persona with given questions."""
    console.print(f"[cyan]Starting test with {model}...[/cyan]")
    
    # Check Ollama connection
    ollama = OllamaInterface()
    if not ollama.check_connection():
        console.print("[red]Error: Cannot connect to Ollama.[/red]")
        console.print("Make sure Ollama is running: [cyan]ollama serve[/cyan]")
        return
    
    # Check if model is available
    available_models = ollama.list_models()
    if model not in available_models:
        console.print(f"[yellow]Warning: Model '{model}' not found locally.[/yellow]")
        console.print("Available models:", ", ".join(available_models))
        if click.confirm(f"Would you like to pull {model}?"):
            console.print(f"Pulling {model}... (this may take a few minutes)")
            if ollama.pull_model(model):
                console.print("[green]✓ Model downloaded successfully[/green]")
            else:
                console.print("[red]✗ Failed to download model[/red]")
                return
        else:
            return
    
    # Get model configuration
    model_config = DEFAULT_CONFIGS[config]
    model_config.name = model
    
    # Apply overrides
    if temperature is not None:
        model_config.temperature = temperature
    if top_p is not None:
        model_config.top_p = top_p
    
    console.print(f"[dim]Config: {config} (temp={model_config.temperature}, top_p={model_config.top_p})[/dim]")
    
    # Run test
    runner = TestRunner(ollama)
    
    try:
        session = runner.run_test(
            persona_file=persona,
            question_file=questions,
            model=model,
            config=model_config,
        )
        
        console.print(f"\n[green]✓ Test complete![/green]")
        console.print(f"Session ID: [cyan]{session.session_id}[/cyan]")
        console.print(f"Questions tested: {len(session.results)}")
        console.print(f"\nReview results with: [cyan]python main.py review {session.session_id}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error running test: {e}[/red]")
        import traceback
        traceback.print_exc()


@cli.command()
@click.argument('session_id', required=False)
@click.option('--list', '-l', 'list_sessions', is_flag=True, help='List all available sessions')
def review(session_id, list_sessions):
    """Review test results interactively."""
    ui = ReviewUI()
    
    if list_sessions:
        ui.list_sessions()
        return
    
    if session_id:
        ui.review_session(session_id)
    else:
        # Auto-select unreviewed session
        ui.review_session(auto_select=True)


@cli.command()
@click.argument('session_id')
@click.option('--compare', '-c', multiple=True, help='Additional session IDs to compare')
@click.option('--export-csv', type=click.Path(), help='Export to CSV file')
@click.option('--export-json', type=click.Path(), help='Export report to JSON')
def analyze(session_id, compare, export_csv, export_json):
    """Generate analytics and reports for test results."""
    analytics = Analytics()
    
    if compare:
        # Compare multiple sessions
        all_sessions = [session_id] + list(compare)
        console.print(f"[cyan]Comparing {len(all_sessions)} sessions...[/cyan]\n")
        analytics.display_comparison(all_sessions)
    else:
        # Single session report
        analytics.display_report(session_id)
    
    # Export if requested
    if export_csv:
        try:
            output = analytics.export_to_csv(session_id, export_csv)
            console.print(f"\n[green]✓ Exported to CSV:[/green] {output}")
        except Exception as e:
            console.print(f"[red]Error exporting CSV: {e}[/red]")
    
    if export_json:
        try:
            output = analytics.export_report_json(session_id, export_json)
            console.print(f"[green]✓ Exported report to JSON:[/green] {output}")
        except Exception as e:
            console.print(f"[red]Error exporting JSON: {e}[/red]")


@cli.command()
@click.argument('session_id')
def results(session_id):
    """View results summary for a session."""
    ui = ReviewUI()
    ui.view_results(session_id)


@cli.command()
@click.option('--list', '-l', 'list_only', is_flag=True, help='List available models')
@click.option('--pull', '-p', help='Pull a specific model')
@click.option('--recommended', '-r', is_flag=True, help='Show recommended models for M1 Mac')
def models(list_only, pull, recommended):
    """Manage Ollama models."""
    ollama = OllamaInterface()
    
    if not ollama.check_connection():
        console.print("[red]Error: Cannot connect to Ollama.[/red]")
        console.print("Make sure Ollama is running: [cyan]ollama serve[/cyan]")
        return
    
    if recommended:
        console.print("[bold cyan]Recommended models for M1 Mac:[/bold cyan]")
        for model in RECOMMENDED_MODELS:
            console.print(f"  • {model}")
        console.print("\nPull a model with: [cyan]python main.py models --pull <model>[/cyan]")
        return
    
    if pull:
        console.print(f"Pulling {pull}... (this may take several minutes)")
        if ollama.pull_model(pull):
            console.print(f"[green]✓ Successfully pulled {pull}[/green]")
        else:
            console.print(f"[red]✗ Failed to pull {pull}[/red]")
        return
    
    # List available models
    try:
        available = ollama.list_models()
        if available:
            console.print("[bold cyan]Available models:[/bold cyan]")
            for model in available:
                console.print(f"  • {model}")
        else:
            console.print("[yellow]No models installed.[/yellow]")
            console.print("Pull a model with: [cyan]python main.py models --pull llama3[/cyan]")
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")


@cli.command()
def status():
    """Check system status and configuration."""
    console.print("[bold cyan]LLM Persona Testing Pipeline - System Status[/bold cyan]\n")
    
    # Check Ollama
    ollama = OllamaInterface()
    if ollama.check_connection():
        console.print("[green]✓ Ollama connection:[/green] OK")
        try:
            models = ollama.list_models()
            console.print(f"[green]✓ Available models:[/green] {len(models)}")
        except:
            console.print("[yellow]⚠ Could not list models[/yellow]")
    else:
        console.print("[red]✗ Ollama connection:[/red] Failed")
        console.print("  Start Ollama with: [cyan]ollama serve[/cyan]")
    
    # Check directories
    personas_dir = Path("personas")
    questions_dir = Path("questions")
    results_dir = Path("results")
    
    persona_count = len(list(personas_dir.glob("*.yaml"))) if personas_dir.exists() else 0
    question_count = len(list(questions_dir.glob("*.yaml"))) if questions_dir.exists() else 0
    result_count = len(list(results_dir.glob("*.json"))) if results_dir.exists() else 0
    
    console.print(f"[green]✓ Personas:[/green] {persona_count} available")
    console.print(f"[green]✓ Question sets:[/green] {question_count} available")
    console.print(f"[green]✓ Test sessions:[/green] {result_count} saved")
    
    # Unreviewed sessions
    runner = TestRunner()
    unreviewed = runner.get_unreviewed_sessions()
    if unreviewed:
        console.print(f"\n[yellow]⚠ Unreviewed sessions:[/yellow] {len(unreviewed)}")
        console.print("  Review with: [cyan]python main.py review[/cyan]")


@cli.command()
def quickstart():
    """Show a quickstart guide."""
    guide = """
[bold cyan]LLM Persona Testing Pipeline - Quick Start Guide[/bold cyan]

[bold]1. Install and start Ollama:[/bold]
   Visit: https://ollama.ai/
   Then run: [cyan]ollama serve[/cyan]

[bold]2. Pull a recommended model:[/bold]
   [cyan]python main.py models --pull llama3[/cyan]
   
   See all recommended models:
   [cyan]python main.py models --recommended[/cyan]

[bold]3. Run a test:[/bold]
   [cyan]python main.py test \\
       --persona personas/example_tech_enthusiast.yaml \\
       --questions questions/product_choices.yaml \\
       --model llama3[/cyan]

[bold]4. Review results (compare LLM vs actual responses):[/bold]
   [cyan]python main.py review[/cyan]
   
   You'll be prompted to input the actual person's responses
   and rate similarity (1-5 scale).

[bold]5. Analyze results:[/bold]
   [cyan]python main.py analyze <session_id>[/cyan]
   
   Compare multiple models:
   [cyan]python main.py analyze <session1> -c <session2> -c <session3>[/cyan]

[bold]6. Export data:[/bold]
   [cyan]python main.py analyze <session_id> --export-csv results.csv[/cyan]

[bold]Tips:[/bold]
• Edit persona YAML files to test different profiles
• Try different model configurations: --config creative, precise, etc.
• Use [cyan]python main.py status[/cyan] to check your setup
"""
    console.print(guide)


if __name__ == '__main__':
    cli()

