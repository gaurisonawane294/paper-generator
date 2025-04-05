import google.generativeai as genai
import streamlit as st
import time
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta
import json

class APIRateLimiter:
    def __init__(self, calls_per_minute=50):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.cache = {}  # Simple cache for responses
        
    def can_make_call(self) -> bool:
        now = datetime.now()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(minutes=1)]
        return len(self.calls) < self.calls_per_minute
    
    def log_call(self):
        self.calls.append(datetime.now())
    
    def get_cached_response(self, prompt: str) -> Optional[str]:
        return self.cache.get(prompt)
    
    def cache_response(self, prompt: str, response: str):
        self.cache[prompt] = response
        # Limit cache size to 1000 items
        if len(self.cache) > 1000:
            self.cache.pop(next(iter(self.cache)))

class QuestionPaperGenerator:
    def __init__(self):
        self.model = self.load_model()
        self.rate_limiter = APIRateLimiter()
        self.load_question_bank()
        
    def load_model(self) -> Optional[genai.GenerativeModel]:
        try:
            api_key = open("api_key.txt","r").read()
            genai.configure(api_key=api_key)
            return genai.GenerativeModel("gemini-1.5-pro")
        except Exception as e:
            st.error(f"Error loading model: {str(e)}")
            return None
    
    def load_question_bank(self):
        try:
            with open('question_bank.json', 'r') as f:
                self.question_bank = json.load(f)
        except FileNotFoundError:
            self.question_bank = {}
            self.save_question_bank()
    
    def save_question_bank(self):
        with open('question_bank.json', 'w') as f:
            json.dump(self.question_bank, f, indent=4)
    
    def get_from_question_bank(self, subject: str, topic: str, question_type: str) -> List[str]:
        return self.question_bank.get(subject, {}).get(topic, {}).get(question_type, [])
    
    def add_to_question_bank(self, subject: str, topic: str, question_type: str, questions: List[str]):
        if subject not in self.question_bank:
            self.question_bank[subject] = {}
        if topic not in self.question_bank[subject]:
            self.question_bank[subject][topic] = {}
        if question_type not in self.question_bank[subject][topic]:
            self.question_bank[subject][topic][question_type] = []
        
        self.question_bank[subject][topic][question_type].extend(questions)
        self.save_question_bank()

    def format_question_prompt(self, requirements: Dict) -> str:
        total_marks = (
            requirements['num_mcq'] + 
            (requirements['num_3_marks'] * 3) + 
            (requirements['num_5_marks'] * 5)
        )
        
        prompt = f"""
        Generate a professional question paper with the following format:

        {requirements.get('subject', '').upper()} EXAMINATION
        Time: 3 Hours                                                  Maximum Marks: {total_marks}

        Instructions:
        1. All questions are compulsory
        2. Write answers clearly and neatly
        3. Start each section on a new page
        4. Numbers to the right indicate full marks

        Subject: {requirements.get('subject', '')}
        Topic: {requirements.get('topic', '')}
        Syllabus Coverage: {requirements.get('syllabus', '')}
        Difficulty Level: {requirements.get('difficulty', 'Medium')}

        Question Distribution:
        Section A: Multiple Choice Questions ({requirements['num_mcq']} × 1 = {requirements['num_mcq']} marks)
        Section B: Short Answer Questions ({requirements['num_3_marks']} × 3 = {requirements['num_3_marks'] * 3} marks)
        Section C: Long Answer Questions ({requirements['num_5_marks']} × 5 = {requirements['num_5_marks'] * 5} marks)

        Format each section as follows:
        1. Section A (MCQs):
           - Clear question stem
           - Four distinct options (a, b, c, d)
           - No ambiguous or overlapping options
           - Proper spacing between questions

        2. Section B (Short Answer):
           - Clear, focused questions
           - Specify marks as [3 Marks] at end
           - Include computational/analytical questions
           - Proper question numbering

        3. Section C (Long Answer):
           - Complex analytical questions
           - Specify marks as [5 Marks] at end
           - Include case studies/scenarios
           - Clear sub-parts if needed

        Generate questions that are:
        - Clear and unambiguous
        - Appropriate for the difficulty level
        - Well-distributed across topics
        - Properly formatted and numbered
        """
        return prompt

    def format_answer_prompt(self, questions: str) -> str:
        return f"""
        Generate a detailed answer key for this question paper:

        {questions}

        Format the answers as follows:

        ANSWER KEY
        ==========

        Section A: Multiple Choice Questions
        - For each MCQ:
          * Write correct option letter
          * Add brief explanation (1-2 lines)
          * Include key concept tested

        Section B: Short Answer Questions
        - For each question:
          * Main points in bullet form
          * Essential formulas/steps
          * Key concepts and definitions
          * Sample calculations if needed

        Section C: Long Answer Questions
        - For each question:
          * Detailed solution outline
          * Step-by-step approach
          * Important concepts/theorems
          * Diagrams/flowcharts if applicable

        Make answers:
        - Clear and concise
        - Well-structured
        - Easy to follow
        - Focused on key points
        """

    def generate_section_questions(self, requirements: Dict, section_type: str) -> Tuple[str, List[str]]:
        # Try to get questions from question bank first
        subject = requirements.get("subject", "")
        topic = requirements.get("topic", "")
        stored_questions = self.get_from_question_bank(subject, topic, section_type)
        
        num_questions = {
            "MCQ": requirements["num_mcq"],
            "descriptive_3": requirements["num_3_marks"],
            "descriptive_5": requirements["num_5_marks"]
        }[section_type]
        
        if num_questions == 0:
            return "", []

        if stored_questions and len(stored_questions) >= num_questions:
            # Use stored questions if available
            selected_questions = stored_questions[:num_questions]
            return "\n\n".join(selected_questions), selected_questions

        # Generate new questions if needed
        prompt = self.format_question_prompt(requirements)
        
        # Check cache first
        cached_response = self.rate_limiter.get_cached_response(prompt)
        if cached_response:
            questions = cached_response.strip().split("\n\n")
            return "\n\n".join(questions), questions

        # Check rate limiting
        if not self.rate_limiter.can_make_call():
            time.sleep(2)  # Wait if rate limit reached
            
        response = self.model.generate_content(prompt)
        self.rate_limiter.log_call()
        
        questions = response.text.strip().split("\n\n")
        self.rate_limiter.cache_response(prompt, response.text)
        
        # Store new questions in question bank
        self.add_to_question_bank(subject, topic, section_type, questions)
        
        return "\n\n".join(questions), questions

    def generate_answers(self, questions: List[str], question_type: str) -> str:
        answer_prompts = {
            "MCQ": """
                For this MCQ question:
                {question}
                
                Provide:
                1. The correct option letter only
                2. A one-line explanation why it's correct
            """,
            "descriptive": """
                For this question:
                {question}
                
                Provide a concise answer with:
                - Main points in bullet form
                - Essential steps/formulas if needed
                - Keep it focused and clear
                - Include only key concepts
            """
        }
        
        answers = []
        for i, question in enumerate(questions, 1):
            prompt = answer_prompts["MCQ" if question_type == "MCQ" else "descriptive"]
            response = self.model.generate_content(prompt.format(question=question))
            answers.append(f"Q{i}. {response.text.strip()}")
        
        return "\n\n".join(answers)

    def get_output(self, requirements: Dict) -> Tuple[str, bool]:
        if not self.model:
            return "Error: Could not load the AI model. Please check your API key.", False
        
        try:
            # Check cache first
            cache_key = str(requirements)
            cached_response = self.rate_limiter.get_cached_response(cache_key)
            if cached_response:
                return cached_response, True

            # Check rate limiting
            if not self.rate_limiter.can_make_call():
                time.sleep(2)  # Wait if rate limit reached

            # Generate all questions in one go
            questions_prompt = self.format_question_prompt(requirements)
            questions_response = self.model.generate_content(questions_prompt)
            self.rate_limiter.log_call()
            
            questions = questions_response.text.strip()

            # Generate all answers in one go
            answers_prompt = self.format_answer_prompt(questions)
            answers_response = self.model.generate_content(answers_prompt)
            self.rate_limiter.log_call()
            
            answers = answers_response.text.strip()

            # Combine output
            separator = "=" * 50
            complete_output = "Question Paper\n" + separator + "\n\n" + questions + "\n\nAnswer Key\n" + separator + "\n\n" + answers

            # Cache the result
            self.rate_limiter.cache_response(cache_key, complete_output)

            return complete_output, True
                        
        except Exception as e:
            return f"Error generating content: {str(e)}", False

# Create a singleton instance
generator = QuestionPaperGenerator()

def get_output(requirements: Dict) -> str:
    output, success = generator.get_output(requirements)
    return output
