# RateGuard

**RateGuard** is a lightweight Python library for enforcing a maximum rate of function calls (e.g., requests per minute) in a thread-safe manner. Its primary feature is a simple decorator, `@rate_limit(rpm=...)`, that you can apply to any function to ensure the function doesn’t exceed a specified rate limit—especially useful when making concurrent API calls.

## Table of Contents

- [Why RateGuard?](#why-rateguard)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Concurrency and Thread Safety](#concurrency-and-thread-safety)
- [Example: Rate Limiting Concurrent API Calls](#example-rate-limiting-concurrent-api-calls)
- [License](#license)

---

## Why RateGuard?

When dealing with external APIs, it’s common to run into rate-limit restrictions. Exceeding these limits can result in errors or even temporary bans. **RateGuard** helps ensure you stay below these thresholds by automatically waiting the required time before sending the next request. Its decorator-based design keeps your code clean and easy to maintain.

---

## How It Works

1. **Decorator**: `rate_limit(rpm=...)` wraps your function.
2. **Lock and Timestamp**:
   - Uses a thread lock (`threading.Lock()`) to synchronize access across concurrent threads.
   - Tracks the time of the last call in a shared variable.
3. **Enforcement**:
   - Calculates the required interval between calls (`60.0 / rpm`).
   - If a call arrives before the interval has elapsed, it sleeps just long enough to maintain the correct overall rate.
4. **Thread-Safe**:
   - The lock ensures only one thread checks or updates call timing at a time, preventing race conditions.

---

## Installation

```bash
pip install rateguard
```

> Or install directly from source (if you have the `.whl` or source package):
> ```bash
> pip install dist/rateguard-0.1.0-py3-none-any.whl
> ```

---

## Basic Usage

```python
from rateguard import rate_limit

@rate_limit(rpm=10)  # Limit: 10 calls per minute
def my_function():
    print("Function called!")

for _ in range(20):
    my_function()
```

In the snippet above:
- **`rpm=10`** enforces a 6-second interval (`60 / 10`) between each call.
- The decorator will automatically sleep when necessary to avoid exceeding 10 calls per minute.

---

## Concurrency and Thread Safety

A key advantage of **RateGuard** is that it can be used safely in multi-threaded scenarios. Even if multiple threads call the decorated function at the same time, they will be throttled to ensure the combined rate doesn’t exceed the specified limit.

- **`threading.Lock()`** is used to ensure updates to the shared timestamp happen sequentially.
- Only one thread can update and check the last-call time at a time, preventing race conditions.

Thus, **RateGuard** is especially helpful when you have a pool of threads each making HTTP requests or other rate-sensitive operations.

---

## Example: Rate Limiting Concurrent API Calls

Below is an example that processes 30 questions using Google's Gemini API concurrently. **RateGuard** ensures the model is only called up to 15 times per minute, even with 10 threads running in parallel:

```python
import os
import time
import json
import concurrent.futures
import threading

from dotenv import load_dotenv
from dataclasses import dataclass
from tqdm import tqdm

from google import genai
from rateguard import rate_limit

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

available_models: dict[str, str] = {
    "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",
    "gemini-2.5-pro-exp-03-25": "gemini-2.5-pro-exp-03-25",
    "gemini-2.0-flash": "gemini-2.0-flash",
}

@dataclass(frozen=True)
class Config:
    MODEL_NAME: str = available_models.get("gemini-2.0-flash")
    MODEL_RPM: int = 15

def build_prompt(row: dict) -> str:
    question = row.get("Question", "No question provided.")
    return f"Please generate related questions for: {question}"

@rate_limit(rpm=Config.MODEL_RPM)
def rate_limited_api_call(prompt: str):
    return client.models.generate_content(model=Config.MODEL_NAME, contents=prompt)

def process_row(row: dict):
    question_id = row.get("Question Id")
    question_text = row.get("Question")
    prompt = build_prompt(row)
    response = rate_limited_api_call(prompt)
    return question_id, {
        "main_question": question_text,
        "generated_questions": response.text,
    }

def main():
    records = [
        {"Question Id": f"Q{i+1}", "Question": q} for i, q in enumerate([
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What is deep learning?",
            "Explain neural networks.",
            "What is computer vision?",
            "How do recommendation systems work?",
            "What is natural language processing?",
            "Define reinforcement learning.",
            "What are generative models?",
            "Explain supervised learning.",
            "What is unsupervised learning?",
            "How does clustering work?",
        ])
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            tqdm(
                executor.map(process_row, records),
                total=len(records),
                desc="Processing rows",
            )
        )

    responses_dict = dict(results)
    OUTPUT_FILE: str = (
        f"generated_response_{'_'.join(Config.MODEL_NAME.split('.'))}.json"
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as json_file:
        json.dump(responses_dict, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
```

---

## License

MIT License

---

## Contributing

Contributions are welcome! To contribute to RateGuard:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Write clear, testable code and include relevant tests.
4. Ensure the code passes existing tests.
5. Submit a pull request with a clear description of your changes.

Please open an issue first if you'd like to discuss major changes or ideas. We appreciate your interest and help in making **RateGuard** better!
