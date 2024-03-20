import csv
from datetime import datetime
from io import StringIO
import os
from typing import List, Union

from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from google.cloud import storage

# PARAMETERS TO CONTROL THE BEHAVIOR OF THE GAME ENGINE

# Player names
PLAYER_1_NAME = os.getenv("PLAYER_1_NAME", "all-in-bot")
PLAYER_2_NAME = os.getenv("PLAYER_2_NAME", "prob-bot")

# DNS names for player bots, retrieved from environment variables
PLAYER_1_DNS = os.getenv("PLAYER_1_DNS", "localhost:50051")
PLAYER_2_DNS = os.getenv("PLAYER_2_DNS", "localhost:50052")

# GAME PROGRESS IS RECORDED HERE
MATCH_ID = os.getenv("MATCH_ID", 0)
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


def get_credentials():
    try:
        credentials, _ = default()
        return credentials
    except DefaultCredentialsError:
        print("Google Cloud Authentication credentials not found, writing logs locally.")
        return None


def upload_logs(log: Union[List[str], List[List[str]]], log_filename: str) -> bool:
    """
    Uploads the logs to a Google Cloud Storage bucket.

    Args:
        log (Union[List[str], List[List[str]]]): The list of log messages or CSV rows to upload.
        log_filename (str): The filename to use for the uploaded log file.

    Returns:
        bool: True if the logs were uploaded successfully, False otherwise.
    """
    credentials = get_credentials()
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    if not (credentials and BUCKET_NAME):
        return False

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(BUCKET_NAME)

    log_path = f"match_{MATCH_ID}/{log_filename}"
    blob = bucket.blob(log_path)

    if isinstance(log[0], str):
        log_content = "\n".join(log)
        blob.upload_from_string(log_content)
    else:
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerows(log)
        blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")

    print(f"Logs uploaded to {BUCKET_NAME}/{log_path}")
    return True


def add_match_entry(player1_bankroll: int, player2_bankroll: int) -> None:
    """
    Adds an entry to the 'matches' table in BigQuery.

    Args:
        player1_bankroll (int): The final bankroll of player 1.
        player2_bankroll (int): The final bankroll of player 2.
    """
    credentials = get_credentials()
    DATASET_ID = os.getenv("DATASET_ID")
    if not (credentials and DATASET_ID):
        return

    client = bigquery.Client(credentials=credentials)

    # Check if player names exist in the 'teams' table
    query_teams = f"""
        SELECT teamName
        FROM `{DATASET_ID}.teams`
        WHERE teamName IN ('{PLAYER_1_NAME}', '{PLAYER_2_NAME}')
    """
    query_job = client.query(query_teams)
    teams = set(row["teamName"] for row in query_job.result())

    if PLAYER_1_NAME not in teams or PLAYER_2_NAME not in teams:
        print(
            "One or both player names do not exist in the 'teams' table. Skipping entry."
        )
        return

    # Insert the match entry into the 'matches' table
    row_to_insert = [
        {
            "matchId": MATCH_ID,
            "team1Name": PLAYER_1_NAME,
            "team2Name": PLAYER_2_NAME,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "team1Bankroll": player1_bankroll,
            "team2Bankroll": player2_bankroll,
        }
    ]

    errors = client.insert_rows_json(f"{DATASET_ID}.matches", row_to_insert)
    if errors:
        print(f"Encountered errors while inserting row: {errors}")
    else:
        print("Match entry added successfully.")
