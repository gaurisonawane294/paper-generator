import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class HistoryManager:
    def __init__(self, history_file: str = "paper_history.json"):
        self.history_file = history_file
        self.history = self.load_history()
        
    def load_history(self) -> List[Dict]:
        """Load history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_paper(self, questions: str, answers: Optional[str], metadata: Dict):
        """Add a new paper to history"""
        paper = {
            'id': len(self.history) + 1,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'questions': questions,
            'answers': answers,
            'metadata': metadata
        }
        self.history.append(paper)
        self.save_history()
        return paper['id']
    
    def get_paper(self, paper_id: int) -> Optional[Dict]:
        """Get a specific paper by ID"""
        for paper in self.history:
            if paper['id'] == paper_id:
                return paper
        return None
    
    def get_all_papers(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all papers, optionally limited to a number"""
        papers = sorted(self.history, key=lambda x: x['timestamp'], reverse=True)
        return papers[:limit] if limit else papers
    
    def delete_paper(self, paper_id: int) -> bool:
        """Delete a paper from history"""
        for i, paper in enumerate(self.history):
            if paper['id'] == paper_id:
                self.history.pop(i)
                self.save_history()
                return True
        return False
    
    def search_papers(self, query: str) -> List[Dict]:
        """Search papers by subject or topic"""
        query = query.lower()
        return [
            paper for paper in self.history
            if query in paper['metadata'].get('subject', '').lower() or
               query in paper['metadata'].get('topic', '').lower()
        ]
    
    def get_statistics(self) -> Dict:
        """Get statistics about generated papers"""
        return {
            'total_papers': len(self.history),
            'papers_by_subject': self._count_by_field('subject'),
            'papers_by_difficulty': self._count_by_field('difficulty'),
            'average_marks': self._calculate_average_marks()
        }
    
    def _count_by_field(self, field: str) -> Dict:
        """Helper to count papers by a metadata field"""
        counts = {}
        for paper in self.history:
            value = paper['metadata'].get(field, 'Unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _calculate_average_marks(self) -> float:
        """Calculate average total marks across all papers"""
        total = sum(
            paper['metadata'].get('total_marks', 0) 
            for paper in self.history
        )
        return total / len(self.history) if self.history else 0 