# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, session, make_response
from functools import wraps
import json
import random
import hashlib
import re
import secrets
from datetime import datetime, timedelta
from collections import defaultdict
import bcrypt

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(hours=24)

# In-memory storage (simulating database)
users_store = {}
sessions_store = {}
quiz_attempts = {}
certificates_issued = {}
training_progress = {}
feedback_store = []
leaderboard_data = defaultdict(lambda: {'score': 0, 'attempts': 0, 'best_percentage': 0})

# Comprehensive Quiz Questions Database
QUIZ_DATABASE = {
    'beginner': [
        {
            "id": "B001",
            "question": "What is the primary goal of a phishing attack?",
            "options": [
                "To improve website security",
                "To steal sensitive information",
                "To test network speed",
                "To update software"
            ],
            "correct": 1,
            "explanation": "Phishing attacks aim to steal personal information like passwords, credit card numbers, and sensitive data.",
            "points": 10,
            "tips": "Always verify the source before sharing any personal information online."
        },
        {
            "id": "B002",
            "question": "Which of these is a common sign of a phishing email?",
            "options": [
                "Professional design",
                "Personalized greeting with your name",
                "Urgent request for immediate action",
                "Clear sender information"
            ],
            "correct": 2,
            "explanation": "Phishing emails often create urgency to prevent you from thinking rationally and verifying the request.",
            "points": 10,
            "tips": "Take a moment to pause and verify any urgent requests through official channels."
        },
        {
            "id": "B003",
            "question": "What does HTTPS indicate on a website?",
            "options": [
                "The website is completely safe",
                "Data is encrypted during transmission",
                "The website is verified by Google",
                "No hackers can access the site"
            ],
            "correct": 1,
            "explanation": "HTTPS encrypts data between your browser and the website, but doesn't guarantee the site is legitimate.",
            "points": 10,
            "tips": "Look for HTTPS but also verify the domain name carefully."
        }
    ],
    'intermediate': [
        {
            "id": "I001",
            "question": "What is 'spear phishing'?",
            "options": [
                "Phishing using a spear as a metaphor",
                "Targeted attacks on specific individuals or organizations",
                "Mass emails sent to random people",
                "Phishing through phone calls"
            ],
            "correct": 1,
            "explanation": "Spear phishing uses personalized information to target specific victims, making the attack more convincing.",
            "points": 20,
            "tips": "Be especially cautious of emails that know personal details about you."
        },
        {
            "id": "I002",
            "question": "What technique do attackers use to make fake login pages look real?",
            "options": [
                "Domain spoofing",
                "Color matching",
                "Font optimization",
                "Speed enhancement"
            ],
            "correct": 0,
            "explanation": "Domain spoofing creates websites with similar-looking domain names to trick users.",
            "points": 20,
            "tips": "Always check the full URL in the address bar before entering credentials."
        },
        {
            "id": "I003",
            "question": "What is 'vishing'?",
            "options": [
                "Visual phishing through images",
                "Voice phishing through phone calls",
                "Video phishing through fake streams",
                "Virtual phishing in games"
            ],
            "correct": 1,
            "explanation": "Vishing uses phone calls to trick victims into revealing information.",
            "points": 20,
            "tips": "Never give personal information over unsolicited phone calls."
        }
    ],
    'advanced': [
        {
            "id": "A001",
            "question": "What is Business Email Compromise (BEC)?",
            "options": [
                "Email encryption standard",
                "Attack targeting wire transfers using spoofed executive emails",
                "Business email backup system",
                "Email filtering technology"
            ],
            "correct": 1,
            "explanation": "BEC attacks impersonate executives to authorize fraudulent wire transfers.",
            "points": 30,
            "tips": "Always verify large transactions through multiple communication channels."
        },
        {
            "id": "A002",
            "question": "What is 'pretexting' in social engineering?",
            "options": [
                "Creating a fake scenario to extract information",
                "Sending messages before the actual attack",
                "Testing security systems",
                "Encrypting stolen data"
            ],
            "correct": 0,
            "explanation": "Pretexting involves creating a fabricated story to manipulate victims.",
            "points": 30,
            "tips": "Be suspicious of anyone asking for information, even if they seem legitimate."
        },
        {
            "id": "A003",
            "question": "How can you identify a clone phishing attack?",
            "options": [
                "The email has perfect grammar",
                "The email appears identical to a legitimate one you've received before",
                "The email comes from a known contact",
                "The email has multiple attachments"
            ],
            "correct": 1,
            "explanation": "Clone phishing resends a legitimate email with malicious links or attachments.",
            "points": 30,
            "tips": "Verify unexpected 'resend' or 'updated version' emails through original channels."
        }
    ]
}

