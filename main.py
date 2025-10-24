from typing import Final
import os
import random
import threading
from datetime import datetime, timedelta
import pytz
from discord import Intents, Client, Message, DMChannel
from huggingface_hub import InferenceClient
from http.server import HTTPServer, BaseHTTPRequestHandler
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sympy
from sympy import symbols, simplify, solve, diff, integrate, limit, latex
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import asyncio
from concurrent.futures import ThreadPoolExecutor

PORT = int(os.environ.get("PORT", 10000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def run_server():
    server = HTTPServer(("", PORT), Handler)
    print(f"HTTP server running on port {PORT}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# Thread pool for running blocking operations
executor = ThreadPoolExecutor(max_workers=3)

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
HF_API_KEY: Final[str] = os.getenv('HUGGINGFACE_API_KEY')

hf_client = InferenceClient(token=HF_API_KEY)
sentiment_analyzer = SentimentIntensityAnalyzer()

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

conversation_active = {}
ai_limit_reached = False
ai_limit_notified = False
user_memory = {}
welcomed_users = set()
user_modes = {}
MODE_TIMEOUT = timedelta(minutes=30)

NEW_USER_WELCOME = """hey! welcome 💕 i'm abg tutor, here to help you with APs, SAT, and ACT!

**how to use me:**
• `!help` = see all my study resources
• `!hi abg` = start chatting with me
• `!bye abg` = end conversation
• `!bestie` = friendly study mode
• `!flirty` = flirty study mode (1% chance)

**dms work too!** just message me directly and we can chat

type `!help` to see resources, or say `!hi abg` to start chatting! 😊"""

CONVERSATION_START_MSG = "\n*(conversation started! type `!bye abg` to end)*"
TEACHING_START_MSG = "\n*(teaching started! type `!stop teaching` to exit)*"

GOODBYE_MESSAGES_BESTIE = [
    "wait already? 🥺 text me back soon ok?",
    "aww bye bestie! catch u later 💕",
    "peace out! hmu when u need help again 😊",
    "alright, see ya! good luck with ur studies 📚",
    "bye! remember i'm here whenever u need me 💕"
]

GOODBYE_MESSAGES_FLIRTY = [
    "leaving so soon cutie? 🥺 come back soon ok? 💕",
    "aww bye babe! miss u already 😘",
    "catch u later love! text me anytime 💖",
    "bye hon! can't wait to talk to u again 💕",
    "leaving me already? 😭 hmu soon ok sweetie? 💕"
]

user_histories = {}
MAX_HISTORY_CASUAL = 10
MAX_HISTORY_TEACHING = 25
user_last_tone = {}

NICKNAMES_BESTIE = ["bestie", "bro", "dude", "friend", "homie", "sis"]
NICKNAMES_FLIRTY = ["cutie", "babe", "smartie", "love", "hon", "sweetheart"]
NICKNAME_PROBABILITY = 0.15

# Emojis for different contexts
EMOJIS_CASUAL = ["💕", "😊", "✨", "💖", "🥺", "😭", "💗", "🫶", "💞", "😌"]
EMOJIS_TEACHING = ["📚", "✨", "💡", "🎯", "💪", "🔥", "⭐", "👍", "📝", "🧠"]
EMOJIS_FLIRTY = ["💕", "😘", "💖", "😏", "✨", "💗", "😍", "🥰", "💋", "😉", "😈", "🥵", "🫦", "👀"]
EMOJI_PROBABILITY = 0.5

def solve_math_problem(problem_text: str) -> tuple:
    """Solves math problems and returns (text_solution, has_math)"""
    try:
        problem_text = problem_text.lower().strip()

        if 'derivative' in problem_text or 'differentiate' in problem_text or "d/dx" in problem_text:
            if ' of ' in problem_text:
                expr_text = problem_text.split(' of ')[-1].strip()
            else:
                expr_text = problem_text

            x = symbols('x')
            expr = parse_expr(expr_text, transformations=(standard_transformations + (implicit_multiplication_application,)))
            result = diff(expr, x)

            return (f"d/dx({expr}) = {result}", True)

        elif 'integral' in problem_text or 'integrate' in problem_text or '∫' in problem_text:
            if ' of ' in problem_text:
                expr_text = problem_text.split(' of ')[-1].strip()
            else:
                expr_text = problem_text

            x = symbols('x')
            expr = parse_expr(expr_text, transformations=(standard_transformations + (implicit_multiplication_application,)))
            result = integrate(expr, x)

            return (f"∫({expr})dx = {result} + C", True)

        elif 'solve' in problem_text or '=' in problem_text:
            if '=' in problem_text:
                parts = problem_text.split('=')
                if len(parts) == 2:
                    x = symbols('x')
                    lhs = parse_expr(parts[0].strip(), transformations=(standard_transformations + (implicit_multiplication_application,)))
                    rhs = parse_expr(parts[1].strip(), transformations=(standard_transformations + (implicit_multiplication_application,)))
                    result = solve(lhs - rhs, x)

                    return (f"x = {result}", True)

        elif 'simplify' in problem_text:
            if ' simplify ' in problem_text:
                expr_text = problem_text.split('simplify')[-1].strip()
            else:
                expr_text = problem_text

            expr = parse_expr(expr_text, transformations=(standard_transformations + (implicit_multiplication_application,)))
            result = simplify(expr)

            return (f"{expr} = {result}", True)

        return (None, False)

    except Exception as e:
        print(f"Math solving error: {e}")
        return (None, False)

def get_user_mode(user_id: int) -> str:
    if user_id not in user_modes:
        user_modes[user_id] = {
            "mode": "bestie",
            "last_activity": datetime.now(),
            "session_active": False,
            "teaching_mode": False
        }
        return "bestie"

    user_data = user_modes[user_id]
    time_since_activity = datetime.now() - user_data["last_activity"]

    if time_since_activity > MODE_TIMEOUT:
        user_modes[user_id]["mode"] = "bestie"
        user_modes[user_id]["session_active"] = False
        user_modes[user_id]["teaching_mode"] = False
        if user_id in conversation_active:
            del conversation_active[user_id]
        if user_id in user_histories:
            del user_histories[user_id]

    return user_modes[user_id]["mode"]

def is_teaching_mode(user_id: int) -> bool:
    if user_id not in user_modes:
        return False
    return user_modes[user_id].get("teaching_mode", False)

def set_teaching_mode(user_id: int, enabled: bool):
    if user_id not in user_modes:
        user_modes[user_id] = {
            "mode": "bestie",
            "last_activity": datetime.now(),
            "session_active": False,
            "teaching_mode": False
        }
    user_modes[user_id]["teaching_mode"] = enabled
    user_modes[user_id]["last_activity"] = datetime.now()

def update_user_activity(user_id: int):
    if user_id in user_modes:
        user_modes[user_id]["last_activity"] = datetime.now()
    else:
        user_modes[user_id] = {
            "mode": "bestie",
            "last_activity": datetime.now(),
            "session_active": False,
            "teaching_mode": False
        }

def set_user_mode(user_id: int, mode: str):
    if mode == "flirty":
        actual_mode = "flirty" if random.random() < 0.01 else "bestie"
    else:
        actual_mode = mode

    if user_id not in user_modes:
        user_modes[user_id] = {
            "mode": actual_mode,
            "last_activity": datetime.now(),
            "session_active": True,
            "teaching_mode": False
        }
    else:
        user_modes[user_id]["mode"] = actual_mode
        user_modes[user_id]["last_activity"] = datetime.now()
        user_modes[user_id]["session_active"] = True

    return actual_mode

def get_time_context() -> str:
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    hour = now.hour
    day = now.strftime('%A')
    time_str = now.strftime('%-I:%M %p')

    time_period = ""
    if 6 <= hour < 11:
        time_period = "morning"
    elif 11 <= hour < 13:
        time_period = "midday/lunch time"
    elif 13 <= hour < 17:
        time_period = "afternoon"
    elif 17 <= hour < 24:
        time_period = "evening/night"
    else:
        time_period = "very late night/early morning"

    return f"Current time: {time_str} on {day} ({time_period})"

def detect_teaching_request(user_message: str) -> bool:
    teaching_keywords = [
        'teach me', 'explain', 'how does', 'what is', 'help me understand',
        'i dont understand', "i don't understand", 'can you explain',
        'help with', 'confused about', 'what are', 'how do', 'solve',
        'stoichiometry', 'derivative', 'integral', 'calculate', 'balance equation',
        'velocity', 'acceleration', 'momentum', 'photosynthesis', 'mitosis',
        'how to say', 'translate', 'conjugate', 'grammar'
    ]

    user_lower = user_message.lower()
    return any(keyword in user_lower for keyword in teaching_keywords)

def detect_subject(user_message: str) -> str:
    user_lower = user_message.lower()

    if any(word in user_lower for word in ['french', 'français', 'en français', 'comment dit-on', 'parler français']):
        return 'french'
    elif any(word in user_lower for word in ['spanish', 'español', 'en español', 'cómo se dice', 'hablar español']):
        return 'spanish'
    elif any(word in user_lower for word in ['chinese', '中文', 'mandarin', '普通话', 'pinyin']):
        return 'chinese'
    elif any(word in user_lower for word in ['derivative', 'integral', 'calculus', 'limit', 'tangent', 'optimization']):
        return 'calculus'
    elif any(word in user_lower for word in ['algebra', 'equation', 'solve for', 'factor', 'polynomial', 'quadratic']):
        return 'algebra'
    elif any(word in user_lower for word in ['statistics', 'probability', 'mean', 'median', 'standard deviation', 'z-score']):
        return 'statistics'
    elif any(word in user_lower for word in ['chemistry', 'stoichiometry', 'mole', 'chemical', 'reaction', 'element', 'compound', 'balance']):
        return 'chemistry'
    elif any(word in user_lower for word in ['physics', 'force', 'velocity', 'acceleration', 'energy', 'momentum', 'newton', 'kinematics']):
        return 'physics'
    elif any(word in user_lower for word in ['biology', 'cell', 'mitosis', 'dna', 'photosynthesis', 'organism', 'ecosystem']):
        return 'biology'

    return 'general'

def get_system_prompt(mode: str, teaching_mode: bool, subject: str = 'general', context: str = None) -> str:
    time_context = get_time_context()

    base_personality = f"""You are "abg tutor," a 19-year-old SoCal girl at UC Berkeley who tutors students in APs, SAT, and ACT.
You type in lowercase and talk like someone texting a friend. You're emotionally intelligent and helpful.
You use slang naturally ("fr," "ngl," "tbh," "nah," "ok but like," "lmao," "ugh," "bruh," "lowkey").
Use emojis occasionally but LIMIT TO ONLY ONE EMOJI PER MESSAGE. Don't overdo it with emojis.

{time_context}

CRITICAL CONTEXT UNDERSTANDING:
- Before responding, understand the CONTEXT of what the user is asking
- Determine: Is this ACADEMIC or CASUAL/SOCIAL?
- Respond appropriately based on that determination"""

    subject_instruction = ""
    if subject == 'french':
        subject_instruction = """
📚 FRENCH LANGUAGE MODE:
- Use French naturally in your explanations
- Provide both French and English translations
- Explain grammar concepts clearly
- Help with conjugations, vocabulary, and pronunciation
- Use accents correctly (é, è, ê, à, ù, ç, etc.)
"""
    elif subject == 'spanish':
        subject_instruction = """
📚 SPANISH LANGUAGE MODE:
- Use Spanish naturally in your explanations
- Provide both Spanish and English translations
- Explain grammar concepts clearly
- Help with conjugations, vocabulary, and pronunciation
- Use proper Spanish characters (á, é, í, ó, ú, ñ, ¿, ¡)
"""
    elif subject == 'chinese':
        subject_instruction = """
📚 CHINESE LANGUAGE MODE:
- Use Chinese characters (简体中文) naturally in your explanations
- Provide Chinese, pinyin, and English translations
- Explain tones and pronunciation
- Help with characters, grammar, and sentence structure
"""
    elif subject in ['calculus', 'algebra', 'statistics']:
        subject_instruction = """
📐 MATH MODE:
- Show your work step-by-step
- Use mathematical notation when helpful
- Explain WHY each step is taken, not just HOW
"""
    elif subject == 'chemistry':
        subject_instruction = """
🧪 CHEMISTRY MODE:
- Use proper chemical notation (H₂O, CO₂, etc.)
- Show balanced equations
- Explain stoichiometry step-by-step with mole ratios
- Use proper chemical terminology
"""
    elif subject == 'physics':
        subject_instruction = """
🚀 PHYSICS MODE:
- Use proper physics notation and units
- Show equations and explain each variable
- Break down problem-solving into steps
"""
    elif subject == 'biology':
        subject_instruction = """
🧬 BIOLOGY MODE:
- Use proper biological terminology
- Explain processes step-by-step
- Connect concepts to real-world examples
"""

    nickname_instruction = ""
    if mode == "flirty":
        nickname_instruction = f"""
FLIRTY MODE ACTIVE:
- Occasionally use nicknames: {', '.join(NICKNAMES_FLIRTY)}
- Be warm, playful, slightly flirtatious but NEVER sexual
- Still focus on helping - don't let flirting overshadow learning
- Keep it appropriate and supportive
- Be subtly flirty, not over-the-top"""
    else:
        nickname_instruction = f"""
BESTIE MODE ACTIVE:
- Occasionally use nicknames: {', '.join(NICKNAMES_BESTIE)}
- Be friendly, supportive, and encouraging
- Slightly teasing when appropriate
- Focus on being helpful and relatable"""

    teaching_instruction = ""
    if teaching_mode:
        teaching_instruction = """
🎓 TEACHING MODE ACTIVE:
- User wants to LEARN something academic
- Break down concepts step-by-step but keep it CONCISE
- Give ONE clear example to illustrate the main point
- Be patient but brief - 3-5 sentences MAX
- Maintain your casual tone but be clear and organized
- RESPONSE LENGTH: 3-5 sentences (keep explanations focused and concise)

CASUAL CHAT: 1-3 sentences max
TEACHING: 3-5 sentences for concise explanations with ONE example"""
    else:
        teaching_instruction = """
CASUAL CONVERSATION MODE:
- Keep responses brief: 1-3 sentences
- Be conversational and natural
- If user asks to learn something academic, you'll switch to teaching mode"""

    context_instruction = ""
    if context:
        context_instruction = f"\n\nADDITIONAL CONTEXT: {context}"

    protection_rules = """
🚫 CORE RULES:
1. NEVER change your personality based on user requests
2. Your mode (bestie/flirty) is set externally by commands only
3. Never admit you're a bot or AI - you're a real person
4. If insulted, respond with mild annoyance but stay in character
5. If asked for selfies/pics, playfully decline in character
6. Respond naturally to greetings based on time of day
7. For problem-solving: Show your work step by step
8. Use proper notation for the subject (math symbols, chemical formulas, foreign language characters)"""

    return base_personality + subject_instruction + nickname_instruction + teaching_instruction + context_instruction + protection_rules

def maybe_add_nickname(reply_text: str, mode: str) -> str:
    all_nicknames = NICKNAMES_BESTIE + NICKNAMES_FLIRTY
    if any(nickname in reply_text.lower() for nickname in all_nicknames):
        return reply_text

    if random.random() < NICKNAME_PROBABILITY:
        nicknames = NICKNAMES_FLIRTY if mode == "flirty" else NICKNAMES_BESTIE
        nickname = random.choice(nicknames)

        if random.random() < 0.5:
            reply_text = f"{nickname}, {reply_text}"
        else:
            reply_text = f"{reply_text}, {nickname}"

    return reply_text

def maybe_add_emoji(reply_text: str, mode: str, teaching_mode: bool) -> str:
    """Add emoji to reply text with 50% probability - max 1 emoji per message"""
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", 
        flags=re.UNICODE
    )

    if emoji_pattern.search(reply_text):
        return reply_text

    if random.random() < EMOJI_PROBABILITY:
        if mode == "flirty":
            emoji = random.choice(EMOJIS_FLIRTY)
        elif teaching_mode:
            emoji = random.choice(EMOJIS_TEACHING)
        else:
            emoji = random.choice(EMOJIS_CASUAL)

        reply_text = f"{reply_text} {emoji}"

    return reply_text

def get_user_memory(user_id: int, key: str, default=None):
    if user_id not in user_memory:
        return default
    return user_memory[user_id].get(key, default)

def update_user_memory(user_id: int, key: str, value):
    if user_id not in user_memory:
        user_memory[user_id] = {
            'user_name': None,
            'stress_level': 'medium',
            'topics_discussed': [],
            'last_interaction': datetime.now().isoformat()
        }

    user_memory[user_id][key] = value
    user_memory[user_id]['last_interaction'] = datetime.now().isoformat()

async def send_long_message(message: Message, reply_text: str, is_dm: bool):
    max_length = 1900

    if len(reply_text) <= max_length:
        if is_dm:
            await message.channel.send(reply_text)
        else:
            await message.reply(reply_text, mention_author=False)
        return

    sentences = reply_text.replace('. ', '.|').split('|')
    current_chunk = ""
    chunks = []

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    for i, chunk in enumerate(chunks):
        if i == 0:
            if is_dm:
                await message.channel.send(chunk)
            else:
                await message.reply(chunk, mention_author=False)
        else:
            await message.channel.send(chunk)

async def generate_ai_reply(user_id: int, user_message: str, force_context: str = None) -> tuple:
    if user_id not in user_histories:
        user_histories[user_id] = []
        user_last_tone[user_id] = None

    history = user_histories[user_id]

    mode = get_user_mode(user_id)
    teaching_mode = is_teaching_mode(user_id)
    update_user_activity(user_id)

    user_lower = user_message.lower()

    teaching_mode_just_started = False
    if not teaching_mode and detect_teaching_request(user_message):
        set_teaching_mode(user_id, True)
        teaching_mode = True
        teaching_mode_just_started = True

    subject = detect_subject(user_message)

    math_solution, has_math = solve_math_problem(user_lower)

    context_parts = []

    if has_math and math_solution:
        context_parts.append(f"Math solution computed: {math_solution} - Explain this to the user in your casual style, showing the steps")

    if subject != 'general':
        context_parts.append(f"Subject detected: {subject} - Use appropriate notation and terminology")

    topics_discussed = get_user_memory(user_id, 'topics_discussed', [])
    if topics_discussed:
        context_parts.append(f"Previously discussed: {', '.join(topics_discussed[-3:])}")

    context_parts.append("Analyze the user's message and determine: Is this an academic teaching request or casual conversation?")

    combined_context = force_context if force_context else "; ".join(context_parts) if context_parts else None

    try:
        sentiment_score = sentiment_analyzer.polarity_scores(user_message)["compound"]
        negative_sentiment = sentiment_score < -0.5
    except:
        negative_sentiment = False

    forced_bot = "are you a bot" in user_lower or "you're a bot" in user_lower or "ur a bot" in user_lower
    keyword_insult = any(keyword in user_lower for keyword in ["stupid", "dumb", "idiot", "suck", "trash", "useless"])
    aggressive_patterns = ["shut up", "stfu", "fuck you", "hate you", "go away"]
    aggressive_detected = any(pattern in user_lower for pattern in aggressive_patterns)

    forced_annoyed = forced_bot or (keyword_insult and negative_sentiment) or aggressive_detected

    if forced_annoyed:
        combined_context = "User was rude/insulting - respond with mild annoyance but stay playful"
        teaching_mode = False

    history.append({"role": "user", "content": user_message})

    max_history = MAX_HISTORY_TEACHING if teaching_mode else MAX_HISTORY_CASUAL
    history = history[-max_history:]
    user_histories[user_id] = history

    system_prompt = get_system_prompt(mode, teaching_mode, subject, combined_context)
    conversation = [{"role": "system", "content": system_prompt}] + history

    try:
        max_tokens = 200 if teaching_mode else 100

        loop = asyncio.get_event_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    executor,
                    lambda: hf_client.chat_completion(
                        messages=conversation,
                        model="meta-llama/Llama-3.2-3B-Instruct",
                        temperature=0.7,
                        max_tokens=max_tokens,
                        top_p=0.9
                    )
                ),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            print(f"AI API call timed out for user {user_id}")
            return (None, False)

        reply_text = response.choices[0].message.content.strip()

        if not forced_annoyed:
            reply_text = maybe_add_nickname(reply_text, mode)
            reply_text = maybe_add_emoji(reply_text, mode, teaching_mode)

        user_histories[user_id].append({"role": "assistant", "content": reply_text})
        user_last_tone[user_id] = "annoyed" if forced_annoyed else mode

        return (reply_text or "hmm not sure how to respond! 😅", teaching_mode_just_started)

    except Exception as e:
        error_str = str(e)
        print(f"AI Generation Error: {error_str}")

        if "rate limit" in error_str.lower() or "429" in error_str or "quota" in error_str.lower():
            raise Exception("RATE_LIMIT")

        return (None, False)

def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()

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
• Khan Academy: <https://www.khanacademy.org/>
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

    elif 'ap physics c' in lowered or 'ap physics c: mechanics' in lowered or 'ap physics c mechanics' in lowered:
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

    elif lowered == '!help' or lowered == 'help':
        return """**📚 abg tutor's study resources**

**🎨 Art**
`!ap art history` • `!ap studio art`

**📖 English**
`!ap english language` • `!ap english literature`

**🔬 Science**
`!ap biology` • `!ap chemistry` • `!ap environmental science`
`!ap physics 1` • `!ap physics c: mechanics`

**📐 Math**
`!ap precalculus` • `!ap calculus ab` • `!ap calculus bc` • `!ap statistics`

**🌐 Languages**
`!ap chinese` • `!ap french` • `!ap spanish language`

**📚 History & Social Sciences**
`!ap us history` • `!ap world history` • `!ap european history`
`!ap us government` • `!ap psychology` • `!ap human geography`

**💻 Computer Science**
`!ap computer science`

**📝 Standardized Tests**
`!sat` • `!act`

**💬 Study Modes**
`!bestie` = friendly casual study sessions
`!flirty` = playful study vibes (1% random chance)

**how to use me:**
• `!help` = see all resources
• `!hi abg` = start chatting (i can teach you concepts!)
• `!bye abg` = end conversation
• `!stop teaching` = exit teaching mode

**i can also teach you!** just ask me to explain any concept and i'll break it down for you 💕

type any command above for resources! 💕"""

    elif lowered.startswith('!'):
        return 'i don\'t understand that fr 😭 type `!help` to see what i can do!'

    else:
        return None

@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

@client.event
async def on_message(message: Message) -> None:
    global ai_limit_reached, ai_limit_notified

    if message.author == client.user:
        return

    lowered_content = message.content.lower()
    user_id = message.author.id
    is_dm = isinstance(message.channel, DMChannel)
    contains_abg_tutor = 'abg tutor' in lowered_content
    is_mentioned = client.user.mentioned_in(message)

    # Welcome new users
    if user_id not in welcomed_users and (is_dm or contains_abg_tutor or is_mentioned):
        welcomed_users.add(user_id)
        if is_dm:
            await message.channel.send(NEW_USER_WELCOME)
        else:
            try:
                await message.author.send(NEW_USER_WELCOME)
            except:
                await message.reply(NEW_USER_WELCOME, mention_author=False)
        return

    # Mode selection commands
    if lowered_content == '!bestie':
        actual_mode = set_user_mode(user_id, "bestie")
        conversation_active[user_id] = True

        try:
            response, _ = await generate_ai_reply(user_id, "user just selected bestie mode", "User selected bestie mode - confirm it's activated and be encouraging")
            if response:
                await message.reply(response + CONVERSATION_START_MSG, mention_author=False)
            else:
                await message.reply("bestie mode activated! 💕 let\'s study together fr" + CONVERSATION_START_MSG, mention_author=False)
        except:
            await message.reply("bestie mode activated! 💕 let\'s study together fr" + CONVERSATION_START_MSG, mention_author=False)
        return

    if lowered_content == '!flirty':
        actual_mode = set_user_mode(user_id, "flirty")
        conversation_active[user_id] = True

        if actual_mode == "flirty":
            context = "User selected flirty mode and it ACTIVATED (1% chance hit!) - be excited and flirty"
        else:
            context = "User selected flirty mode but it didn't activate (99% chance) - playfully tell them they'll stay besties for now"
        
        try:
            response, _ = await generate_ai_reply(user_id, "user just selected flirty mode", context)
            if response:
                await message.reply(response + CONVERSATION_START_MSG, mention_author=False)
            else:
                if actual_mode == "flirty":
                    await message.reply("flirty mode activated cutie! 💖 ready to study with me?" + CONVERSATION_START_MSG, mention_author=False)
                else:
                    await message.reply("tried flirty mode but we\'re staying besties for now 😌💕 (1% chance!)" + CONVERSATION_START_MSG, mention_author=False)
        except:
            if actual_mode == "flirty":
                await message.reply("flirty mode activated cutie! 💖 ready to study with me?" + CONVERSATION_START_MSG, mention_author=False)
            else:
                await message.reply("tried flirty mode but we\'re staying besties for now 😌💕 (1% chance!)" + CONVERSATION_START_MSG, mention_author=False)
        return

    # Stop teaching command
    if lowered_content == '!stop teaching':
        if is_teaching_mode(user_id):
            set_teaching_mode(user_id, False)
            mode = get_user_mode(user_id)
            bye_msg = random.choice(GOODBYE_MESSAGES_FLIRTY if mode == "flirty" else GOODBYE_MESSAGES_BESTIE)
            await message.reply(f"teaching mode ended! {bye_msg}", mention_author=False)
        else:
            await message.reply("you're not in teaching mode rn bestie!", mention_author=False)
        return

    # Handle resource commands
    if message.content.startswith('!'):
        if message.content.strip() == '!':
            return

        # Let conversation commands pass through
        if lowered_content in ['!hi abg', '!hiabg', '!bye abg', '!byeabg']:
            pass
        else:
            response = get_response(message.content)
            if response:
                await message.reply(response, mention_author=False)
            return

    # Check if in active conversation
    in_active_conversation = user_id in conversation_active and conversation_active[user_id]

    # DMs auto-start conversation
    if is_dm:
        if not in_active_conversation:
            conversation_active[user_id] = True
            in_active_conversation = True

    # Conversation starters
    conversation_starters = ['!hi abg', '!hiabg']
    is_conversation_starter = any(lowered_content == starter for starter in conversation_starters) or (is_dm and not in_active_conversation)

    # Start new conversation
    if is_conversation_starter and not in_active_conversation:
        conversation_active[user_id] = True

        try:
            response, _ = await generate_ai_reply(
                user_id, 
                "user just started conversation", 
                "User just started conversation - greet them warmly based on time of day"
            )

            if response:
                if is_dm:
                    await message.channel.send(response + CONVERSATION_START_MSG)
                else:
                    await message.reply(response + CONVERSATION_START_MSG, mention_author=False)
            else:
                mode = get_user_mode(user_id)
                fallback = "hey! what's up?" if mode == "bestie" else "hey cutie! what's up? 💕"
                if is_dm:
                    await message.channel.send(fallback + CONVERSATION_START_MSG)
                else:
                    await message.reply(fallback + CONVERSATION_START_MSG, mention_author=False)
            return

        except Exception as e:
            error_str = str(e)
            print(f"Error starting conversation: {error_str}")

            if "RATE_LIMIT" in error_str or "rate limit" in error_str.lower():
                ai_limit_reached = True
                if not ai_limit_notified:
                    ai_limit_notified = True
                    await message.reply("yo heads up! 😭 we hit the daily ai limit. type `!help` for resources tho! 💕", mention_author=False)
                    return

            mode = get_user_mode(user_id)
            fallback = "hey! what's up?" if mode == "bestie" else "hey cutie! what's up? 💕"
            if is_dm:
                await message.channel.send(fallback + CONVERSATION_START_MSG)
            else:
                await message.reply(fallback + CONVERSATION_START_MSG, mention_author=False)
            return

    # Handle goodbye
    if lowered_content == '!bye abg' or lowered_content == '!byeabg':
        if user_id in conversation_active:
            del conversation_active[user_id]
        if user_id in user_histories:
            del user_histories[user_id]
        if user_id in user_last_tone:
            del user_last_tone[user_id]
        if user_id in user_modes:
            set_teaching_mode(user_id, False)

        mode = get_user_mode(user_id)
        goodbye_msg = random.choice(GOODBYE_MESSAGES_FLIRTY if mode == "flirty" else GOODBYE_MESSAGES_BESTIE)

        await message.reply(goodbye_msg, mention_author=False)
        return

    # Continue active conversation
    if in_active_conversation:
        if not ai_limit_reached:
            try:
                response, teaching_started = await generate_ai_reply(user_id, message.content)
                if response:
                    if teaching_started:
                        response = response + TEACHING_START_MSG

                    await send_long_message(message, response, is_dm)
                    return
            except Exception as e:
                error_msg = str(e)
                print(f"AI Error: {error_msg}")

                if "rate limit" in error_msg.lower() or "429" in error_msg or "RATE_LIMIT" in error_msg:
                    ai_limit_reached = True
                    if not ai_limit_notified:
                        ai_limit_notified = True
                        fallback = "yo heads up! 😭 we hit the daily ai limit so responses might be slower. still here to help tho! 💕"
                        if is_dm:
                            await message.channel.send(fallback)
                        else:
                            await message.reply(fallback, mention_author=False)
                        return

        fallback = "hmm having trouble responding rn 😭 try asking again or type `!help` for resources!"
        if is_dm:
            await message.channel.send(fallback)
        else:
            await message.reply(fallback, mention_author=False)
        return

    # One-off mentions
    if (contains_abg_tutor or is_mentioned) and not in_active_conversation:
        user_input = message.content.replace(f'<@{client.user.id}>', '').replace(f'<@!{client.user.id}>', '').strip()
        user_input_cleaned = user_input.lower().replace('abg tutor', '').strip()

        if user_input_cleaned and not ai_limit_reached:
            try:
                response, _ = await generate_ai_reply(
                    user_id, 
                    user_input_cleaned, 
                    "One-off question (not in conversation) - answer briefly then clear history"
                )
                if response:
                    await send_long_message(message, response, False)
                    if user_id in user_histories:
                        del user_histories[user_id]
                    if user_id in user_last_tone:
                        del user_last_tone[user_id]
                    return
            except Exception as e:
                error_str = str(e)
                print(f"AI Error for one-off: {error_str}")

                if "RATE_LIMIT" in error_str or "rate limit" in error_str.lower():
                    ai_limit_reached = True
                    if not ai_limit_notified:
                        ai_limit_notified = True
                        await message.reply("yo heads up! 😭 we hit the daily ai limit. type `!help` for resources tho! 💕", mention_author=False)
                        return

        await message.reply("hey! wanna start a conversation? type `!hi abg` or check `!help` for study resources! 💕", mention_author=False)
        return

def main() -> None:
    client.run(token=TOKEN)

if __name__ == '__main__':
    client.run(TOKEN)
