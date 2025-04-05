import json
import os

def load_templates():
    try:
        with open("templates.json", "r") as f:
            templates = json.load(f)
    except FileNotFoundError:
        templates = {
            "Mid Exam": {
                "question_types": {
                    "MCQ": True,
                    "Descriptive": True
                },
                "num_mcq": 5,
                "num_3_marks": 6,
                "num_5_marks": 5,
                "total_marks": 50,
                "selected_option": "Easy",
                "include_answers": True
            },
            "Final Exam": {
                "question_types": {
                    "MCQ": True,
                    "Descriptive": True
                },
                "num_mcq": 10,
                "num_3_marks": 12,
                "num_5_marks": 10,
                "total_marks": 100,
                "selected_option": "Hard",
                "include_answers": True
            }
        }
        save_templates(templates)
    return templates

def save_templates(templates):
    with open("templates.json", "w") as f:
        json.dump(templates, f, indent=4)

def add_template(name, config):
    templates = load_templates()
    templates[name] = config
    save_templates(templates)
    return templates

def delete_template(name):
    templates = load_templates()
    if name in templates:
        del templates[name]
        save_templates(templates)
    return templates 