import streamlit as st
import ast
from PIL import Image, ImageDraw, ImageFont


def renew_action_num():
    st.session_state.action_num = 0


def use_default_logs():
    st.session_state.use_default_logs = True
    with open("logs/engine_log.txt", "r") as log_file:
        # Split the logs by empty lines
        log = log_file.read().split("\n\n")
    st.session_state.uploaded_log = log


def use_uploaded_logs():
    st.session_state.use_default_logs = False
    


def card_name_to_full_name(card_name):
    number = card_name[0]
    suit = card_name[1]
    suit_to_word = dict(h="hearts", d="diamonds", s="spades", c="clubs")
    return f"{number}_of_{suit_to_word[suit]}"
    

def update_table_image(player1_cards, player2_cards, player1_bet, player2_bet, community_cards, round_result, log, round_num):
    """
    Update the poker table image with the given player cards.
    """
    table_img = Image.open("images/poker_table.png")
    button = Image.open("images/button.png")
    player1_cards = [Image.open(card) for card in player1_cards]
    player2_cards = [Image.open(card) for card in player2_cards]
    community_cards = [Image.open(card) for card in community_cards]

    # Resize the images while maintaining the aspect ratio
    for i in range(len(player1_cards)):
        player1_cards[i].thumbnail((250, 250))
        player2_cards[i].thumbnail((250, 250))
    for i in range(len(community_cards)):
        community_cards[i].thumbnail((250, 250))
    card_width, card_height = player1_cards[0].size

    # Add bet as text 
    player1_bet_text = f"Bet: {player1_bet}"
    player2_bet_text = f"Bet: {player2_bet}"
    font_size = 70
    font = ImageFont.truetype("images/CinzelDecorative-Bold.ttf", font_size)
    draw = ImageDraw.Draw(table_img)
    draw.text((table_img.width // 2 + card_width // 2 + 300, table_img.height // 2 - font_size + 350), player1_bet_text, fill="gold", font=font)
    draw.text((table_img.width // 2 + card_width // 2 + 300, table_img.height // 2 - font_size - 350), player2_bet_text, fill="gold", font=font)
    
    # Past cards on the table
    for i in range(len(player1_cards)):
        table_img.paste(player1_cards[i], (table_img.width // 2 - card_width // 2 + 300 * i - 150, table_img.height // 2 - card_height // 2 + 400))
        table_img.paste(player2_cards[i], (table_img.width // 2 - card_width // 2 + 300 * i - 150, table_img.height // 2 - card_height // 2 - 400))
    for i in range(len(community_cards)):
        table_img.paste(community_cards[i], (table_img.width // 2 - card_width // 2 + 300 * i - 150, table_img.height // 2 - card_height // 2))
    


    z = (round_num % 2) * 2 - 1
    table_img.paste(button, (table_img.width // 2 - 400, table_img.height // 2 + z * 200 - 50))

    # Add log as text
    log_font_size = 50
    # Make sure to add newlines to the log if it's too long
    if len(log) > 5:
        log = log[:5] + "\n" + log[5:]
    font = ImageFont.truetype("images/Arial.ttf", log_font_size)
    draw.text((table_img.width // 2 - 1000, table_img.height // 2 - log_font_size), log, fill="gold", font=font)
    if round_result is not None:
        draw.rectangle([0, 0, 3000, 2000], fill="black")
        font = ImageFont.truetype("images/CinzelDecorative-Bold.ttf", 100)
        draw.text((table_img.width // 2 - 500, table_img.height // 2 - 100), round_result, fill="gold", font=font)

    return table_img


def get_poker_table(round_log, action_num):
    """
    Get the poker table image for the given round log and action number.
    """
    round_log = round_log.split("\n")
    round_num = int(round_log[0].split("Round #")[1])

    # Get the player names
    player1_name = round_log[4-round_num%2].split("dealt ")[0]

    # Get the cards for the players
    player1_cards = round_log[4-round_num%2].split("dealt ")[1]
    player2_cards = round_log[3+round_num%2].split("dealt ")[1]
    player1_cards = ast.literal_eval(player1_cards)
    player2_cards = ast.literal_eval(player2_cards)
    player1_cards = [f"images/cards/{card_name_to_full_name(card)}.png" for card in player1_cards]
    player2_cards = [f"images/cards/{card_name_to_full_name(card)}.png" for card in player2_cards]

    player1_bet, player2_bet = 2-round_num%2, 1+round_num%2
    community_cards = []
    round_result = None

    if action_num < 5:
        return update_table_image(player1_cards, player2_cards, player1_bet, player2_bet, community_cards, round_result, round_log[action_num], round_num)
    
    prev_round_bet = 0
    for i in range(5, len(round_log)):
        if "Board" in round_log[i]:
            prev_round_bet = int(round_log[i].split("Board: ")[1].split(" Pot:")[1]) / 2
            prev_round_bet = int(prev_round_bet) if prev_round_bet.is_integer() else prev_round_bet
            community_cards = ast.literal_eval(round_log[i].split("Board: ")[1].split(" Pot:")[0])
            community_cards = [f"images/cards/{card_name_to_full_name(card)}.png" for card in community_cards]
        if "calls" in round_log[i]:
            if player1_name in round_log[i]:
                player1_bet = player2_bet
            else:
                player2_bet = player1_bet
        elif "bets" in round_log[i]:
            if player1_name in round_log[i]:
                player1_bet = int(round_log[i].split("bets ")[1]) + prev_round_bet
            else:
                player2_bet = int(round_log[i].split("bets ")[1]) + prev_round_bet            
        elif i == len(round_log)-1 and round_result is None:
            round_result = round_log[i-1] + "\n" + round_log[i]
        if i == action_num:
            return update_table_image(player1_cards, player2_cards, player1_bet, player2_bet, community_cards, round_result, round_log[i], round_num)

    return update_table_image(player1_cards, player2_cards, player1_bet, player2_bet, community_cards, round_result, round_log[i], round_num)

def visualize(logs):
    # Choose a round to display
    #round_num = st.slider("Choose a round", 1, len(logs)-1, 1, on_change=renew_action_num)
    round_num = st.number_input("Choose a round", 1, len(logs)-1, 1, on_change=renew_action_num)

    # Expander for the logs
    with st.expander("Round Logs"):
        st.write(logs[round_num].replace("\n", "<br>"), unsafe_allow_html=True)

    # Action clicker
    if "action_num" not in st.session_state:
        st.session_state["action_num"] = 0
    col1, col2 = st.columns([0.3, 1])
    with col1:
        if st.button("Next action") and st.session_state.action_num < len(logs[round_num].split("\n")) - 1:
            if st.session_state.action_num == 0: st.session_state.action_num = 5
            else: st.session_state.action_num += 1
    with col2:
        if st.button("Previous action") and st.session_state.action_num > 0:
            if st.session_state.action_num == 5: st.session_state.action_num = 0
            else: st.session_state.action_num -= 1
    poker_table_image = get_poker_table(logs[round_num], st.session_state.action_num)
    st.image(poker_table_image, use_column_width=True)



st.title('Poker AI visualizer')

# Initialize session states
if "uploaded_log" not in st.session_state:
    st.session_state.uploaded_log = None
if "use_default_logs" not in st.session_state:
    st.session_state.use_default_logs = False

# Upload logs
st.write("Upload the logs from the game")
uploaded_log = st.file_uploader("Choose a file", type="txt", on_change=use_uploaded_logs)
if uploaded_log is not None and not st.session_state.use_default_logs:
    st.write("File uploaded successfully")
    st.session_state.uploaded_log = uploaded_log.read().decode("utf-8").split("\n\n")

# Use default logs
col1, col2 = st.columns([0.3, 1])
with col1:
    st.button("Use default logs", on_click=use_default_logs)
with col2:
    st.button("Use uploaded logs", on_click=use_uploaded_logs)

# Visualize logs
if st.session_state.use_default_logs:
    st.write("Using default logs")
    visualize(st.session_state.uploaded_log)
elif st.session_state.uploaded_log is not None:
    visualize(st.session_state.uploaded_log)
