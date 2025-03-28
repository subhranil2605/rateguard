import os
import time
import json
import concurrent.futures
import threading

from dotenv import load_dotenv
from dataclasses import dataclass
from tqdm import tqdm

from google import genai

# Import rate_limit from rateguard
from rateguard import rate_limit

# Load environment variables from .env file
load_dotenv()

# Access environment variables
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

# Configure the API key
client = genai.Client(api_key=GEMINI_API_KEY)

# Dictionary of all the available models
available_models: dict[str, str] = {
    "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",
    "gemini-2.5-pro-exp-03-25": "gemini-2.5-pro-exp-03-25",
    "gemini-2.0-flash": "gemini-2.0-flash",
}


# Constant configuration
@dataclass(frozen=True)
class Config:
    MODEL_NAME: str = available_models.get("gemini-2.0-flash")
    MODEL_RPM: int = 15


def build_prompt(row: dict) -> str:
    # Construct a prompt using the question text from the row
    question = row.get("Question", "No question provided.")
    return f"Please generate related questions for: {question}"


@rate_limit(rpm=Config.MODEL_RPM)
def rate_limited_api_call(prompt: str):
    # Call the API to generate content based on the prompt
    return client.models.generate_content(model=Config.MODEL_NAME, contents=prompt)


def process_row(row: dict):
    """
    Process a single row: build a prompt, call the API (with rate limiting),
    and return a tuple with the question id and the result dictionary.
    """
    question_id = row.get("Question Id")
    question_text = row.get("Question")
    prompt = build_prompt(row)

    # Call the API to generate content for the current row
    response = rate_limited_api_call(prompt)

    # Return a tuple of the question_id and a dictionary with the needed data
    return question_id, {
        "main_question": question_text,
        "generated_questions": response.text,
    }


def main():
    # Define a list of 30 sample rows (each row is a dictionary)
    records = [
        {"Question Id": "Q1", "Question": "What is artificial intelligence?"},
        {"Question Id": "Q2", "Question": "How does machine learning work?"},
        {"Question Id": "Q3", "Question": "What is deep learning?"},
        {"Question Id": "Q4", "Question": "Explain neural networks."},
        {"Question Id": "Q5", "Question": "What is computer vision?"},
        {"Question Id": "Q6", "Question": "How do recommendation systems work?"},
        {"Question Id": "Q7", "Question": "What is natural language processing?"},
        {"Question Id": "Q8", "Question": "Define reinforcement learning."},
        {"Question Id": "Q9", "Question": "What are generative models?"},
        {"Question Id": "Q10", "Question": "Explain supervised learning."},
        {"Question Id": "Q11", "Question": "What is unsupervised learning?"},
        {"Question Id": "Q12", "Question": "How does clustering work?"},
        {"Question Id": "Q13", "Question": "What is regression analysis?"},
        {"Question Id": "Q14", "Question": "Explain classification techniques."},
        {"Question Id": "Q15", "Question": "What is data preprocessing?"},
        {"Question Id": "Q16", "Question": "How do decision trees work?"},
        {"Question Id": "Q17", "Question": "Explain random forests."},
        {"Question Id": "Q18", "Question": "What is support vector machine?"},
        {"Question Id": "Q19", "Question": "What is ensemble learning?"},
        {"Question Id": "Q20", "Question": "Describe feature engineering."},
        {"Question Id": "Q21", "Question": "What is hyperparameter tuning?"},
        {"Question Id": "Q22", "Question": "How does cross-validation work?"},
        {"Question Id": "Q23", "Question": "Explain gradient descent."},
        {"Question Id": "Q24", "Question": "What are activation functions?"},
        {"Question Id": "Q25", "Question": "Describe overfitting in models."},
        {"Question Id": "Q26", "Question": "What is regularization?"},
        {"Question Id": "Q27", "Question": "Explain convolutional neural networks."},
        {"Question Id": "Q28", "Question": "What is recurrent neural network?"},
        {"Question Id": "Q29", "Question": "Define transfer learning."},
        {"Question Id": "Q30", "Question": "What is model deployment?"},
    ]

    # Use ThreadPoolExecutor to process rows concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            tqdm(
                executor.map(process_row, records),
                total=len(records),
                desc="Processing rows",
            )
        )

    # Convert list of tuples to a dictionary (assuming process_row returns (question_id, result_dict))
    responses_dict = dict(results)

    # Create a unique output filename based on the model name
    OUTPUT_FILE: str = (
        f"generated_response_{'_'.join(Config.MODEL_NAME.split('.'))}.json"
    )

    # Save the dictionary of responses to a JSON file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as json_file:
        json.dump(responses_dict, json_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
