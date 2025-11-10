COMMANDS = ["LS", "GET", "PUT"]

def parse(message):
    message = message.strip()
    if not message:
        return None, None

    parts = message.split(maxsplit=1)
    command = parts[0].upper()

    filename = parts[1] if len(parts) > 1 else None
    return command, filename


def validate(command):
    response_code = "200"
    response = "OK"
    
    if command not in COMMANDS:
        response = f"Invalid Command, command: \"{command}\" unknown. "
        response_code = "400"

    return response_code, response

