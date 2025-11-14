"""Test orchestration for running LLM predictions on personas."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .llm_interface import OllamaInterface, construct_persona_prompt, LLMResponse
from .config import ModelConfig, PERSONAS_DIR, QUESTIONS_DIR, RESULTS_DIR


@dataclass
class TestResult:
    """Results from a single test question."""
    test_id: str
    persona_id: str
    persona_name: str
    question_id: str
    question_text: str
    question_type: str
    llm_response: str
    model: str
    model_config: Dict[str, Any]
    timestamp: str
    generation_time: Optional[float] = None
    tokens_generated: Optional[int] = None
    actual_response: Optional[str] = None
    similarity_score: Optional[float] = None
    notes: Optional[str] = None
    reviewed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class TestSession:
    """A complete test session."""
    session_id: str
    persona_file: str
    question_file: str
    model: str
    model_config: Dict[str, Any]
    timestamp: str
    results: List[TestResult]
    completed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "persona_file": self.persona_file,
            "question_file": self.question_file,
            "model": self.model,
            "model_config": self.model_config,
            "timestamp": self.timestamp,
            "completed": self.completed,
            "results": [r.to_dict() for r in self.results],
        }


class TestRunner:
    """Orchestrates testing of personas with questions."""
    
    def __init__(self, ollama_interface: Optional[OllamaInterface] = None):
        """Initialize the test runner.
        
        Args:
            ollama_interface: Optional OllamaInterface instance
        """
        self.ollama = ollama_interface or OllamaInterface()
        self.results_dir = Path(RESULTS_DIR)
        self.results_dir.mkdir(exist_ok=True)
    
    def load_persona(self, persona_file: str) -> Dict[str, Any]:
        """Load persona data from YAML file.
        
        Args:
            persona_file: Path to persona YAML file
        
        Returns:
            Dictionary containing persona data
        
        Raises:
            FileNotFoundError: If persona file doesn't exist
            ValueError: If YAML is invalid
        """
        path = Path(persona_file)
        if not path.exists():
            raise FileNotFoundError(f"Persona file not found: {persona_file}")
        
        with open(path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                return data
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in persona file: {e}")
    
    def load_questions(self, question_file: str) -> Dict[str, Any]:
        """Load questions from YAML file.
        
        Args:
            question_file: Path to questions YAML file
        
        Returns:
            Dictionary containing question data
        
        Raises:
            FileNotFoundError: If question file doesn't exist
            ValueError: If YAML is invalid
        """
        path = Path(question_file)
        if not path.exists():
            raise FileNotFoundError(f"Question file not found: {question_file}")
        
        with open(path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                return data
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in question file: {e}")
    
    def run_test(
        self,
        persona_file: str,
        question_file: str,
        model: str,
        config: ModelConfig,
        questions_to_test: Optional[List[str]] = None,
    ) -> TestSession:
        """Run a complete test session.
        
        Args:
            persona_file: Path to persona YAML file
            question_file: Path to questions YAML file
            model: Name of the model to use
            config: Model configuration
            questions_to_test: Optional list of specific question IDs to test
        
        Returns:
            TestSession with all results
        
        Raises:
            ConnectionError: If cannot connect to Ollama
            ValueError: If files are invalid
        """
        # Load persona and questions
        persona = self.load_persona(persona_file)
        question_data = self.load_questions(question_file)
        questions = question_data.get("questions", [])
        
        # Filter questions if specific IDs provided
        if questions_to_test:
            questions = [q for q in questions if q["id"] in questions_to_test]
        
        # Create session
        session_id = f"{persona['id']}_{model.replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session = TestSession(
            session_id=session_id,
            persona_file=persona_file,
            question_file=question_file,
            model=model,
            model_config=config.to_dict(),
            timestamp=datetime.now().isoformat(),
            results=[],
        )
        
        # Run each question
        for question in questions:
            result = self._run_single_question(
                persona=persona,
                question=question,
                model=model,
                config=config,
                session_id=session_id,
            )
            session.results.append(result)
        
        session.completed = True
        
        # Save session
        self.save_session(session)
        
        return session
    
    def _run_single_question(
        self,
        persona: Dict[str, Any],
        question: Dict[str, Any],
        model: str,
        config: ModelConfig,
        session_id: str,
    ) -> TestResult:
        """Run a single question test.
        
        Args:
            persona: Persona data
            question: Question data
            model: Model name
            config: Model configuration
            session_id: ID of the test session
        
        Returns:
            TestResult for this question
        """
        # Construct the full question text
        question_text = question["question"]
        if "follow_up" in question:
            question_text += f"\n\n{question['follow_up']}"
        
        # Build prompt
        system_prompt, user_prompt = construct_persona_prompt(persona, question_text)
        
        # Generate response
        llm_response = self.ollama.generate(
            model=model,
            prompt=user_prompt,
            config=config,
            system_prompt=system_prompt,
        )
        
        # Create test result
        test_id = f"{session_id}_{question['id']}"
        result = TestResult(
            test_id=test_id,
            persona_id=persona["id"],
            persona_name=persona["name"],
            question_id=question["id"],
            question_text=question_text,
            question_type=question.get("type", "unknown"),
            llm_response=llm_response.response_text,
            model=model,
            model_config=config.to_dict(),
            timestamp=llm_response.timestamp,
            generation_time=llm_response.generation_time,
            tokens_generated=llm_response.tokens_generated,
        )
        
        return result
    
    def save_session(self, session: TestSession) -> Path:
        """Save test session to JSON file.
        
        Args:
            session: TestSession to save
        
        Returns:
            Path to saved file
        """
        filepath = self.results_dir / f"{session.session_id}.json"
        with open(filepath, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        return filepath
    
    def load_session(self, session_id: str) -> Optional[TestSession]:
        """Load a test session from file.
        
        Args:
            session_id: ID of the session to load
        
        Returns:
            TestSession if found, None otherwise
        """
        filepath = self.results_dir / f"{session_id}.json"
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct TestResult objects
        results = [TestResult(**r) for r in data["results"]]
        
        return TestSession(
            session_id=data["session_id"],
            persona_file=data["persona_file"],
            question_file=data["question_file"],
            model=data["model"],
            model_config=data["model_config"],
            timestamp=data["timestamp"],
            results=results,
            completed=data.get("completed", False),
        )
    
    def list_sessions(self) -> List[str]:
        """List all available test sessions.
        
        Returns:
            List of session IDs
        """
        return [f.stem for f in self.results_dir.glob("*.json")]
    
    def get_unreviewed_sessions(self) -> List[str]:
        """Get sessions that have unreviewed results.
        
        Returns:
            List of session IDs with unreviewed results
        """
        unreviewed = []
        for session_id in self.list_sessions():
            session = self.load_session(session_id)
            if session and any(not r.reviewed for r in session.results):
                unreviewed.append(session_id)
        return unreviewed
    
    def update_result(
        self,
        session_id: str,
        test_id: str,
        actual_response: Optional[str] = None,
        similarity_score: Optional[float] = None,
        notes: Optional[str] = None,
        reviewed: bool = True,
    ) -> bool:
        """Update a test result with actual response and scoring.
        
        Args:
            session_id: ID of the session
            test_id: ID of the test result
            actual_response: The actual response from the real person
            similarity_score: Similarity score (0-5)
            notes: Optional notes about the comparison
            reviewed: Whether this result has been reviewed
        
        Returns:
            True if update successful, False otherwise
        """
        session = self.load_session(session_id)
        if not session:
            return False
        
        # Find and update the result
        for result in session.results:
            if result.test_id == test_id:
                if actual_response is not None:
                    result.actual_response = actual_response
                if similarity_score is not None:
                    result.similarity_score = similarity_score
                if notes is not None:
                    result.notes = notes
                result.reviewed = reviewed
                
                # Save updated session
                self.save_session(session)
                return True
        
        return False

