import os
from typing import List
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage

# PARAMETERS TO CONTROL THE BEHAVIOR OF THE GAME ENGINE

# Player names
PLAYER_1_NAME = os.getenv("PLAYER_1_NAME", "bot1")
PLAYER_2_NAME = os.getenv("PLAYER_2_NAME", "bot2")

# DNS names for player bots, retrieved from environment variables
PLAYER_1_DNS = os.getenv("PLAYER_1_DNS", "localhost:50051")
PLAYER_2_DNS = os.getenv("PLAYER_2_DNS", "localhost:50052")

# GAME PROGRESS IS RECORDED HERE
LOGS_DIRECTORY = "logs"
GAME_LOG_FILENAME = "engine_log"
BOT_LOG_FILENAME = "debug_log"

# PLAYER_LOG_SIZE_LIMIT IS IN BYTES
PLAYER_LOG_SIZE_LIMIT = 524288  # unused?

# STARTING_GAME_CLOCK AND TIMEOUTS ARE IN SECONDS
CONNECT_TIMEOUT = 4
CONNECT_RETRIES = 5
READY_CHECK_TIMEOUT = 0
READY_CHECK_RETRIES = 1
ACTION_REQUEST_TIMEOUT = 2
ACTION_REQUEST_RETRIES = 2
ENFORCE_GAME_CLOCK = True
STARTING_GAME_CLOCK = 300.0

# THE GAME VARIANT FIXES THE PARAMETERS BELOW
NUM_ROUNDS = 1000
STARTING_STACK = 400
BIG_BLIND = 2
SMALL_BLIND = 1

BUCKET_NAME = os.getenv("BUCKET_NAME")


def upload_logs(log: List[str], log_filename: str) -> bool:
    """
    Uploads the logs to a Google Cloud Storage bucket.

    Args:
        log (List[str]): The list of log messages to upload.
        log_filename (str): The filename to use for the uploaded log file.

    Returns:
        bool: True if the logs were uploaded successfully, False otherwise.
    """
    if not BUCKET_NAME:
        return False

    try:
        credentials, _ = default()

        storage_client = storage.Client(credentials=credentials)

        bucket = storage_client.bucket(BUCKET_NAME)

        log_path = f"match_{os.getenv('MATCH_ID', 0)}/{log_filename}"

        blob = bucket.blob(log_path)

        log_content = "\n".join(log)
        blob.upload_from_string(log_content)

        print(f"Logs uploaded to {BUCKET_NAME}/{log_path}")
        return True

    except DefaultCredentialsError:
        print("Authentication credentials not found.")
        print(
            "Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable or authenticate using the gcloud CLI."
        )
        return False
