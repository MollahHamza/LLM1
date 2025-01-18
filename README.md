

# Project Setup Guide

This guide will walk you through setting up the necessary environment for running the project.

## Prerequisites

- Python 3.6 or higher is required.
- Ensure that you have `pip` installed to manage dependencies.

## Setup Steps

### 1. Create a Virtual Environment

To keep your environment isolated, create a Python virtual environment:

```bash
python -m venv myenv
```

### 2. Activate the Virtual Environment

After creating the virtual environment, activate it:

- On **Windows**:

```bash
myenv\Scripts\activate.bat
```

- On **Linux/macOS**:

```bash
source myenv/bin/activate
```

This will activate the virtual environment, and you should see `(myenv)` in your terminal prompt.

### 3. Install Required Packages

Once the environment is activated, install the required Python packages:

```bash
pip install ollama numpy
```

This will install:

- **Ollama** (likely for working with language models).
- **Numpy** (for numerical computing).

### 4. Download Models

To run the project successfully, you will need to download specific models:

- **llama3.2:1b**
- **nomic-embed-text**

Make sure you have the correct URLs or instructions to download these models, as they might be hosted on specific repositories or cloud platforms.

### 5. Running the Project

Once everything is set up, you can start using the environment and models in your project. Make sure to run your scripts with the virtual environment active.

---

### Troubleshooting

- If you encounter any errors during installation, ensure that you have an active internet connection and the correct versions of dependencies.
- If models fail to load, verify that you’ve downloaded them correctly and placed them in the correct directories.
