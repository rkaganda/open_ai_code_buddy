import subprocess
import logging

logger = logging.getLogger(__name__)

def execute_command(input_text, shell_type):
    print(f"shell_type={shell_type}")
    cmd_str = ''
    if shell_type == "bash":
        cmd_str = "-c"
    elif shell_type == "powershell":
        cmd_str = "-Command"
    elif shell_type == "cmd":
        cmd_str = "/c"
    else:
        raise ValueError(f"Unsupported shell type: {shell_type}")
    logging.debug(f"Executing: {shell_type} {cmd_str} {input_text}")
    print(input_text)
    try:
        process = subprocess.run(
            [shell_type, cmd_str, input_text.strip()],  
            stdin=subprocess.PIPE,  # input
            stdout=subprocess.PIPE, # output
            stderr=subprocess.PIPE, # errors
            text=True,          
        )
        logging.debug("Command STDOUT: %s", process.stdout)
        logging.error("Command STDERR: %s", process.stderr)
        print(process.stdout)
        print(process.stderr)
    except Exception as e:
        raise e

    return process.stdout, process.stderr

