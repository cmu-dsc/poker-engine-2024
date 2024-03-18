import streamlit as st
import ast
from PIL import Image, ImageDraw, ImageFont


def renew_action_num():
    st.session_state.action_num = 0

def use_default_logs():
    st.session_state.using_default_logs = True

def card_name_to_full_name(card_name):
    number = card_name[0]
    if number == "1": number = "ace"
    suit = card_name[1]
    suit_to_word = dict(h="hearts", d="diamonds", s="spades", c="clubs")
    return f"{number}_of_{suit_to_word[suit]}"
    

def update_table_image(player1_card_img, player2_card_img, player1_bet, player2_bet, community_cards, log):
    """
    Update the poker table image with the given player cards.
    """
    table_img = Image.open("images/poker_table.png")
    player1_card_img = Image.open(player1_card_img)
    player2_card_img = Image.open(player2_card_img)
    community_cards = [Image.open(card) for card in community_cards]

    # Resize the images while maintaining the aspect ratio
    player1_card_img.thumbnail((250, 250))
    player2_card_img.thumbnail((250, 250))
    for i in range(len(community_cards)):
        community_cards[i].thumbnail((250, 250))
    card_width, card_height = player1_card_img.size

    # Add bet as text 
    player1_bet_text = f"Bet: {player1_bet}"
    player2_bet_text = f"Bet: {player2_bet}"
    font_size = 70
    font = ImageFont.truetype("images/CinzelDecorative-Bold.ttf", font_size)
    draw = ImageDraw.Draw(table_img)
    draw.text((table_img.width // 2 + card_width // 2 + 100, table_img.height // 2 - font_size + 350), player1_bet_text, fill="gold", font=font)
    draw.text((table_img.width // 2 + card_width // 2 + 100, table_img.height // 2 - font_size - 350), player2_bet_text, fill="gold", font=font)
    
    # Past cards on the table
    table_img.paste(player1_card_img, (table_img.width // 2 - card_width // 2, table_img.height // 2 - card_height // 2 + 400))
    table_img.paste(player2_card_img, (table_img.width // 2 - card_width // 2, table_img.height // 2 - card_height // 2 - 400))
    for i in range(len(community_cards)):
        table_img.paste(community_cards[i], (table_img.width // 2 - card_width // 2 + 300 * i - 150, table_img.height // 2 - card_height // 2))

    # Add log as text
    log_font_size = 50
    # Make sure to add newlines to the log if it's too long
    if len(log) > 5:
        log = log[:5] + "\n" + log[5:]
    font = ImageFont.truetype("images/Arial.ttf", log_font_size)
    draw.text((table_img.width // 2 - 1000, table_img.height // 2 - log_font_size), log, fill="gold", font=font)

    return table_img


def get_poker_table(round_log, action_num):
    """
    Get the poker table image for the given round log and action number.
    """
    round_log = round_log.split("\n")

    # Get the cards for the players
    player1_card = round_log[3].split("dealt ")[1]
    player2_card = round_log[4].split("dealt ")[1]
    player1_card = ast.literal_eval(player1_card)[0]
    player2_card = ast.literal_eval(player2_card)[0]

    player1_card_img = f"images/cards/{card_name_to_full_name(player1_card)}.png"
    player2_card_img = f"images/cards/{card_name_to_full_name(player2_card)}.png"

    # Get blinds 
    blind1 = round_log[1].split(" posts")[0][-1]
    blind2 = round_log[2].split(" posts")[0][-1]

    player1_bet = 1 if blind1 == "1" else 2
    player2_bet = 1 if blind2 == "1" else 2

    community_cards = []

    if action_num == 0:
        return update_table_image(player1_card_img, player2_card_img, player1_bet, player2_bet, community_cards, round_log[4])
    
    for i in range(5, len(round_log)):
        if "Board" in round_log[i]:
            community_cards = ast.literal_eval(round_log[i].split("Board: ")[1].split(" Pot:")[0])
            community_cards = [f"images/cards/{card_name_to_full_name(card)}.png" for card in community_cards]
        if "calls" in round_log[i]:
            if "bot1" in round_log[i]:
                player1_bet = player2_bet
            else:
                player2_bet = player1_bet
        elif "raises" in round_log[i]:
            if "bot1" in round_log[i]:
                player1_bet = int(round_log[i].split("raises to ")[1])
            else:
                player2_bet = int(round_log[i].split("raises to ")[1])
        elif "folds" in round_log[i]:
            break
        if i == 5 + action_num - 1:
            return update_table_image(player1_card_img, player2_card_img, player1_bet, player2_bet, community_cards, round_log[i])
    return update_table_image(player1_card_img, player2_card_img, player1_bet, player2_bet, community_cards, round_log[i])


def visualize(logs):
    # Choose a round to display
    round_num = st.slider("Choose a round", 1, len(logs), 1, on_change=renew_action_num)

    # Expander for the logs
    with st.expander("Round Logs"):
        st.write(logs[round_num].replace("\n", "<br>"), unsafe_allow_html=True)

    # Action clicker
    if "action_num" not in st.session_state:
        st.session_state["action_num"] = 0
    col1, col2 = st.columns([0.3, 1])
    with col1:
        if st.button("Next action") and st.session_state.action_num < len(logs[round_num].split("\n")) - 5:
            st.session_state.action_num += 1
    with col2:
        if st.button("Previous action") and st.session_state.action_num > 0:
            st.session_state.action_num -= 1
    poker_table_image = get_poker_table(logs[round_num], st.session_state.action_num)
    st.image(poker_table_image, use_column_width=True)



st.title('Poker AI visualizer')

if "using_default_logs" not in st.session_state:
    st.session_state.using_default_logs = False

# Upload logs
st.write("Upload the logs from the game")
uploaded_file = st.file_uploader("Choose a file", type="txt")
if uploaded_file is not None:
    st.write("File uploaded successfully")
    st.session_state.using_default_logs = False
    # Split the logs by empty lines
    logs = uploaded_file.read().decode("utf-8").split("\n\n")
    visualize(logs)

# Read logs 
st.button("Or use default logs", on_click=use_default_logs)
if st.session_state.using_default_logs:
    st.write("Using default logs")
    with open("logs/gamelog.txt", "r") as log_file:
        # Split the logs by empty lines
        logs = log_file.read().split("\n\n")
        visualize(logs)


