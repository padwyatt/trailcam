from datetime import datetime, timedelta

def log_message(message):
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open('log.txt', 'a') as file:
        file.write(log_entry)

def purge_old_lines():
    
    cutoff_date = datetime.now() - timedelta(days=30)

    with open('log.txt', 'r') as file:
        lines = file.readlines()

    filtered_lines = [
        line for line in lines
        if datetime.strptime(line[1:20], "%Y-%m-%d %H:%M:%S") >= cutoff_date
    ]

    with open('log.txt', 'w') as file:
        file.writelines(filtered_lines)
