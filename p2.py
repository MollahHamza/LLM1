import os
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
import ollama

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

class Question:
    def __init__(self, text, options, correct_answer, context, topic):
        self.text = text
        self.options = options
        self.correct_answer = correct_answer
        self.context = context
        self.topic = topic

    def to_dict(self):
        return {
            "text": self.text,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "context": self.context,
            "topic": self.topic
        }

    @staticmethod
    def from_dict(data):
        return Question(
            text=data["text"],
            options=data["options"],
            correct_answer=data["correct_answer"],
            context=data["context"],
            topic=data["topic"]
        )

def generate_questions(paragraph):
    try:
        # First, get the topic
        topic_response = ollama.chat(
            model="llama3.2:1b",
            messages=[{
                "role": "system",
                "content": "Identify the main topic of this text in 2-3 words."
            },
            {"role": "user", "content": paragraph}],
        )
        topic = topic_response["message"]["content"].strip()

        # Then generate questions
        response = ollama.chat(
            model="llama3.2:1b",
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
                Topic: [Topic from the question]

                Q2: [Question]
                ... and so on for all 5 questions.
                
                Each correct answer must be a single letter: A, B, C, D
                Make sure questions are diverse and test different aspects of the text.
                Include a specific topic for each question that represents what knowledge area it tests.
                """
            },
            {"role": "user", "content": paragraph}],
        )

        response_text = response["message"]["content"]
        questions = []
        current_question = {}
        
        lines = response_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Q"):
                if current_question.get("text"):
                    questions.append(Question(
                        current_question["text"],
                        current_question["options"],
                        current_question["correct_answer"],
                        paragraph,
                        current_question.get("topic", topic)
                    ))
                current_question = {"options": []}
                current_question["text"] = line.split(":", 1)[1].strip()
            elif line.startswith(("A)", "B)", "C)", "D)")):
                current_question["options"].append(line)
            elif "Correct Answer:" in line:
                answer_text = line.split("Correct Answer:", 1)[1].strip()
                current_question["correct_answer"] = answer_text[0].upper()
            elif "Topic:" in line:
                current_question["topic"] = line.split("Topic:", 1)[1].strip()

        # Add the last question
        if current_question.get("text"):
            questions.append(Question(
                current_question["text"],
                current_question["options"],
                current_question["correct_answer"],
                paragraph,
                current_question.get("topic", topic)
            ))

        return questions
    except Exception as e:
        print(f"Error generating questions: {e}")
        return []

def generate_questions_from_context(context, previous_topics):
    try:
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[{
                "role": "system",
                "content": f"""
                Generate 5 different multiple-choice questions based on this context, focusing on these topics: {', '.join(previous_topics)}.
                Format each question as:
                Q1: [Question]
                A) [Option]
                B) [Option]
                C) [Option]
                D) [Option]
                Correct Answer: [A/B/C/D]
                Topic: [Topic from the question]

                Make questions more challenging than the first round but ensure they're still based on the context.
                """
            },
            {"role": "user", "content": context}],
        )

        response_text = response["message"]["content"]
        questions = []
        current_question = {}
        
        lines = response_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Q"):
                if current_question.get("text"):
                    questions.append(Question(
                        current_question["text"],
                        current_question["options"],
                        current_question["correct_answer"],
                        context,
                        current_question.get("topic", previous_topics[0])
                    ))
                current_question = {"options": []}
                current_question["text"] = line.split(":", 1)[1].strip()
            elif line.startswith(("A)", "B)", "C)", "D)")):
                current_question["options"].append(line)
            elif "Correct Answer:" in line:
                answer_text = line.split("Correct Answer:", 1)[1].strip()
                current_question["correct_answer"] = answer_text[0].upper()
            elif "Topic:" in line:
                current_question["topic"] = line.split("Topic:", 1)[1].strip()

        # Add the last question
        if current_question.get("text"):
            questions.append(Question(
                current_question["text"],
                current_question["options"],
                current_question["correct_answer"],
                context,
                current_question.get("topic", previous_topics[0])
            ))

        return questions
    except Exception as e:
        print(f"Error generating questions: {e}")
        return []

def generate_lesson(topics):
    try:
        topics_str = ", ".join(topics)
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[{
                "role": "system",
                "content": f"""Create a focused lesson covering these topics: {topics_str}.
                Make it concise but comprehensive enough to help someone understand the key concepts."""
            }]
        )
        return response["message"]["content"]
    except Exception as e:
        print(f"Error generating lesson: {e}")
        return ""

class QuizApp:
    def __init__(self, root, questions):
        self.root = root
        self.first_round_questions = questions[:5]  # First 5 questions for round 1
        self.questions = self.first_round_questions
        self.current_question = 0
        self.score = 0
        self.wrong_questions = []  # Store wrong questions instead of just topics
        self.round = 1
        self.round_scores = []
        
        self.setup_ui()
        self.display_question()

    def setup_ui(self):
        self.root.title("Quiz App")
        
        # Progress display
        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(pady=5)

        # Round display
        self.round_label = tk.Label(self.root, text=f"Round {self.round}")
        self.round_label.pack(pady=5)

        # Question display
        self.question_label = tk.Label(self.root, wraplength=500, justify=tk.LEFT)
        self.question_label.pack(pady=10)

        # Lesson display
        self.lesson_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=10, width=60)
        self.lesson_text.pack(pady=10)
        self.lesson_text.pack_forget()  # Hidden initially

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

        # Continue button for lessons
        self.continue_button = tk.Button(self.root, text="Continue to Next Round", command=self.start_next_round)
        self.continue_button.pack(pady=10)
        self.continue_button.pack_forget()  # Hidden initially

        # Score display
        self.score_label = tk.Label(self.root, text="Score: 0/0")
        self.score_label.pack(pady=5)

        # Feedback display
        self.feedback_label = tk.Label(self.root, wraplength=500, justify=tk.LEFT)
        self.feedback_label.pack(pady=5)

    def display_question(self):
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            
            # Update displays
            self.progress_label.config(text=f"Question {self.current_question + 1} of {len(self.questions)}")
            self.round_label.config(text=f"Round {self.round}")
            self.question_label.config(text=question.text)
            self.feedback_label.config(text="")
            self.score_label.config(text=f"Score: {self.score}/{self.current_question}")
            
            # Display options
            for i, option in enumerate(question.options):
                self.option_buttons[i].config(text=option)
            self.options_var.set("")  # Clear previous selection
            
            # Show quiz elements, hide lesson elements
            self.lesson_text.pack_forget()
            self.continue_button.pack_forget()
            self.options_frame.pack()
            self.submit_button.pack()
        else:
            self.end_round()

    def submit_answer(self):
        if not self.options_var.get():
            messagebox.showerror("Error", "Please select an answer.")
            return

        current_question = self.questions[self.current_question]
        selected_answer = int(self.options_var.get())
        correct_answer = ord(current_question.correct_answer) - ord('A') + 1
        
        if selected_answer == correct_answer:
            self.score += 1
            feedback = "Correct! ✓"
        else:
            feedback = f"Incorrect. The correct answer was {current_question.correct_answer}."
            self.wrong_questions.append(current_question)  # Store the entire question object
        
        self.feedback_label.config(text=feedback)
        self.score_label.config(text=f"Score: {self.score}/{self.current_question + 1}")
        
        self.root.after(1500, self.next_question)

    def next_question(self):
        self.current_question += 1
        self.display_question()

    def end_round(self):
        if len(self.questions) == 0:
            self.end_quiz()
            return
            
        round_score = (self.score / len(self.questions)) * 100
        self.round_scores.append(round_score)
        
        self.options_frame.pack_forget()
        self.submit_button.pack_forget()
        
        if self.wrong_questions and self.round == 1:
            # Generate lesson based on contexts of wrong questions
            contexts = [q.context for q in self.wrong_questions]
            topics = [q.topic for q in self.wrong_questions]
            combined_context = " ".join(contexts)
            
            # Generate and display lesson
            lesson = generate_lesson(topics)
            self.question_label.config(text="Review the following lesson on topics you missed:")
            self.lesson_text.delete(1.0, tk.END)
            self.lesson_text.insert(tk.END, lesson)
            self.lesson_text.pack()
            
            # Generate new questions based on wrong questions' contexts
            new_questions = generate_questions_from_context(combined_context, topics)
            self.questions = new_questions[:5]  # Take up to 5 new questions
            
            self.continue_button.pack()
        else:
            self.end_quiz()

    def start_next_round(self):
        self.round += 1
        self.current_question = 0
        self.score = 0
        
        # Reset UI
        self.lesson_text.pack_forget()
        self.continue_button.pack_forget()
        
        self.display_question()

    def end_quiz(self):
        # Clear UI
        self.options_frame.pack_forget()
        self.submit_button.pack_forget()
        self.feedback_label.pack_forget()
        self.progress_label.pack_forget()
        self.lesson_text.pack_forget()
        self.continue_button.pack_forget()
        
        # Display final scores
        final_text = "Quiz Complete!\n\n"
        for i, score in enumerate(self.round_scores, 1):
            final_text += f"Round {i} Score: {score:.1f}%\n"
        
        if len(self.round_scores) > 1:
            improvement = self.round_scores[-1] - self.round_scores[0]
            final_text += f"\nImprovement: {improvement:+.1f}%"
        
        self.question_label.config(text=final_text)
        self.score_label.config(text="")

if __name__ == "__main__":
    story_file = "story.txt"
    output_file = "questions.json"

    # Generate initial questions
    paragraphs = parse_file(story_file)
    all_questions = []
    
    # Generate at least 5 questions for the first round
    for paragraph in paragraphs[:1]:  # Only need first paragraph initially
        questions = generate_questions(paragraph)
        all_questions.extend([q.to_dict() for q in questions])
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=4)
    
    # Load questions and start quiz
    questions = [Question.from_dict(q) for q in all_questions]
    root = tk.Tk()
    app = QuizApp(root, questions)
    root.mainloop()