# Interactive Scenarios Database
SCENARIOS = [
    {
        "id": "SC001",
        "title": "🏦 The Bank Alert Scam",
        "difficulty": "Beginner",
        "category": "Email Phishing",
        "description": "You receive an email from 'Chase Bank' saying your account will be locked due to suspicious activity. The email has a link to 'verify your identity'.",
        "email_content": """
        From: security@chase-secure.com
        Subject: URGENT: Account Access Limited
        
        Dear Valued Customer,
        
        We detected unusual login attempts on your account from an unrecognized device.
        To prevent permanent account closure, verify your identity immediately:
        
        https://chase-account-verify.com/secure
        
        Failure to verify within 24 hours will result in account termination.
        
        Sincerely,
        Chase Security Team
        """,
        "red_flags": [
            "Suspicious sender domain (chase-secure.com vs chase.com)",
            "Generic greeting 'Dear Valued Customer'",
            "Creates urgency with 24-hour deadline",
            "Threatening language about account closure",
            "Suspicious URL not matching official bank domain"
        ],
        "correct_action": "Never click the link. Contact your bank directly using the official phone number on your bank statement or card.",
        "quiz": {
            "question": "What should you do with this email?",
            "options": [
                "Click the link and verify immediately",
                "Reply asking for more information",
                "Delete the email and call your bank using official number",
                "Forward to friends to check"
            ],
            "correct": 2
        }
    },
    {
        "id": "SC002",
        "title": "💼 CEO Fraud - Wire Transfer Request",
        "difficulty": "Advanced",
        "category": "Business Email Compromise",
        "description": "As a finance manager, you receive an email from your CEO requesting an urgent wire transfer of $50,000 to a new vendor.",
        "email_content": """
        From: ceo@yourcompany.com (spoofed)
        Subject: Urgent wire transfer needed - Confidential
        
        [Name],
        
        I'm in a client meeting and need your immediate assistance.
        Please wire $50,000 to this account for an emergency acquisition:
        
        Account: 987654321
        Routing: 123456789
        Bank: Regional Business Bank
        
        This is highly confidential. Process immediately and let me know when done.
        
        - [CEO Name]
        """,
        "red_flags": [
            "Request bypasses normal approval process",
            "Extreme urgency and confidentiality",
            "New vendor account not in system",
            "Can't verify through normal channels",
            "CEO typically doesn't send wire requests directly"
        ],
        "correct_action": "Never process wire transfers based solely on email. Call the CEO using a known phone number to verify.",
        "quiz": {
            "question": "What is the safest response?",
            "options": [
                "Process the transfer immediately to help the CEO",
                "Ask colleagues if they received similar requests",
                "Call the CEO using company directory phone number to verify",
                "Reply asking for more authorization"
            ],
            "correct": 2
        }
    },
    {
        "id": "SC003",
        "title": "📦 Package Delivery Scam",
        "difficulty": "Beginner",
        "category": "SMS Phishing (Smishing)",
        "description": "You receive a text message claiming a package couldn't be delivered and you need to pay a small fee for redelivery.",
        "email_content": """
        Text Message:
        UPS: Your package #US982347234 is on hold.
        Please pay $2.99 for redelivery at:
        https://ups-delivery-fee.com/pay
        
        Reply STOP to unsubscribe
        """,
        "red_flags": [
            "Unexpected delivery notification",
            "Not expecting any packages",
            "Suspicious URL not matching official UPS domain",
            "Request for payment for redelivery",
            "Generic tracking number format"
        ],
        "correct_action": "Don't click the link. Check tracking through official UPS website or app if expecting a package.",
        "quiz": {
            "question": "You're not expecting any packages. What should you do?",
            "options": [
                "Click the link to check anyway",
                "Reply with STOP to unsubscribe",
                "Delete the message and ignore",
                "Pay the fee to be safe"
            ],
            "correct": 2
        }
    },
    {
        "id": "SC004",
        "title": "🖥️ Tech Support Pop-up Scam",
        "difficulty": "Intermediate",
        "category": "Vishing/Tech Support",
        "description": "A pop-up appears on your browser with a loud alarm sound, claiming your computer is infected with 5 viruses and to call Microsoft Support immediately.",
        "email_content": """
        Browser Pop-up Alert:
        ⚠️ WINDOWS SECURITY WARNING ⚠️
        
        YOUR COMPUTER HAS BEEN LOCKED!
        5 VIRUSES DETECTED
        Call Microsoft Certified Support Immediately:
        1-888-XXX-XXXX
        
        DO NOT RESTART OR SHUT DOWN - DATA LOSS RISK
        """,
        "red_flags": [
            "Scare tactics with alarm sounds",
            "Claims of multiple viruses from a browser",
            "Requests to call a phone number",
            "Browser pop-up can't detect actual viruses",
            "Generic 'Microsoft Support' reference"
        ],
        "correct_action": "Close the browser using Task Manager. Run legitimate antivirus scan if concerned. Never call the number.",
        "quiz": {
            "question": "What should you do when seeing this pop-up?",
            "options": [
                "Call the number immediately for help",
                "Close browser via Task Manager, ignore pop-up",
                "Pay for their support service",
                "Restart computer immediately"
            ],
            "correct": 1
        }
    },
    {
        "id": "SC005",
        "title": "💸 Fake Invoice from Vendor",
        "difficulty": "Intermediate",
        "category": "Financial Scams",
        "description": "Your accounting department receives an invoice email from a regular vendor, but the payment details have changed.",
        "email_content": """
        From: accounting@vendor-service.com
        Subject: Updated Invoice #INV-2024-8932 - Immediate Payment Required
        
        Dear Accounting Team,
        
        Please find attached invoice #INV-2024-8932 for last month's services ($12,450).
        
        IMPORTANT: Our banking information has changed. Please update your records:
        New Bank: First National Bank
        Account: 876543210
        Routing: 321654987
        
        Payment is due within 5 business days to avoid late fees.
        
        Regards,
        Vendor Accounts Receivable
        """,
        "red_flags": [
            "Unexpected change in payment details",
            "Pressure to pay quickly",
            "Email from slightly different domain",
            "No prior notification of banking change",
            "Request to update payment records"
        ],
        "correct_action": "Verify banking changes through a phone call to known vendor contact numbers, not those in the email.",
        "quiz": {
            "question": "What's the safest way to handle this payment change?",
            "options": [
                "Update payment info and process invoice",
                "Call vendor using known phone number to verify change",
                "Reply to email asking for verification",
                "Hold payment indefinitely"
            ],
            "correct": 1
        }
    }
]

