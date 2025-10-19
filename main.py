from typing import Final
import os
import random
from discord import Intents, Client, Message, DMChannel
from flask import Flask
from threading import Thread

# Load the token from .env file
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up bot permissions (intents)
intents: Intents = Intents.default()
intents.message_content = True  # This allows the bot to read messages
client: Client = Client(intents=intents)

# Track active conversations
conversation_active = {}  # {user_id: True/False}

# Conversation start message
CONVERSATION_START_MSG = "\n*(Type goodbye to end our conversation)*"


# Function to get the bot's response based on what the user typed
def get_response(user_input: str) -> str:
    """
    This function takes what the user typed and returns the appropriate response.
    Add more subjects here as you need them!
    """
    lowered: str = user_input.lower()

    # AP SUBJECTS
    if 'ap art history' in lowered or 'apah' in lowered or 'ap ah' in lowered:
        return """**🎨 AP Art History Resources:**
    • Khan Academy: https://www.khanacademy.org/humanities/ap-art-history
    • Study Sheets: <https://knowt.com/exams/AP/AP-Art-History>
    • Smarthistory (recommended): <https://smarthistory.org/>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap biology' in lowered or 'ap bio' in lowered:
        return """**🧬 AP Biology Resources:**
    • Khan Academy: <https://www.khanacademy.org/science/ap-biology>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Biology>
    • Amoeba Sisters: <https://www.youtube.com/@AmoebaSister>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap precalculus' in lowered or 'ap precalc' in lowered:
        return """**📐 AP Precalculus Resources:**
    • Khan Academy: <https://www.khanacademy.org/math/precalculus>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Precalculus>
    • Organic Chemistry Tutor: <https://www.youtube.com/@TheOrganicChemistryTutor>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap calculus ab' in lowered or 'ap calc ab' in lowered or 'calc ab' in lowered:
        return """**📐 AP Calculus AB Resources:**
    • Khan Academy: <https://www.khanacademy.org/math/ap-calculus-ab>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Calculus-AB>
    • Organic Chemistry Tutor: <https://www.youtube.com/@TheOrganicChemistryTutor>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap calculus bc' in lowered or 'ap calc bc' in lowered or 'calc bc' in lowered:
        return """**📐 AP Calculus BC Resources:**
    • Khan Academy: <https://www.khanacademy.org/math/ap-calculus-bc>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Calculus-BC>
    • Organic Chemistry Tutor: <https://www.youtube.com/@TheOrganicChemistryTutor>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap chemistry' in lowered or 'ap chem' in lowered:
        return """**🧪 AP Chemistry Resources:**
    • Khan Academy: <https://www.khanacademy.org/science/ap-chemistry>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Chemistry>
    • Organic Chemistry Tutor: <https://www.youtube.com/@TheOrganicChemistryTutor>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap chinese' in lowered:
        return """**🇨🇳 AP Chinese Resources:**
    • Study Sheets: <https://knowt.com/exams/AP/AP-Chinese-Language-and-Culture>
    • Grammar: <https://resources.allsetlearning.com/chinese/grammar>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap comparative government' in lowered or 'ap comp gov' in lowered:
        return """**🏛️ AP Comparative Government Resources:**
    • Study Sheets: <https://knowt.com/exams/AP/AP-Comparative-Government-and-Politics>
    • Heimler's History: <https://www.youtube.com/@HeimlerHistory>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap computer science' in lowered or 'ap cs' in lowered or 'apcsa' in lowered or 'apcs' in lowered:
        return """**</> AP Computer Science Resources:**
    • Study Sheets: <https://knowt.com/exams/AP/AP-Computer-Science-Principles>
    • Free Harvard course: https://cs50.harvard.edu/>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap english literature' in lowered or 'ap lit' in lowered or 'ap english lit' in lowered:
        return """**📚 AP English Literature Resources:**
    • Study Sheets: <https://knowt.com/exams/AP/AP-English-Literature-and-Composition>
    • Crash Course: <https://www.youtube.com/crashcourse>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap english language' in lowered or 'ap lang' in lowered or 'ap english lang' in lowered:
        return """**📚 AP English Language Resources:**
    • Khan Academy: <https://www.khanacademy.org/ela>
    • Study Sheets: <https://knowt.com/exams/AP/AP-English-Language-and-Composition>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap environmental science' in lowered or 'apes' in lowered:
        return """**🌱 AP Environmental Science Resources:**
    • Khan Academy: <https://www.khanacademy.org/science/ap-biology>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Environmental-Science>
    • Crash Course: <https://www.youtube.com/crashcourse>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap european history' in lowered or 'ap euro' in lowered:
        return """**🇪🇺 AP European History Resources:**
    • Khan Academy: <https://www.khanacademy.org/humanities/world-history>
    • Study Sheets: <https://knowt.com/exams/AP/AP-European-History>
    • Heimler's History: <https://www.youtube.com/@HeimlerHistory>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap french' in lowered:
        return """**🇫🇷 AP French Resources:**
    • Study Sheets: <https://knowt.com/exams/AP/AP-French-Language-and-Culture>
    • French Articles (Recommended): <https://savoirs.rfi.fr/fr/apprendre-enseigner>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap human geography' in lowered or 'ap hug' in lowered or 'aphug' in lowered:
        return """**🌎 AP Human Geography Resources:**
    • Khan Academy: <https://www.khanacademy.org/>`
    • Study Sheets: <https://knowt.com/exams/AP/AP-Human-Geography>
    • Crash Course Geography: <https://www.youtube.com/crashcourse>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap physics 1' in lowered or 'ap physics one' in lowered:
        return """**🚀 AP Physics 1 Resources:**
    • Khan Academy: <https://www.khanacademy.org/science/ap-physics-1>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Physics-1_Algebra.Based>
    • Free MIT Courses: <https://ocw.mit.edu/>
    • The Organic Chemistry Tutor: <https://www.youtube.com/@TheOrganicChemistryTutor>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap physics c' in lowered or 'ap physics c: mechanics' in lowered or 'ap physics c mechanics' in lowered or 'ap physics c: mech' in lowered or 'ap physics c mech' in lowered:
        return """**🚀 AP Physics C: Mechanics Resources:**
    • Khan Academy: <https://www.khanacademy.org/science/ap-physics-c-mechanics>
    • Free MIT Courses: <https://ocw.mit.edu/>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Physics-C_Mechanics>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap psychology' in lowered or 'ap psych' in lowered:
        return """**🧠 AP Psychology Resources:**
    • Khan Academy: <https://www.khanacademy.org/science/ap-psychology>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Psychology>
    • Crash Course: <https://www.youtube.com/crashcourse>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap spanish language' in lowered or 'ap spanish' in lowered:
        return """**🇪🇸 AP Spanish Language Resources:**
    • Study Sheets: <https://knowt.com/exams/AP/AP-Spanish-Language-and-Culture>
    • SpanishDict: <https://www.spanishdict.com/>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap statistics' in lowered or 'ap stats' in lowered or 'ap stat' in lowered:
        return """**📊 AP Statistics Resources:**
    • Khan Academy: <https://www.khanacademy.org/math/ap-statistics>
    • Study Sheets: <https://knowt.com/exams/AP/AP-Statistics>
    • Crash Course: <https://www.youtube.com/crashcourse>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap studio art' in lowered:
        return """**🎨 AP Studio Art Resources:**
    • Student Art Guide: <https://www.studentartguide.com/>
    • Ctrl+Paint (digital art): <https://www.ctrlpaint.com/>
    • Proko (hand art): <https://www.proko.com/>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap us government' in lowered or 'ap gov' in lowered or 'ap us gov' in lowered:
        return """**🏛️ AP US Government Resources:**
    • Khan Academy: <https://www.khanacademy.org/humanities/us-government>
    • Study Sheets: <https://knowt.com/exams/AP/AP-United-States-Government-and-Politics>
    • Heimler's History: <https://www.youtube.com/@HeimlerHistory>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap us history' in lowered or 'apush' in lowered:
        return """**🇺🇸 AP US History Resources:**
    • Khan Academy: <https://www.khanacademy.org/humanities/us-history>
    • Study Sheets: <https://knowt.com/exams/AP/AP-United-States-History>
    • Heimler's History: <https://www.youtube.com/@HeimlerHistory>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'ap world history' in lowered or 'ap world' in lowered:
        return """**🌍 AP World History Resources:**
    • Khan Academy: <https://www.khanacademy.org/humanities/world-history>
    • Heimler's History: <https://www.youtube.com/@HeimlerHistory>
    • AP Classroom: <https://apstudents.collegeboard.org/>"""

    elif 'sat' in lowered:
        return """**📚 SAT Resources:**
    • CrackSAT: <https://www.cracksat.net/index.html>
    • SAT Question Bank: <https://satsuitequestionbank.collegeboard.org/>
    • Practice Tests: <https://bluebook.collegeboard.org/students/download-bluebook>
    • BHS offers SAT tutoring; ask your counselor!"""

    elif 'act' in lowered:
        return """**📚 ACT Resources:**
    • CrackAB: <https://www.crackab.com/>
    • Practice Tests: <https://www.act.org/content/act/en/products-and-services/the-act/test-preparation.html>"""

    # Help command - shows all available commands
    elif lowered == '!help' or lowered == 'help':
        return """**Here's what I can tutor you in:**

**AP Courses:**
`!ap art history`
`!ap biology`
`!ap precalculus`
`!ap calculus ab`
`!ap calculus bc`
`!ap chemistry`
`!ap chinese`
`!ap comparative government`
`!ap computer science`
`!ap english literature`
`!ap english language`
`!ap environmental science`
`!ap european history`
`!ap french`
`!ap human geography`
`!ap physics 1`
`!ap physics c: mechanics`
`!ap psychology`
`!ap spanish language`
`!ap statistics`
`!ap studio art`
`!ap us government`
`!ap us history`
`!ap world history`

**SAT Prep:**
`!sat`

**ACT Prep:**
`!act`

Type anything above and I'll help you 👆🏻"""

    # If the message starts with "!" but isn't recognized
    elif lowered.startswith('!'):
        return 'I don\'t understand that. Type `!help` to see what I can do!'

    # If it doesn't start with "!", don't respond
    else:
        return None


