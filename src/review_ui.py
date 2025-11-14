"""Interactive terminal UI for reviewing and comparing test results."""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box

from .test_runner import TestRunner, TestSession, TestResult


class ReviewUI:
    """Interactive UI for reviewing test results."""
    
    def __init__(self, test_runner: Optional[TestRunner] = None):
        """Initialize the review UI.
        
        Args:
            test_runner: Optional TestRunner instance
        """
        self.runner = test_runner or TestRunner()
        self.console = Console()
    
    def list_sessions(self):
        """Display all available test sessions."""
        sessions = self.runner.list_sessions()
        
        if not sessions:
            self.console.print("[yellow]No test sessions found.[/yellow]")
            self.console.print("Run a test first with: [cyan]python main.py test[/cyan]")
            return
        
        table = Table(title="Available Test Sessions", box=box.ROUNDED)
        table.add_column("Session ID", style="cyan")
        table.add_column("Status", style="green")
        
        for session_id in sessions:
            session = self.runner.load_session(session_id)
            if session:
                reviewed_count = sum(1 for r in session.results if r.reviewed)
                total_count = len(session.results)
                status = f"{reviewed_count}/{total_count} reviewed"
                if reviewed_count == total_count:
                    status = "[green]✓ Complete[/green]"
                elif reviewed_count > 0:
                    status = f"[yellow]⚠ Partial ({reviewed_count}/{total_count})[/yellow]"
                else:
                    status = f"[red]✗ Unreviewed ({total_count})[/red]"
                
                table.add_row(session_id, status)
        
        self.console.print(table)
    
    def review_session(self, session_id: Optional[str] = None, auto_select: bool = True):
        """Review a test session interactively.
        
        Args:
            session_id: Optional session ID to review. If None, will prompt user.
            auto_select: If True and no session_id provided, automatically select
                        the first unreviewed session
        """
        # Load session
        if not session_id:
            unreviewed = self.runner.get_unreviewed_sessions()
            if not unreviewed:
                self.console.print("[yellow]No unreviewed sessions found.[/yellow]")
                return
            
            if auto_select:
                session_id = unreviewed[0]
                self.console.print(f"[cyan]Auto-selecting unreviewed session:[/cyan] {session_id}")
            else:
                self.console.print("\n[bold]Unreviewed sessions:[/bold]")
                for i, sid in enumerate(unreviewed, 1):
                    self.console.print(f"  {i}. {sid}")
                
                choice = Prompt.ask(
                    "Select a session number",
                    choices=[str(i) for i in range(1, len(unreviewed) + 1)]
                )
                session_id = unreviewed[int(choice) - 1]
        
        session = self.runner.load_session(session_id)
        if not session:
            self.console.print(f"[red]Session not found:[/red] {session_id}")
            return
        
        # Display session info
        self._display_session_header(session)
        
        # Review each result
        for i, result in enumerate(session.results, 1):
            if result.reviewed:
                continue  # Skip already reviewed
            
            self.console.print(f"\n[bold cyan]Question {i}/{len(session.results)}[/bold cyan]")
            self._review_result(session_id, result)
        
        self.console.print("\n[green]✓ Review complete![/green]")
    
    def _display_session_header(self, session: TestSession):
        """Display session information header."""
        self.console.print()
        info_text = (
            f"[bold]Session:[/bold] {session.session_id}\n"
            f"[bold]Persona:[/bold] {session.persona_file}\n"
            f"[bold]Model:[/bold] {session.model}\n"
            f"[bold]Questions:[/bold] {len(session.results)}\n"
            f"[bold]Timestamp:[/bold] {session.timestamp}"
        )
        self.console.print(Panel(info_text, title="Test Session", border_style="blue"))
    
    def _review_result(self, session_id: str, result: TestResult):
        """Review a single test result.
        
        Args:
            session_id: ID of the session
            result: TestResult to review
        """
        # Display question
        question_panel = Panel(
            result.question_text,
            title=f"Question ({result.question_type})",
            border_style="yellow",
            box=box.ROUNDED
        )
        self.console.print(question_panel)
        
        # Display LLM response
        llm_text = Text(result.llm_response)
        llm_panel = Panel(
            llm_text,
            title=f"LLM Response ({result.model})",
            border_style="cyan",
            box=box.ROUNDED
        )
        self.console.print(llm_panel)
        
        # Get actual response
        self.console.print("\n[bold green]Enter the actual response from the real person:[/bold green]")
        self.console.print("[dim](You can survey the real person and input their response here)[/dim]")
        actual_response = Prompt.ask("Actual response")
        
        # Display comparison
        self.console.print("\n[bold]Comparison:[/bold]")
        comparison_table = Table(box=box.SIMPLE)
        comparison_table.add_column("LLM", style="cyan", width=50)
        comparison_table.add_column("Actual", style="green", width=50)
        comparison_table.add_row(
            result.llm_response[:200] + "..." if len(result.llm_response) > 200 else result.llm_response,
            actual_response[:200] + "..." if len(actual_response) > 200 else actual_response
        )
        self.console.print(comparison_table)
        
        # Get similarity score
        self.console.print("\n[bold]Rate the similarity:[/bold]")
        self.console.print("1 = Completely different")
        self.console.print("2 = Somewhat different") 
        self.console.print("3 = Neutral/Mixed")
        self.console.print("4 = Quite similar")
        self.console.print("5 = Very similar/accurate")
        
        score = None
        while score is None:
            try:
                score_input = Prompt.ask("Similarity score", choices=["1", "2", "3", "4", "5"])
                score = float(score_input)
            except ValueError:
                self.console.print("[red]Please enter a number between 1 and 5[/red]")
        
        # Optional notes
        add_notes = Confirm.ask("Add notes?", default=False)
        notes = None
        if add_notes:
            notes = Prompt.ask("Notes")
        
        # Update result
        success = self.runner.update_result(
            session_id=session_id,
            test_id=result.test_id,
            actual_response=actual_response,
            similarity_score=score,
            notes=notes,
            reviewed=True
        )
        
        if success:
            self.console.print("[green]✓ Saved[/green]")
        else:
            self.console.print("[red]✗ Failed to save[/red]")
    
    def view_results(self, session_id: str):
        """View results for a session.
        
        Args:
            session_id: ID of the session to view
        """
        session = self.runner.load_session(session_id)
        if not session:
            self.console.print(f"[red]Session not found:[/red] {session_id}")
            return
        
        self._display_session_header(session)
        
        # Results table
        table = Table(title="Test Results", box=box.ROUNDED)
        table.add_column("Q#", style="cyan", width=4)
        table.add_column("Question ID", style="white", width=25)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Score", style="green", width=6)
        table.add_column("Status", style="blue", width=10)
        
        for i, result in enumerate(session.results, 1):
            score = f"{result.similarity_score:.1f}" if result.similarity_score else "—"
            status = "✓ Done" if result.reviewed else "⚠ Pending"
            status_style = "green" if result.reviewed else "yellow"
            
            table.add_row(
                str(i),
                result.question_id,
                result.question_type,
                score,
                f"[{status_style}]{status}[/{status_style}]"
            )
        
        self.console.print(table)
        
        # Summary statistics
        if any(r.reviewed for r in session.results):
            reviewed_results = [r for r in session.results if r.reviewed and r.similarity_score]
            if reviewed_results:
                avg_score = sum(r.similarity_score for r in reviewed_results) / len(reviewed_results)
                self.console.print(f"\n[bold]Average Similarity Score:[/bold] {avg_score:.2f}/5.0")
    
    def compare_sessions(self, session_ids: list[str]):
        """Compare results across multiple sessions.
        
        Args:
            session_ids: List of session IDs to compare
        """
        if len(session_ids) < 2:
            self.console.print("[yellow]Need at least 2 sessions to compare[/yellow]")
            return
        
        sessions = []
        for sid in session_ids:
            session = self.runner.load_session(sid)
            if session:
                sessions.append(session)
            else:
                self.console.print(f"[yellow]Warning: Session not found: {sid}[/yellow]")
        
        if len(sessions) < 2:
            self.console.print("[red]Not enough valid sessions to compare[/red]")
            return
        
        # Comparison table
        table = Table(title="Session Comparison", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        for session in sessions:
            model_name = session.model.split(':')[0]  # Show just model name
            table.add_column(model_name, style="white")
        
        # Average scores
        avg_scores = []
        for session in sessions:
            reviewed = [r for r in session.results if r.reviewed and r.similarity_score]
            if reviewed:
                avg = sum(r.similarity_score for r in reviewed) / len(reviewed)
                avg_scores.append(f"{avg:.2f}")
            else:
                avg_scores.append("—")
        table.add_row("Avg Score", *avg_scores)
        
        # Review completion
        completions = []
        for session in sessions:
            reviewed_count = sum(1 for r in session.results if r.reviewed)
            completions.append(f"{reviewed_count}/{len(session.results)}")
        table.add_row("Reviewed", *completions)
        
        # Avg generation time
        gen_times = []
        for session in sessions:
            times = [r.generation_time for r in session.results if r.generation_time]
            if times:
                avg_time = sum(times) / len(times)
                gen_times.append(f"{avg_time:.1f}s")
            else:
                gen_times.append("—")
        table.add_row("Avg Time", *gen_times)
        
        self.console.print(table)

