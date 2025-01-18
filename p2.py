import ollama
import time
import os
import json
import numpy as np
from numpy.linalg import norm
import tkinter as tk
from tkinter import scrolledtext, messagebox


# Function to parse a file and return paragraphs
def parse_file(filename):
    with open(filename, encoding="utf-8-sig") as f:
        paragraphs = []
        buffer = []
        for line in f.readlines():
            line = line.strip()
            if line:
                buffer.append(line)
            elif len(buffer):
                paragraphs.append((" ").join(buffer))
                buffer = []
        if len(buffer):
            paragraphs.append((" ").join(buffer))
        return paragraphs


# Save embeddings to a JSON file
def save_embeddings(filename, embeddings):
    if not os.path.exists("embeddings"):
        os.makedirs("embeddings")
    with open(f"embeddings/{filename}.json", "w") as f:
        json.dump(embeddings, f)


# Load embeddings from a JSON file
def load_embeddings(filename):
    if not os.path.exists(f"embeddings/{filename}.json"):
        return False
    with open(f"embeddings/{filename}.json", "r") as f:
        return json.load(f)


# Get embeddings for the text chunks
def get_embeddings(filename, modelname, chunks):
    if (embeddings := load_embeddings(filename)) is not False:
        return embeddings
    embeddings = [
        ollama.embeddings(model=modelname, prompt=chunk)["embedding"]
        for chunk in chunks
    ]
    save_embeddings(filename, embeddings)
    return embeddings


# Find the most similar chunks using cosine similarity
def find_most_similar(needle, haystack):
    needle_norm = norm(needle)
    similarity_scores = [
        np.dot(needle, item) / (needle_norm * norm(item)) for item in haystack
    ]
    return sorted(zip(similarity_scores, range(len(haystack))), reverse=True)


# Define the main logic for the GUI
class RAGApp:
    def __init__(self, root, story_file):
        self.root = root
        self.root.title("RAG LLM Assistant")

        # Load the story file and embeddings
        self.filename = story_file
        self.paragraphs = parse_file(story_file)
        self.embeddings = get_embeddings(story_file, "nomic-embed-text", self.paragraphs)

        # System prompt for the assistant
        self.SYSTEM_PROMPT = """You are a helpful reading assistant who answers questions 
        based on snippets of text provided in context. Answer only using the context provided, 
        being as concise as possible. If you're unsure, just say that you don't know.
        Context:
        """

        # Input field for the user
        self.label = tk.Label(root, text="Ask your question:")
        self.label.pack(pady=5)

        self.question_input = tk.Entry(root, width=50)
        self.question_input.pack(pady=5)

        # Button to submit the question
        self.submit_button = tk.Button(root, text="Submit", command=self.handle_question)
        self.submit_button.pack(pady=5)

        # ScrolledText widget to display responses
        self.output_area = scrolledtext.ScrolledText(root, width=60, height=20, wrap=tk.WORD)
        self.output_area.pack(pady=10)

        # Quit button
        self.quit_button = tk.Button(root, text="Quit", command=root.quit)
        self.quit_button.pack(pady=5)

    def handle_question(self):
        prompt = self.question_input.get().strip()
        if not prompt:
            messagebox.showerror("Input Error", "Please enter a question.")
            return

        # Generate the embedding for the question
        prompt_embedding = ollama.embeddings(model="nomic-embed-text", prompt=prompt)["embedding"]

        # Find the most similar chunks
        most_similar_chunks = find_most_similar(prompt_embedding, self.embeddings)[:5]
        context = "\n".join(self.paragraphs[item[1]] for item in most_similar_chunks)

        # Get the response from the LLM
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT + context},
                {"role": "user", "content": prompt},
            ],
        )

        # Display the response in the output area
        self.output_area.insert(tk.END, f"Q: {prompt}\nA: {response['message']['content']}\n\n")
        self.output_area.see(tk.END)
        self.question_input.delete(0, tk.END)


# Main function to run the GUI
def main():
    story_file = "story.txt"
    if not os.path.exists(story_file):
        print(f"Error: The file '{story_file}' does not exist.")
        return

    root = tk.Tk()
    app = RAGApp(root, story_file)
    root.mainloop()


if __name__ == "__main__":
    main()
