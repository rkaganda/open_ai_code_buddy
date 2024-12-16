import requests
import os
import terminal_log
import logging
import re
import time
import yaml
import json


logger = logging.getLogger(__name__)

def get_open_ai_response(next_prompt, prev_message_chain, system_prompt, attempt_count, config):
    if attempt_count > config['response_attempt_limit']:
        raise Exception(f"Response attempt limit reached for OpenAI response. {attempt_count}>{config['response_attempt_limit']}")

    # request url and headers
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}"
    }
    # system payload
    system_payload = [
        {
            "role":"system", 
            "content": [
                {   
                    "type": "text",
                    "text":f"{system_prompt}"
                }]
        }]

    # create payload with prompt
    new_content = [{"type":"text", "text":f"{next_prompt}"}]
    new_payload = [{
        "role": "user",
        "content": new_content
    }]

    # concatonate prompt with message chain 
    messages = system_payload + prev_message_chain + new_payload

    logger.info(f"new_payload={messages}")

    # create request
    payload = {
        "model": config['chat_model'],
        "messages": messages,
        "temperature": 0
    }

    for _ in range(config['response_attempt_limit']):
        # send the request
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:  # ok response
            response_text = response.json()['choices'][0]['message']['content'] # extract the response

            # format prompt and response to add to chain
            response_chain = [
                {"role": "user", "content": next_prompt},
                {"role": "assistant", "content": response_text}
            ]
            return response_chain, response.json()['choices'][0]['message']['content']
        elif response.status_code == 429:  # rate limit
            logger.info(f"Request failed with status code {response.status_code}: {response.text}")
            error_data = response.json()
            match = re.search(r"Please try again in (\d+)ms", error_data.get("message", ""))
            sleep_time = int(match.group(1)) / 1000 if match else .5
            print(f"rate limit... sleeping for {sleep_time}")  
            time.sleep(sleep_time)
            continue # retry
        else:
            logger.error(f"Request failed with status code {response.status_code}: {response.text}")
            print(f"Request failed with status code {response.status_code}: {response.text}")
            continue # retry


def extract_command(response_text, config):
    command_prompt_tags = config['command_tags']
    command_start_idx = -1
    command_prompt_tag = ''
    for tag in command_prompt_tags:
        command_start_idx = response_text.find(f"```{tag}\n")
        if command_start_idx != -1:
            command_prompt_tag = tag
            break
    if command_start_idx == -1:
        logger.error(f"No command_prompt_tag in response_text={response_text}")
        return False
    response_text = response_text[command_start_idx+len(f"```{tag}\n"):]
    response_text = response_text[:response_text.find('```')].strip()
    return response_text, command_prompt_tag

def load_config():
    config = {}
    API_KEY = os.getenv("OPEN_API_KEY")
    CHAT_MODEL = os.getenv("OPEN_API_MODEL")

    if not API_KEY:
        raise ValueError("API key is not set. Please configure the OPEN_API_KEY environment variable.")
    if not CHAT_MODEL:
        raise ValueError("Chat model is not set. Please configure the OPEN_API_MODEL environment variable.")
    
    config['api_key'] = API_KEY
    config['chat_model'] = CHAT_MODEL

    with open('agent_config.yaml', "r") as file:
        try: 
            data = yaml.safe_load(file)
            config['system_prompt'] = data['system_prompt']
            config['goals'] = data['goals']
            config['max_queries'] = data['max_queries']
            config['response_attempt_limit'] = data['response_attempt_limit']
            # first goal 
            config['system_prompt']['goal'] = config['goals'][0]
            if 'VALID_CODE' in config['system_prompt']:
                config['command_tags'] = [tag for tag in config['system_prompt']['VALID_CODE']]
            else:
                raise Exception("No VALID_CODE tags found in agent_config.yaml system_prompt.")

            config['system_prompt_str'] = json.dumps(config['system_prompt'])
        except Exception as e:
            logger.error(e)
            raise e
    return config
    
def main(config):
    logging.basicConfig(filename='open_ai_prompt.log', level=logging.DEBUG)

    prev_messages_chain = []
    
    current_prompt = ""
    for _ in range(config['max_queries']):
        logger.info(f"current_prompt={current_prompt}")
        response_chain, response_text = get_open_ai_response(
            current_prompt, 
            prev_messages_chain, 
            system_prompt=config['system_prompt_str'],
            attempt_count=0,
            config=config
        )
        prev_messages_chain = prev_messages_chain+response_chain
        if response_text.find('!TASK_DONE!') != -1:
            print("task done")
            break; 
        terminal_command, shell_type = extract_command(response_text, config)
        if not terminal_command:
            current_prompt = "No valid terminal command was found."
            logger.info(f"No valid terminal command was found. stdout={response_text}")
            continue
        else:
            logger.info(f"executing={terminal_command}")
            stdout, stderror = terminal_log.execute_command(terminal_command, shell_type)
            current_prompt = f"<executed_command>{terminal_command}</executed_command>\n<stdout>{stdout}</stdout>\n<stderror>{stderror}</stderror>"
            logger.info(f"stdout={stdout}")
            logger.info(f"stderror={stderror}")


if __name__=="__main__":
    config = load_config()
    try:
        main(config)
    except Exception as e:
        logger.critical(f"Exception: {e}", exc_info=True)
        print("An error occurred. Check the log.")
    