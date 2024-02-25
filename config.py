import os

# PARAMETERS TO CONTROL THE BEHAVIOR OF THE GAME ENGINE

# Player names
PLAYER_1_NAME = os.getenv("PLAYER_1_NAME", "Player1DefaultName")
PLAYER_2_NAME = os.getenv("PLAYER_2_NAME", "Player2DefaultName")

# DNS names for player bots, retrieved from environment variables
PLAYER_1_DNS = os.getenv("PLAYER_1_DNS", "player1-service.default.svc.cluster.local")
PLAYER_2_DNS = os.getenv("PLAYER_2_DNS", "player2-service.default.svc.cluster.local")

# GAME PROGRESS IS RECORDED HERE
GAME_LOG_FILENAME = "gamelog"

# PLAYER_LOG_SIZE_LIMIT IS IN BYTES
PLAYER_LOG_SIZE_LIMIT = 524288

# STARTING_GAME_CLOCK AND TIMEOUTS ARE IN SECONDS
ENFORCE_GAME_CLOCK = True
STARTING_GAME_CLOCK = 30.0

# THE GAME VARIANT FIXES THE PARAMETERS BELOW
NUM_ROUNDS = 1000
STARTING_STACK = 400
BIG_BLIND = 2
SMALL_BLIND = 1