def get_conversation_response(user_input: str, user_id: int) -> str:
    """
    Simple conversation responses based on keywords
    """
    lowered = user_input.lower()

    # Goodbye - CHECK THIS FIRST before other keywords
    if 'bye' in lowered or 'goodbye' in lowered or 'see you' in lowered or 'later' in lowered or 'gn' in lowered or 'goodnight' in lowered or 'ttyl' in lowered:
        # Remove user from active conversation
        if user_id in conversation_active:
            del conversation_active[user_id]
            print(f"[DEBUG] User {user_id} removed from conversation. Active users: {list(conversation_active.keys())}")
        return random.choice([
            'bye! good luck with your studies!',
            'see you! come back if you need help',
            'later! happy studying',
            'goodbye! you got this!',
            'peace out! good luck',
        ])

    # Greetings
    if any(word in lowered for word in ['hi abg tutor', 'hey abg tutor', 'hello abg tutor', 'sup abg tutor', 'yo abg tutor', 'wassup abg tutor', 'what\'s up abg tutor', 'howdy abg tutor', 'greetings abg tutor', 'salutations abg tutor', 'how are you abg tutor', 'how you doing abg tutor', 'hows it going abg tutor', 'whats up abg tutor']):
        return random.choice([
            'hey! what\'s up?',
            'yo! how you doing?',
            'hey there! need help with anything?',
            'sup! what brings you here?',
            'hi! how can i help?',
        ])

    # How are you
    elif any(phrase in lowered for phrase in ['how are you', 'how r u', 'hows it going', 'how you doing', 'wyd']):
        return random.choice([
            'i\'m good! just here to help with your studies',
            'doing great! ready to help you ace those tests',
            'pretty good! what about you?',
            'chilling! you need help with anything?',
            'i\'m vibing! how are you?',
        ])

    # Good/fine responses
    elif any(word in lowered for word in ['good', 'fine', 'great', 'awesome', 'nice', 'cool']):
        return random.choice([
            'that\'s good to hear!',
            'glad you\'re doing well!',
            'nice! lmk if you need anything',
            'awesome! i\'m here if you need help',
            'bet! happy to help if you need it',
        ])

    # Bad/not good responses
    elif any(phrase in lowered for phrase in ['bad', 'not good', 'terrible', 'awful', 'struggling', 'stressed']):
        return random.choice([
            'aw sorry to hear that :( need help with anything?',
            'that sucks :( i\'m here if you need study help',
            'hope things get better! need any study resources?',
            'sending good vibes your way! need help with school stuff?',
        ])

    # What can you do
    elif any(phrase in lowered for phrase in ['what can you do', 'what do you do', 'how do you work', 'help me']):
        return 'i can help you with AP subjects, SAT, and ACT prep! just type `!help` to see all the subjects i cover'

    # School/homework related
    elif any(word in lowered for word in ['homework', 'test', 'exam', 'quiz', 'study', 'studying']):
        return random.choice([
            'need help studying? type `!help` to see all my resources!',
            'i got tons of study resources! use `!help` to see what i cover',
            'studying for something? check out `!help` for all my AP and test prep stuff',
            'got a test coming up? type `!help` to find resources for your subject',
        ])

    # Thank you
    elif any(word in lowered for word in ['thanks', 'thank you', 'thx', 'ty', 'appreciate']):
        return random.choice([
            'no problem!',
            'anytime!',
            'you\'re welcome!',
            'happy to help!',
            'of course!',
            'np!',
        ])

    # AP subjects mentioned
    elif 'ap' in lowered or any(word in lowered for word in ['biology', 'chemistry', 'physics', 'calculus', 'history', 'art', 'english', 'government', 'psychology', 'computer science', 'spanish', 'french', 'chinese', 'geography', 'statistics']):
        return 'looking for AP resources? type `!help` to see all the subjects i cover!'

    # SAT/ACT mentioned
    elif 'sat' in lowered or 'act' in lowered:
        return 'need test prep? i got SAT and ACT resources! type `!sat` or `!act`'

    # Jokes/funny
    elif any(word in lowered for word in ['joke', 'funny', 'lol', 'lmao', 'haha']):
        return random.choice([
            'lol i\'m better at tutoring than comedy',
            'haha glad you\'re having fun! need any study help?',
            'lmao i\'m here for the vibes and the study resources',
        ])

    # Yes/no responses
    elif lowered in ['yes', 'yeah', 'yea', 'yup', 'sure', 'ok', 'okay']:
        return random.choice([
            'cool! what do you need help with?',
            'alright! type `!help` to see what i can do',
            'bet! lmk what you need',
        ])

    elif lowered in ['no', 'nah', 'nope']:
        return random.choice([
            'no worries! i\'m here if you change your mind',
            'all good! just lmk if you need anything',
            'that\'s fine! i\'m always here to help',
        ])

    # Default response when bot doesn't understand
    else:
        return random.choice([
            'hmm not sure what you mean. need study help? type `!help`',
            'i didn\'t quite get that. type `!help` to see what i can do!',
            'sorry i\'m just a study bot lol. try `!help` to see my resources',
            'not sure how to respond to that. i\'m better with study stuff - type `!help`!',
            'hm i\'m a bit confused. wanna see my study resources? type `!help`',
        ])


