import csv
from datetime import datetime
from io import StringIO
import os
from typing import List, Union

from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage
from google.cloud.sql.connector import Connector
import sqlalchemy

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
        print(
            "Google Cloud Authentication credentials not found, writing logs locally."
        )
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
    Adds an entry to the 'matches' table in Cloud SQL MySQL and updates the 'teams' table.

    Args:
        player1_bankroll (int): The final bankroll of player 1.
        player2_bankroll (int): The final bankroll of player 2.
    """
    instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]

    with Connector() as connector:

        def getconn() -> sqlalchemy.engine.base.Connection:
            conn = connector.connect(
                instance_connection_name,
                "pymysql",
                user=db_user,
                password=db_pass,
                db=db_name,
            )
            return conn

        pool = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=getconn,
        )

        try:
            with pool.connect() as db_conn:
                # Check if player names exist in the 'teams' table
                query_teams = sqlalchemy.text("""
                    SELECT githubUsername
                    FROM teams
                    WHERE githubUsername IN (:player1, :player2)
                """)
                result = db_conn.execute(
                    query_teams, player1=PLAYER_1_NAME, player2=PLAYER_2_NAME
                )
                teams = set(row[0] for row in result)

                if PLAYER_1_NAME not in teams or PLAYER_2_NAME not in teams:
                    print(
                        "One or both player names do not exist in the 'teams' table. Skipping entry."
                    )
                    return

                # Insert the match entry into the 'matches' table
                insert_query = sqlalchemy.text("""
                    INSERT INTO matches (matchId, team1Id, team2Id, timestamp, team1Bankroll, team2Bankroll)
                    VALUES (:match_id, :team1, :team2, :timestamp, :bankroll1, :bankroll2)
                """)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_conn.execute(
                    insert_query,
                    match_id=MATCH_ID,
                    team1=PLAYER_1_NAME,
                    team2=PLAYER_2_NAME,
                    timestamp=timestamp,
                    bankroll1=player1_bankroll,
                    bankroll2=player2_bankroll,
                )

                # Update the 'teams' table with win/loss counts
                if player1_bankroll > player2_bankroll:
                    update_query = sqlalchemy.text("""
                        UPDATE teams
                        SET wins = wins + 1
                        WHERE githubUsername = :winner;

                        UPDATE teams
                        SET losses = losses + 1
                        WHERE githubUsername = :loser;
                    """)
                    db_conn.execute(
                        update_query, winner=PLAYER_1_NAME, loser=PLAYER_2_NAME
                    )
                elif player2_bankroll > player1_bankroll:
                    update_query = sqlalchemy.text("""
                        UPDATE teams
                        SET wins = wins + 1
                        WHERE githubUsername = :winner;

                        UPDATE teams
                        SET losses = losses + 1
                        WHERE githubUsername = :loser;
                    """)
                    db_conn.execute(
                        update_query, winner=PLAYER_2_NAME, loser=PLAYER_1_NAME
                    )

                db_conn.commit()
                print("Match entry added and teams table updated successfully.")

        except Exception as e:
            print(f"Error while interacting with the database: {str(e)}")
            db_conn.rollback()
