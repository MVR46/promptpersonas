"""Analytics and reporting for test results."""

import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich import box

from .test_runner import TestRunner, TestSession


class Analytics:
    """Analytics engine for test results."""
    
    def __init__(self, test_runner: Optional[TestRunner] = None):
        """Initialize analytics engine.
        
        Args:
            test_runner: Optional TestRunner instance
        """
        self.runner = test_runner or TestRunner()
        self.console = Console()
    
    def generate_report(self, session_id: str) -> Dict[str, Any]:
        """Generate analytics report for a session.
        
        Args:
            session_id: ID of the session to analyze
        
        Returns:
            Dictionary containing analytics
        """
        session = self.runner.load_session(session_id)
        if not session:
            return {}
        
        reviewed_results = [r for r in session.results if r.reviewed and r.similarity_score is not None]
        
        if not reviewed_results:
            return {
                "session_id": session_id,
                "status": "no_reviews",
                "message": "No reviewed results to analyze"
            }
        
        # Calculate metrics
        scores = [r.similarity_score for r in reviewed_results]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # Score by question type
        scores_by_type = defaultdict(list)
        for r in reviewed_results:
            scores_by_type[r.question_type].append(r.similarity_score)
        
        type_averages = {
            qtype: sum(scores) / len(scores)
            for qtype, scores in scores_by_type.items()
        }
        
        # Performance metrics
        gen_times = [r.generation_time for r in session.results if r.generation_time]
        avg_gen_time = sum(gen_times) / len(gen_times) if gen_times else 0
        
        tokens = [r.tokens_generated for r in session.results if r.tokens_generated]
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0
        
        return {
            "session_id": session_id,
            "model": session.model,
            "persona": session.persona_file,
            "timestamp": session.timestamp,
            "total_questions": len(session.results),
            "reviewed_questions": len(reviewed_results),
            "overall_metrics": {
                "average_similarity": avg_score,
                "min_similarity": min_score,
                "max_similarity": max_score,
                "accuracy_percentage": (avg_score / 5.0) * 100,
            },
            "by_question_type": type_averages,
            "performance_metrics": {
                "avg_generation_time_seconds": avg_gen_time,
                "avg_tokens_generated": avg_tokens,
            },
            "question_breakdown": [
                {
                    "question_id": r.question_id,
                    "type": r.question_type,
                    "similarity_score": r.similarity_score,
                    "notes": r.notes,
                }
                for r in reviewed_results
            ]
        }
    
    def display_report(self, session_id: str):
        """Display analytics report in the console.
        
        Args:
            session_id: ID of the session to analyze
        """
        report = self.generate_report(session_id)
        
        if not report or report.get("status") == "no_reviews":
            self.console.print("[yellow]No reviewed results to analyze[/yellow]")
            return
        
        # Header
        self.console.print(f"\n[bold cyan]Analytics Report: {session_id}[/bold cyan]\n")
        
        # Overall metrics
        metrics = report["overall_metrics"]
        metrics_table = Table(title="Overall Performance", box=box.ROUNDED)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        metrics_table.add_row("Average Similarity", f"{metrics['average_similarity']:.2f}/5.0")
        metrics_table.add_row("Accuracy Percentage", f"{metrics['accuracy_percentage']:.1f}%")
        metrics_table.add_row("Min Score", f"{metrics['min_similarity']:.2f}")
        metrics_table.add_row("Max Score", f"{metrics['max_similarity']:.2f}")
        metrics_table.add_row("Questions Reviewed", f"{report['reviewed_questions']}/{report['total_questions']}")
        
        self.console.print(metrics_table)
        
        # Performance metrics
        perf = report["performance_metrics"]
        perf_table = Table(title="Performance Metrics", box=box.ROUNDED)
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="yellow")
        
        perf_table.add_row("Avg Generation Time", f"{perf['avg_generation_time_seconds']:.2f}s")
        perf_table.add_row("Avg Tokens Generated", f"{perf['avg_tokens_generated']:.0f}")
        
        self.console.print(perf_table)
        
        # By question type
        if report["by_question_type"]:
            type_table = Table(title="Accuracy by Question Type", box=box.ROUNDED)
            type_table.add_column("Question Type", style="cyan")
            type_table.add_column("Avg Similarity", style="green")
            type_table.add_column("Accuracy %", style="yellow")
            
            for qtype, avg in sorted(report["by_question_type"].items()):
                accuracy = (avg / 5.0) * 100
                type_table.add_row(qtype, f"{avg:.2f}/5.0", f"{accuracy:.1f}%")
            
            self.console.print(type_table)
    
    def compare_models(self, session_ids: List[str]) -> Dict[str, Any]:
        """Compare performance across multiple sessions.
        
        Args:
            session_ids: List of session IDs to compare
        
        Returns:
            Comparison data
        """
        comparisons = []
        
        for session_id in session_ids:
            report = self.generate_report(session_id)
            if report and report.get("status") != "no_reviews":
                comparisons.append({
                    "session_id": session_id,
                    "model": report["model"],
                    "avg_similarity": report["overall_metrics"]["average_similarity"],
                    "accuracy_pct": report["overall_metrics"]["accuracy_percentage"],
                    "avg_time": report["performance_metrics"]["avg_generation_time_seconds"],
                    "reviewed": report["reviewed_questions"],
                    "total": report["total_questions"],
                })
        
        return {
            "comparisons": comparisons,
            "best_accuracy": max(comparisons, key=lambda x: x["avg_similarity"]) if comparisons else None,
            "fastest": min(comparisons, key=lambda x: x["avg_time"]) if comparisons else None,
        }
    
    def display_comparison(self, session_ids: List[str]):
        """Display model comparison in console.
        
        Args:
            session_ids: List of session IDs to compare
        """
        comparison = self.compare_models(session_ids)
        
        if not comparison["comparisons"]:
            self.console.print("[yellow]No data to compare[/yellow]")
            return
        
        table = Table(title="Model Comparison", box=box.ROUNDED)
        table.add_column("Model", style="cyan")
        table.add_column("Avg Similarity", style="green")
        table.add_column("Accuracy %", style="yellow")
        table.add_column("Avg Time", style="blue")
        table.add_column("Reviewed", style="white")
        
        for comp in comparison["comparisons"]:
            table.add_row(
                comp["model"],
                f"{comp['avg_similarity']:.2f}/5.0",
                f"{comp['accuracy_pct']:.1f}%",
                f"{comp['avg_time']:.2f}s",
                f"{comp['reviewed']}/{comp['total']}"
            )
        
        self.console.print(table)
        
        # Highlight best performers
        if comparison["best_accuracy"]:
            best = comparison["best_accuracy"]
            self.console.print(f"\n[green]🏆 Most Accurate:[/green] {best['model']} ({best['accuracy_pct']:.1f}%)")
        
        if comparison["fastest"]:
            fastest = comparison["fastest"]
            self.console.print(f"[blue]⚡ Fastest:[/blue] {fastest['model']} ({fastest['avg_time']:.2f}s)")
    
    def export_to_csv(self, session_id: str, output_path: Optional[str] = None) -> Path:
        """Export session results to CSV.
        
        Args:
            session_id: ID of the session to export
            output_path: Optional output path. If None, uses default location.
        
        Returns:
            Path to the exported CSV file
        """
        session = self.runner.load_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if output_path is None:
            output_path = f"{session_id}.csv"
        
        output_file = Path(output_path)
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'question_id',
                'question_type',
                'question_text',
                'llm_response',
                'actual_response',
                'similarity_score',
                'notes',
                'reviewed',
                'generation_time',
                'tokens_generated',
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in session.results:
                writer.writerow({
                    'question_id': result.question_id,
                    'question_type': result.question_type,
                    'question_text': result.question_text[:100] + "..." if len(result.question_text) > 100 else result.question_text,
                    'llm_response': result.llm_response,
                    'actual_response': result.actual_response or "",
                    'similarity_score': result.similarity_score or "",
                    'notes': result.notes or "",
                    'reviewed': result.reviewed,
                    'generation_time': result.generation_time or "",
                    'tokens_generated': result.tokens_generated or "",
                })
        
        return output_file
    
    def export_report_json(self, session_id: str, output_path: Optional[str] = None) -> Path:
        """Export analytics report to JSON.
        
        Args:
            session_id: ID of the session
            output_path: Optional output path
        
        Returns:
            Path to exported JSON file
        """
        report = self.generate_report(session_id)
        
        if output_path is None:
            output_path = f"{session_id}_report.json"
        
        output_file = Path(output_path)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file