# Best Practices Database
BEST_PRACTICES = {
    "email_security": [
        {"title": "Check sender email addresses carefully", "description": "Look for misspellings or slight variations in domain names (e.g., paypa1.com instead of paypal.com)"},
        {"title": "Hover before you click", "description": "Mouse over links to see the actual URL before clicking"},
        {"title": "Verify unexpected attachments", "description": "Contact sender through different channel before opening unexpected attachments"},
        {"title": "Look for red flags", "description": "Poor grammar, urgent requests, threats, or too-good-to-be-true offers"},
        {"title": "Don't reply to suspicious emails", "description": "Replying confirms your email is active and monitored"},
        {"title": "Enable email filtering", "description": "Use spam filters and anti-phishing features in your email client"}
    ],
    "browser_security": [
        {"title": "Check for HTTPS", "description": "Look for padlock icon before entering sensitive information"},
        {"title": "Verify domain names", "description": "Check for misspelled domain names (amaz0n.com vs amazon.com)"},
        {"title": "Use password managers", "description": "They won't auto-fill on fake websites"},
        {"title": "Enable 2FA", "description": "Two-factor authentication adds critical protection layer"},
        {"title": "Keep software updated", "description": "Browser and security updates include protection against known threats"},
        {"title": "Use ad-blockers", "description": "Blocks malicious ads and pop-ups"}
    ],
    "general_awareness": [
        {"title": "Be skeptical by default", "description": "Question unsolicited requests for information"},
        {"title": "Verify through official channels", "description": "Use known phone numbers, not those provided in suspicious messages"},
        {"title": "Don't share credentials", "description": "Legitimate companies never ask for passwords via email or phone"},
        {"title": "Trust your instincts", "description": "If something feels wrong, it probably is"},
        {"title": "Report suspicious activity", "description": "Report phishing to IT department or relevant authorities"},
        {"title": "Regular security training", "description": "Stay updated on latest phishing techniques"}
    ]
}

# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function

def calculate_security_score(username):
    """Calculate user's overall security awareness score"""
    progress = training_progress.get(username, {})
    quiz_scores = progress.get('quiz_scores', {})
    
    total_score = 0
    max_score = 0
    
    for level in ['beginner', 'intermediate', 'advanced']:
        if level in quiz_scores:
            total_score += quiz_scores[level].get('percentage', 0)
            max_score += 100
    
    if max_score > 0:
        return (total_score / max_score) * 100
    return 0