# Function to send messages
async def send_message(message: Message, user_message: str) -> None:
    """
    This function handles sending the bot's response.
    It checks if the message should be private (DM) or public (in channel).
    """
    if not user_message:
        print('(Message was empty because intents were not enabled probably)')
        return

    # If the message starts with "?", send response as a DM
    is_private = False
    if user_message[0] == '?':
        user_message = user_message[1:]
        is_private = True

    try:
        response: str = get_response(user_message)

        # If get_response returns None, don't send anything (for normal chat messages)
        if response is None:
            return

        # Send as DM or in the channel
        if is_private:
            await message.author.send(response)
        else:
            await message.channel.send(response)
    except Exception as e:
        print(f'Error: {e}')


# Event: When the bot successfully connects to Discord
@client.event
async def on_ready() -> None:
    """
    This runs once when the bot starts up and connects to Discord.
    """
    print(f'{client.user} is now running!')


# Event: When someone sends a message in a channel the bot can see
@client.event
async def on_message(message: Message) -> None:
    """
    This runs every time someone sends a message.
    """
    # Ignore messages from the bot itself (prevents infinite loops!)
    if message.author == client.user:
        return

    lowered_content = message.content.lower()
    user_id = message.author.id

    # Check if bot is mentioned or in DMs - Handle mentions and DMs FIRST
    if client.user.mentioned_in(message) or isinstance(message.channel, DMChannel):
        # Remove mention from message
        user_input = message.content.replace(f'<@{client.user.id}>', '').replace(f'<@!{client.user.id}>', '').strip()

        # If they just pinged with no message, treat it like "hi abg tutor"
        if not user_input:
            user_input = "hi abg tutor"

        # Check if conversation was already active BEFORE getting response
        was_active = user_id in conversation_active and conversation_active[user_id]

        # If not active, mark as active now
        if not was_active:
            conversation_active[user_id] = True

        response = get_conversation_response(user_input, user_id)

        # Send response with prompt ONLY if this started the conversation
        if response:
            if not was_active:
                await message.channel.send(response + CONVERSATION_START_MSG)
            else:
                await message.channel.send(response)
        return

    # Check for compliment/appreciation phrases (always responds, doesn't start conversation)
    if any(phrase in lowered_content for phrase in [
        # Basic love/like
        'i like abg tutor', 'i love abg tutor', 'love abg tutor', 'i luv abg tutor',
        'luv abg tutor', 'love u abg tutor', 'ily abg tutor', 'abg tutor ily',
        'i <3 abg tutor', 'abg tutor <3', 'abg tutor ❤️', 'abg tutor 💕', 'i love you abg tutor', 
        'do you like me back abg tutor', 'do you like me abg tutor', 'do you love me abg tutor',

        # Quality/compliments
        'abg tutor is great', 'abg tutor is cool', 'abg tutor is the best',
        'abg tutor is amazing', 'abg tutor is awesome', 'abg tutor is so good',
        'abg tutor is fire', 'abg tutor is goated', 'abg tutor is elite',
        'abg tutor so good', 'abg tutor really good', 'abg tutor too good',

        # Goat/W variations
        'abg tutor goated', 'abg tutor the goat', 'abg tutor goat',
        'abg tutor w', 'w abg tutor', 'abg tutor is a w',
        'abg tutor massive w', 'abg tutor huge w',

        # Short lazy typing
        'abg tutor good', 'abg tutor best', 'abg tutor fire', 'abg tutor cool',
        'abg tutor>>>', 'abg tutor>>', 'abg tutor >>>',

        # Slang compliments
        'abg tutor clutch',
        'abg tutor carrying', 'abg tutor on top', 'abg tutor clears',
        'abg tutor bussin', 'abg tutor elite', 'abg tutor cracked',

        # Appreciation/thanks
        'thank you abg tutor', 'thanks abg tutor', 'ty abg tutor', 'thx abg tutor',
        'appreciate you abg tutor', 'appreciate abg tutor', 'abg tutor appreciate you',
        'abg tutor saved me', 'abg tutor came through', 'abg tutor clutched',
        'abg tutor helping me', 'abg tutor helps so much',

        # "Be" constructions
        'abg tutor be the best', 'abg tutor be helping',
        'abg tutor be clutch', 'abg tutor be carrying',

        # Vibe/energy
        'abg tutor energy',
        'abg tutor got the vibes',

        # Comparisons
        'abg tutor > everything', 'abg tutor better', 'abg tutor > everyone',
        'abg tutor best bot', 'abg tutor best tutor', 'abg tutor number 1',
        'abg tutor #1', 'nothing beats abg tutor',

        # Stan/support
        'stan abg tutor', 'abg tutor stan', 'abg tutor supremacy',
        'abg tutor nation', 'team abg tutor',

        # Random realistic ones
        'abg tutor goat fr', 'abg tutor the best fr', 'abg tutor w bot',
        'abg tutor fire ngl', 'abg tutor carrying fr', 'abg tutor so clutch',
        'abg tutor my fav', 'abg tutor my favorite', 'fav bot abg tutor',
        'best bot abg tutor', 'abg tutor undefeated', 'abg tutor never misses',
        'abg tutor always comes through',

        # Emojis combos people actually use
        'abg tutor 🔥', 'abg tutor 💯', 'abg tutor ✨', 'abg tutor 🙏',
        'abg tutor 🐐', 'abg tutor 👑', 'abg tutor 💪',
    ]):
        # Random response - picks ONE from the list
        romantic_responses = [
            'you\'re making me blush stopppp 💕',
            'my heart just skipped a beat ngl',
            'why am i blushing at my screen rn 😳',
            'you\'re too sweet i\'m melting 💕',
            'the way you just made my day >>> 💗',
            'not you making me feel all soft 🥹',
            'you\'re so cute for that 💖',
            'i\'m lowkey blushing this is embarrassing 😳',
            'you know how to make someone feel special 🥺',
            'my heart can\'t handle this rn 😭',
            'you\'re actually the sweetest ever 🥹💗',
            'why did that make me smile so hard 😳',
            'you\'re too good to me fr 🥺💖',
            'not me giggling and kicking my feet rn 😭',
            'you really know what to say huh 😳💗',
            'you got me swooning omg 🥹💕',
        ]

        friendly_responses = [
            'Thanks! You\'re awesome! ✨',
            'Thank you so much! 😊',
            'You made my day! 🌟',
            'That means a lot to me! 💙',
            'I appreciate that! 🙌',
            'Thanks for the support! 💪',
            'You\'re too kind! 😇',
            'Grateful for you! 🌸',
            'Thank you for being amazing! ⭐',
            'This made me so happy! 😄',
            'You\'re pretty cool yourself! 😎',
            'You get me! 🤝',
            'stop you\'re making me emotional 🥺',
            'you\'re too nice i can\'t handle it 😭',
            'bro you\'re the best fr 🫡',
            'love you gang!!',
            'you\'re my day one 🤝',
            'that\'s what i\'m talking about 🔥',
            'appreciate you bro 🙏',
            'we locked in fr 🔒💯',
            'you a real one 🤝',
            'nah you\'re goated fr 🐐',
            'we bros for life 👊',
            'bro really came through 🙏',
            'this why you my favorite 💯',
            'you got good taste ngl 😎',
            'same energy bro 🤝',
            'you understand the assignment 💯',
            'w taste fr 🔥',
            'you just get it 🤷',
            'you\'re in my top tier list 📊',
            'you already know wassup 💪',
        ]

        # Romantic reaction emojis (for special person)
        romantic_reactions = ['❤️', '💕', '💖', '💗', '💓', '💞', '💝', '🥰', '😍', '🥹', '😳', '🦋']

        # Friendly reaction emojis (for everyone else)
        friendly_reactions = ['👍', '💯', '🔥', '✨', '🙌', '🤝', '😎', '💪', '⭐', '🎉', '👊', '🫡']

        # REPLACE THIS WITH THE SPECIAL PERSON'S USER ID
        special_person_id = 561352123548172288  # Put their Discord ID here

        if message.author.id == special_person_id:
            # Special person ALWAYS gets romantic responses (100%)
            await message.add_reaction(random.choice(romantic_reactions))
            response = random.choice(romantic_responses)
        else:
            # Everyone else has 1/10 chance for romantic, 9/10 for friendly
            if random.random() < 0.1:  # 10% chance
                await message.add_reaction(random.choice(romantic_reactions))
                response = random.choice(romantic_responses)
            else:  # 90% chance
                await message.add_reaction(random.choice(friendly_reactions))
                response = random.choice(friendly_responses)

        await message.channel.send(response)
        return  # Don't start conversation, just respond once

    # Handle ! commands (ALWAYS responds, STARTS conversation)
    if message.content.startswith('!'):
        if message.content.strip() == '!':
            return

        username = str(message.author)
        user_message = message.content
        channel = str(message.channel)
        print(f'[{channel}] {username}: "{user_message}"')

        # Get the response
        response = get_response(user_message)
        if response:
            # Only add message if conversation wasn't already active
            if user_id not in conversation_active or not conversation_active[user_id]:
                conversation_active[user_id] = True
                await message.channel.send(response + CONVERSATION_START_MSG)
            else:
                await message.channel.send(response)
        return

    # Check if "hi abg tutor" or similar greetings - START conversation
    if any(phrase in lowered_content for phrase in [
        'hi abg tutor', 'hey abg tutor', 'hello abg tutor', 'sup abg tutor', 
        'yo abg tutor', 'wassup abg tutor', 'what\'s up abg tutor', 
        'howdy abg tutor', 'greetings abg tutor', 'salutations abg tutor'
    ]):
        # Only add message if conversation wasn't already active
        if user_id not in conversation_active or not conversation_active[user_id]:
            conversation_active[user_id] = True
            response = get_conversation_response(message.content, user_id)
            await message.channel.send(response + CONVERSATION_START_MSG)
        else:
            response = get_conversation_response(message.content, user_id)
            await message.channel.send(response)
        return

    # Check if bot is mentioned or in DMs - START conversation
    if client.user.mentioned_in(message) or isinstance(message.channel, DMChannel):
        # Remove mention from message
        user_input = message.content.replace(f'<@{client.user.id}>', '').replace(f'<@!{client.user.id}>', '').strip()

        if user_input:
            response = get_conversation_response(user_input, user_id)
            # Only add message if conversation wasn't already active
            if user_id not in conversation_active or not conversation_active[user_id]:
                conversation_active[user_id] = True
                await message.channel.send(response + CONVERSATION_START_MSG)
            else:
                await message.channel.send(response)
        return

    # ONLY continue conversation if user is already talking to bot
    if user_id in conversation_active and conversation_active[user_id]:
        response = get_conversation_response(message.content, user_id)
        # Check if conversation was ended (response will be a goodbye message or None)
        if response:
            await message.channel.send(response)
        return

    # If none of the above, ignore the message (don't respond)


# Main function to run the bot
def main() -> None:
    """
    This starts the bot and connects it to Discord using your token.
    """
    client.run(token=TOKEN)


# This runs the main function when you run the script
if __name__ == '__main__':
    main()