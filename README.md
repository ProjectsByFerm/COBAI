COBOL AI Agent for Precision Learning is an intelligent system designed to help users master COBOL with accuracy, clarity, and efficiency. 

COBAI is a structured AI-powered learning and evaluation framework designed to teach and assess COBOL programming skills using LLM-driven coaching, scoring, and research-based experimentation.


COBAI combines:

- Structured learning modules
- AI coaching (LLM integration)
- Performance scoring & evaluation
- Research-driven experimentation

The system is built to analyze how effectively AI can teach programming concepts—specifically COBOL—through guided tasks, feedback loops, and measurable outcomes.

KEY FEATURES

AI Coach
Provides guided assistance on COBOL tasks
Uses prompt-engineered learning strategies
Task-Based Learning
Modular COBOL exercises (MOVE, IF, COMPUTE, etc.)
JSON-based task definitions
Automated Scoring
Evaluates correctness and performance
Standardized scoring pipeline
Experiment Framework
Run structured studies on learning effectiveness
Export and analyze results

⚙️ Setup
1. Clone the repo
git clone https://github.com/ProjectsByFerm/COBAI.git
cd COBAI

2. Set up environment
cd app
cp .env.example .env

Fill in your API key inside .env.

3. Install dependencies
pip install -r requirements.txt
- running the System

Run a study session:

python app/study_runner.py
- Example Learning Flow
Load a COBOL task (JSON module)
AI coach provides guidance
User submits solution
System evaluates correctness
Results are stored for analysis
📊 Analysis

To summarize results:

python analysis/summarize_results.py

PURPOSE

This project is designed to:

Explore AI-assisted learning effectiveness
Provide structured programming education
Enable research experiments with measurable outcomes
- Environment Variables

MIT License