def generate_certificate(username):
    """Generate certificate ID for completed training"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = hashlib.sha256(f"{username}{timestamp}{secrets.token_hex(8)}".encode()).hexdigest()[:12].upper()
    return f"PATC-{unique_id}"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/training')
@login_required
def training():
    return render_template('training.html')

@app.route('/scenarios')
@login_required
def scenarios():
    return render_template('scenarios.html')

@app.route('/quiz')
@login_required
def quiz():
    return render_template('quiz.html')

@app.route('/certificate')
@login_required
def certificate():
    return render_template('certificate.html')

# API Routes
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({'error': 'Username must be 3-20 characters'}), 400
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return jsonify({'error': 'Username can only contain letters, numbers, and underscore'}), 400
    
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    if username in users_store:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Store user
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    users_store[username] = {
        'username': username,
        'email': email,
        'password': hashed_password.decode('utf-8'),
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    
    # Initialize training progress
    training_progress[username] = {
        'quiz_scores': {},
        'scenarios_completed': [],
        'certificate_issued': False,
        'total_points': 0,
        'streak_days': 0,
        'last_active': datetime.now().isoformat()
    }
    
    session['user_id'] = username
    session.permanent = True
    
    return jsonify({'message': 'Registration successful', 'username': username}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username not in users_store:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    user = users_store[username]
    stored_password = user['password'].encode('utf-8')
    input_password = password.encode('utf-8')
    
    if bcrypt.checkpw(input_password, stored_password):
        session['user_id'] = username
        session.permanent = True
        user['last_login'] = datetime.now().isoformat()
        
        return jsonify({
            'message': 'Login successful',
            'username': username,
            'redirect': '/dashboard'
        }), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/user/profile')
@login_required
def get_user_profile():
    username = session['user_id']
    user = users_store.get(username, {})
    progress = training_progress.get(username, {})
    
    security_score = calculate_security_score(username)
    
    return jsonify({
        'username': username,
        'email': user.get('email'),
        'member_since': user.get('created_at'),
        'last_login': user.get('last_login'),
        'security_score': security_score,
        'total_points': progress.get('total_points', 0),
        'quiz_completed': len(progress.get('quiz_scores', {})) >= 3,
        'scenarios_completed': len(progress.get('scenarios_completed', [])),
        'certificate_issued': progress.get('certificate_issued', False),
        'streak_days': progress.get('streak_days', 0)
    }), 200

@app.route('/api/quiz/take', methods=['POST'])
@login_required
def take_quiz():
    data = request.json
    level = data.get('level', 'beginner')
    
    if level not in QUIZ_DATABASE:
        return jsonify({'error': 'Invalid quiz level'}), 400
    
    questions = QUIZ_DATABASE[level]
    # Remove correct answers for client-side (store indices separately)
    quiz_data = []
    for q in questions:
        quiz_data.append({
            'id': q['id'],
            'question': q['question'],
            'options': q['options'],
            'points': q['points']
        })
    
    # Store correct answers in session for validation
    session[f'quiz_{level}'] = {q['id']: q['correct'] for q in questions}
    session[f'quiz_points_{level}'] = {q['id']: q['points'] for q in questions}
    
    return jsonify({
        'level': level,
        'questions': quiz_data,
        'total_questions': len(questions)
    }), 200

@app.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    username = session['user_id']
    data = request.json
    level = data.get('level')
    answers = data.get('answers', {})
    
    stored_answers = session.get(f'quiz_{level}', {})
    points_map = session.get(f'quiz_points_{level}', {})
    
    score = 0
    total_points = 0
    results = []
    
    for q_id, selected in answers.items():
        correct = stored_answers.get(q_id)
        points = points_map.get(q_id, 0)
        
        is_correct = (int(selected) == correct)
        if is_correct:
            score += 1
            total_points += points
    
    percentage = (score / len(answers)) * 100 if answers else 0
    
    # Store progress
    if username not in training_progress:
        training_progress[username] = {'quiz_scores': {}, 'scenarios_completed': [], 'total_points': 0}
    
    training_progress[username]['quiz_scores'][level] = {
        'score': score,
        'total': len(answers),
        'percentage': percentage,
        'points_earned': total_points,
        'completed_at': datetime.now().isoformat()
    }
    
    training_progress[username]['total_points'] += total_points
    
    # Clear session quiz data
    session.pop(f'quiz_{level}', None)
    session.pop(f'quiz_points_{level}', None)
    
    # Check if all quizzes completed for certificate
    all_completed = len(training_progress[username]['quiz_scores']) >= 3
    
    return jsonify({
        'score': score,
        'total': len(answers),
        'percentage': percentage,
        'points_earned': total_points,
        'total_points': training_progress[username]['total_points'],
        'all_quizzes_completed': all_completed,
        'level_completed': level
    }), 200

@app.route('/api/scenarios/list')
@login_required
def get_scenarios_list():
    username = session['user_id']
    completed_scenarios = training_progress.get(username, {}).get('scenarios_completed', [])
    
    scenarios_with_status = []
    for scenario in SCENARIOS:
        scenarios_with_status.append({
            'id': scenario['id'],
            'title': scenario['title'],
            'difficulty': scenario['difficulty'],
            'category': scenario['category'],
            'description': scenario['description'],
            'completed': scenario['id'] in completed_scenarios
        })
    
    return jsonify({'scenarios': scenarios_with_status}), 200

@app.route('/api/scenarios/<scenario_id>')
@login_required
def get_scenario_detail(scenario_id):
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404
    
    return jsonify({
        'id': scenario['id'],
        'title': scenario['title'],
        'difficulty': scenario['difficulty'],
        'category': scenario['category'],
        'description': scenario['description'],
        'email_content': scenario['email_content'],
        'red_flags': scenario['red_flags'],
        'correct_action': scenario['correct_action'],
        'quiz': scenario['quiz']
    }), 200

@app.route('/api/scenarios/submit', methods=['POST'])
@login_required
def submit_scenario():
    username = session['user_id']
    data = request.json
    scenario_id = data.get('scenario_id')
    answer = data.get('answer')
    
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404
    
    is_correct = (answer == scenario['quiz']['correct'])
    
    if is_correct and scenario_id not in training_progress[username]['scenarios_completed']:
        training_progress[username]['scenarios_completed'].append(scenario_id)
        training_progress[username]['total_points'] += 50
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': scenario['quiz']['options'][scenario['quiz']['correct']],
        'explanation': scenario['correct_action'],
        'points_earned': 50 if is_correct else 0
    }), 200

@app.route('/api/best-practices')
@login_required
def get_best_practices():
    return jsonify(BEST_PRACTICES), 200

@app.route('/api/leaderboard')
@login_required
def get_leaderboard():
    leaderboard = []
    for username, progress in training_progress.items():
        total_points = progress.get('total_points', 0)
        quiz_scores = progress.get('quiz_scores', {})
        avg_percentage = sum(s.get('percentage', 0) for s in quiz_scores.values()) / max(len(quiz_scores), 1)
        
        leaderboard.append({
            'username': username,
            'points': total_points,
            'avg_score': round(avg_percentage, 1),
            'scenarios_completed': len(progress.get('scenarios_completed', [])),
            'badges_earned': len(quiz_scores)
        })
    
    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    return jsonify(leaderboard[:10]), 200

@app.route('/api/certificate/generate', methods=['POST'])
@login_required
def generate_certificate_endpoint():
    username = session['user_id']
    progress = training_progress.get(username, {})
    
    # Check if all quizzes completed
    if len(progress.get('quiz_scores', {})) >= 3:
        if not progress.get('certificate_issued'):
            certificate_id = generate_certificate(username)
            certificates_issued[username] = {
                'certificate_id': certificate_id,
                'issued_date': datetime.now().isoformat(),
                'username': username,
                'scores': progress.get('quiz_scores', {})
            }
            progress['certificate_issued'] = True
            
            return jsonify({
                'certificate_id': certificate_id,
                'issued_date': datetime.now().strftime("%B %d, %Y"),
                'username': username
            }), 200
        else:
            cert_data = certificates_issued.get(username, {})
            return jsonify({
                'certificate_id': cert_data.get('certificate_id'),
                'issued_date': cert_data.get('issued_date'),
                'username': username
            }), 200
    else:
        return jsonify({'error': 'Complete all quizzes to earn certificate'}), 400

@app.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.json
    username = session['user_id']
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    feedback_store.append({
        'username': username,
        'rating': rating,
        'comment': comment,
        'submitted_at': datetime.now().isoformat()
    })
    
    return jsonify({'message': 'Thank you for your feedback!'}), 200

@app.route('/api/stats')
@login_required
def get_stats():
    username = session['user_id']
    progress = training_progress.get(username, {})
    
    return jsonify({
        'total_users': len(users_store),
        'total_scenarios_completed': sum(len(p.get('scenarios_completed', [])) for p in training_progress.values()),
        'average_security_score': calculate_security_score(username),
        'completion_rate': round((len(progress.get('quiz_scores', {})) / 3) * 100, 1) if progress else 0
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)