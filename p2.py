import os
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
import ollama

class Question:
    def __init__(self, text, options, correct_answer, context):
        self.text = text
        self.options = options
        self.correct_answer = correct_answer
        self.context = context

    def to_dict(self):
        return {
            "text": self.text,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "context": self.context,
        }

    @staticmethod
    def from_dict(data):
        return Question(
            text=data["text"],
            options=data["options"],
            correct_answer=data["correct_answer"],
            context=data["context"],
        )

def parse_file(filename):
    with open(filename, encoding="utf-8-sig") as f:
        paragraphs = []
        buffer = []
        for line in f.readlines():
            line = line.strip()
            if line:
                buffer.append(line)
            elif buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
        if buffer:
            paragraphs.append(" ".join(buffer))
        return paragraphs

def generate_questions(paragraph):
    try:
        response = ollama.chat(
            model="llama3.2-vision",
            messages=[{
                "role": "system",
                "content": """
                Generate 5 different multiple-choice questions based on the following text. 
                Format each question as:
                Q1: [Question]
                A) [Option]
                B) [Option]
                C) [Option]
                D) [Option]
                Correct Answer: [A/B/C/D]

                Q2: [Question]
                ... and so on for all 5 questions.
                
                Each correct answer must be a single letter: A, B, C, or D
                Make sure questions are diverse and test different aspects of the text.
                """
            },
            {"role": "user", "content": paragraph}],
        )

        response_text = response["message"]["content"]
        print("Response Text:", response_text)  # Debugging output

        questions = []
        current_question = {}
        
        lines = response_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Q"):
                if current_question.get("text"):  # Save previous question if exists
                    questions.append(Question(
                        current_question["text"],
                        current_question["options"],
                        current_question["correct_answer"],
                        paragraph
                    ))
                current_question = {"options": []}
                current_question["text"] = line.split(":", 1)[1].strip()
            elif line.startswith(("A)", "B)", "C)", "D)")):
                current_question["options"].append(line)
            elif "Correct Answer:" in line:
                answer_text = line.split("Correct Answer:", 1)[1].strip()
                current_question["correct_answer"] = answer_text[0].upper()

        # Add the last question
        if current_question.get("text"):
            questions.append(Question(
                current_question["text"],
                current_question["options"],
                current_question["correct_answer"],
                paragraph
            ))

        return questions
    except Exception as e:
        print(f"Error generating questions for paragraph: {e}")
        return []

def preprocess_questions(story_file, output_file):
    paragraphs = parse_file(story_file)
    all_questions = []
    for paragraph in paragraphs[:3]:  # Process first 3 paragraphs
        questions = generate_questions(paragraph)
        all_questions.extend([q.to_dict() for q in questions])
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=4)
    print(f"Preprocessed questions saved to {output_file}")

def load_questions(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Question.from_dict(q) for q in data]

class QuizApp:
    def __init__(self, root, questions):
        self.root = root
        self.questions = questions
        self.current_question = 0
        self.score = 0
        
        self.setup_ui()
        self.display_question()

    def setup_ui(self):
        self.root.title("Quiz App")
        
        # Progress display
        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(pady=5)

        # Question display
        self.question_label = tk.Label(self.root, wraplength=500, justify=tk.LEFT)
        self.question_label.pack(pady=10)

        # Options display
        self.options_var = tk.StringVar(value="")
        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack(pady=5)

        self.option_buttons = []
        for i in range(4):
            btn = tk.Radiobutton(
                self.options_frame,
                variable=self.options_var,
                value=str(i+1),
                text="",
                wraplength=400,
                anchor="w",
                justify=tk.LEFT,
            )
            btn.pack(anchor="w")
            self.option_buttons.append(btn)

        # Submit button
        self.submit_button = tk.Button(self.root, text="Submit", command=self.submit_answer)
        self.submit_button.pack(pady=10)

        # Score display
        self.score_label = tk.Label(self.root, text="Score: 0/0")
        self.score_label.pack(pady=5)

        # Feedback display
        self.feedback_label = tk.Label(self.root, wraplength=500, justify=tk.LEFT)
        self.feedback_label.pack(pady=5)

    def display_question(self):
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            
            # Update progress
            self.progress_label.config(text=f"Question {self.current_question + 1} of {len(self.questions)}")
            
            # Display question
            self.question_label.config(text=question.text)
            
            # Clear previous feedback
            self.feedback_label.config(text="")
            
            # Update score display
            self.score_label.config(text=f"Score: {self.score}/{self.current_question}")
            
            # Display options
            for i, option in enumerate(question.options):
                self.option_buttons[i].config(text=option)
            self.options_var.set("")  # Clear previous selection
        else:
            self.end_quiz()

    def submit_answer(self):
        selected_answer = self.options_var.get()
        if not selected_answer:
            messagebox.showerror("Error", "Please select an answer.")
            return

        current_question = self.questions[self.current_question]
        correct_answer = current_question.correct_answer
        
        # Convert answers to integers for comparison
        is_correct = int(selected_answer) == (ord(correct_answer) - ord('A') + 1)
        
        if is_correct:
            self.score += 1
            feedback = "Correct! ✓"
        else:
            feedback = f"Incorrect. The correct answer was {correct_answer}."
        
        self.feedback_label.config(text=feedback)
        self.score_label.config(text=f"Score: {self.score}/{self.current_question + 1}")
        
        # Wait a short moment before moving to next question
        self.root.after(1500, self.next_question)

    def next_question(self):
        self.current_question += 1
        self.display_question()

    def end_quiz(self):
        # Clear the options and submit button
        self.options_frame.pack_forget()
        self.submit_button.pack_forget()
        self.feedback_label.pack_forget()
        self.progress_label.pack_forget()
        
        # Calculate percentage
        percentage = (self.score / len(self.questions)) * 100
        
        # Display final score
        final_score = f"Quiz Complete!\nYour final score: {self.score}/{len(self.questions)} ({percentage:.1f}%)"
        self.question_label.config(text=final_score)
        self.score_label.config(text="")

if __name__ == "__main__":
    story_file = "story.txt"
    output_file = "questions.json"

    # Delete existing question file and generate new questions
    if os.path.exists(output_file):
        os.remove(output_file)

    preprocess_questions(story_file, output_file)

    # Load preprocessed questions
    questions = load_questions(output_file)

    # Start the quiz
    root = tk.Tk()
    app = QuizApp(root, questions)
    root.mainloop()
