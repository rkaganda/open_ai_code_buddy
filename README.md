# openai code buddy

- **Give the chat model a goal**
- **Execute the response in a terminal**
- **Pipe the terminal responses back to the chat model**
- **repeat**

What could possible go wrong 😄

## Prerequisites
- Python 3.11+
- pip 
- OpenAI API subscription

## Setup and Run

- ```clone https://github.com/rkaganda/open_ai_code_buddy.git``` 
- ```pip install -r requirements.txt```
- **Create a .env or set env params for**
    - ```OPEN_API_KEY``` - the key used for the chat requests
    - ```OPEN_API_MODEL``` - the chat model used for the requests
- **Setup agent_config.yaml**
    - ```system_prompt``` - all the information to be included in the system prompt
        - ```shell``` - ```powershell```,```cmd``` ,```bash```
    - ```goals``` - what you want the agent to do (only one goal supported atm)
    - ```max_queries``` - max number of prompts to achive goal
    - ```response_attempt_limit``` - max openai requests per prompt
- **Run the agent**
    - ```python main.py```

