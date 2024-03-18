import os
import boto3

# PARAMETERS TO CONTROL THE BEHAVIOR OF THE GAME ENGINE

# Player names
PLAYER_1_NAME = os.getenv("PLAYER_1_NAME", "Player1")
PLAYER_2_NAME = os.getenv("PLAYER_2_NAME", "Player2")

# DNS names for player bots, retrieved from environment variables
PLAYER_1_DNS = os.getenv("PLAYER_1_DNS", "localhost:50051")
PLAYER_2_DNS = os.getenv("PLAYER_2_DNS", "localhost:50052")

# GAME PROGRESS IS RECORDED HERE
LOGS_DIRECTORY = "logs"
GAME_LOG_FILENAME = "engine_log"

# Check if the logs directory exists, create it if it doesn't
os.makedirs(LOGS_DIRECTORY, exist_ok=True)

# PLAYER_LOG_SIZE_LIMIT IS IN BYTES
PLAYER_LOG_SIZE_LIMIT = 524288

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


def upload_log_to_s3(log_filename):
    """Uploads a log file to S3 if a bucket name is configured."""
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

    if S3_BUCKET_NAME:
        s3 = boto3.client("s3")
        try:
            s3.upload_file(log_filename, S3_BUCKET_NAME, log_filename)
            print(f"Uploaded {log_filename} to S3 bucket {S3_BUCKET_NAME}")
        except boto3.exceptions.S3UploadFailedError as e:
            print(f"Failed to upload {log_filename} to S3: {e}")
    else:
        print("S3_BUCKET_NAME not set. Skipping upload.")
