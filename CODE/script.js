// script.js - Complete JavaScript for PhishGuard Pro

// ==================== GLOBAL VARIABLES ====================
let currentUser = null;
let quizData = null;
let currentQuiz = null;
let userAnswers = {};
let currentScenario = null;

// ==================== UTILITY FUNCTIONS ====================

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} animate-fadeInUp`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.maxWidth = '400px';
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Show loading spinner
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

// Hide loading spinner
function hideLoading(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Validate email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate username
function validateUsername(username) {
    const re = /^[a-zA-Z0-9_]{3,20}$/;
    return re.test(username);
}

// Validate password
function validatePassword(password) {
    return password.length >= 6;
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard!', 'success');
    } catch (err) {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy', 'danger');
    }
}

// ==================== AUTHENTICATION FUNCTIONS ====================

// Login function
async function login(username, password) {
    if (!username || !password) {
        showNotification('Please fill in all fields', 'danger');
        return false;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
            return true;
        } else {
            showNotification(data.error || 'Login failed', 'danger');
            return false;
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Error connecting to server', 'danger');
        return false;
    }
}

// Register function
async function register(username, email, password) {
    if (!username || !email || !password) {
        showNotification('Please fill in all fields', 'danger');
        return false;
    }
    
    if (!validateUsername(username)) {
        showNotification('Username must be 3-20 characters (letters, numbers, underscore)', 'danger');
        return false;
    }
    
    if (!validateEmail(email)) {
        showNotification('Please enter a valid email address', 'danger');
        return false;
    }
    
    if (!validatePassword(password)) {
        showNotification('Password must be at least 6 characters', 'danger');
        return false;
    }
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Registration successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
            return true;
        } else {
            showNotification(data.error || 'Registration failed', 'danger');
            return false;
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Error connecting to server', 'danger');
        return false;
    }
}

// Logout function
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/';
    }
}

// Check authentication status
async function checkAuth() {
    try {
        const response = await fetch('/api/user/profile');
        if (response.ok) {
            currentUser = await response.json();
            return true;
        }
        return false;
    } catch (error) {
        return false;
    }
}

// ==================== QUIZ FUNCTIONS ====================

// Start quiz
async function startQuiz(level) {
    try {
        const response = await fetch('/api/quiz/take', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level })
        });
        
        if (response.ok) {
            quizData = await response.json();
            currentQuiz = {
                level: level,
                questions: quizData.questions,
                currentIndex: 0,
                answers: {}
            };
            displayQuiz();
        } else {
            showNotification('Failed to load quiz', 'danger');
        }
    } catch (error) {
        console.error('Error starting quiz:', error);
        showNotification('Error loading quiz', 'danger');
    }
}

// Display current quiz question
function displayQuiz() {
    if (!currentQuiz) return;
    
    const question = currentQuiz.questions[currentQuiz.currentIndex];
    const quizContainer = document.getElementById('quizContainer');
    
    if (quizContainer) {
        quizContainer.innerHTML = `
            <div class="quiz-header">
                <div class="quiz-progress">
                    Question ${currentQuiz.currentIndex + 1} of ${currentQuiz.questions.length}
                </div>
                <div class="quiz-points">Points: ${question.points}</div>
            </div>
            <div class="quiz-question">${escapeHtml(question.question)}</div>
            <div class="quiz-options">
                ${question.options.map((option, idx) => `
                    <div class="quiz-option ${currentQuiz.answers[question.id] === idx ? 'selected' : ''}" 
                         onclick="selectAnswer('${question.id}', ${idx})">
                        ${String.fromCharCode(65 + idx)}. ${escapeHtml(option)}
                    </div>
                `).join('')}
            </div>
            <div class="quiz-controls">
                <button class="btn btn-secondary" onclick="previousQuestion()" ${currentQuiz.currentIndex === 0 ? 'disabled' : ''}>
                    ← Previous
                </button>
                <button class="btn btn-primary" onclick="nextQuestion()">
                    ${currentQuiz.currentIndex === currentQuiz.questions.length - 1 ? 'Submit Quiz' : 'Next →'}
                </button>
            </div>
        `;
    }
}

// Select answer
function selectAnswer(questionId, answerIndex) {
    if (currentQuiz) {
        currentQuiz.answers[questionId] = answerIndex;
        displayQuiz();
    }
}

// Next question
function nextQuestion() {
    if (!currentQuiz) return;
    
    const currentQuestion = currentQuiz.questions[currentQuiz.currentIndex];
    
    if (currentQuiz.answers[currentQuestion.id] === undefined) {
        showNotification('Please select an answer before continuing', 'warning');
        return;
    }
    
    if (currentQuiz.currentIndex === currentQuiz.questions.length - 1) {
        submitQuiz();
    } else {
        currentQuiz.currentIndex++;
        displayQuiz();
    }
}

// Previous question
function previousQuestion() {
    if (currentQuiz && currentQuiz.currentIndex > 0) {
        currentQuiz.currentIndex--;
        displayQuiz();
    }
}

// Submit quiz
async function submitQuiz() {
    try {
        const response = await fetch('/api/quiz/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level: currentQuiz.level,
                answers: currentQuiz.answers
            })
        });
        
        if (response.ok) {
            const results = await response.json();
            displayQuizResults(results);
        } else {
            showNotification('Failed to submit quiz', 'danger');
        }
    } catch (error) {
        console.error('Error submitting quiz:', error);
        showNotification('Error submitting quiz', 'danger');
    }
}

// Display quiz results
function displayQuizResults(results) {
    const quizContainer = document.getElementById('quizContainer');
    const percentage = Math.round(results.percentage);
    
    let feedbackHtml = `
        <div class="quiz-results">
            <h2>Quiz Results</h2>
            <div class="quiz-score">
                Score: ${results.score}/${results.total} (${percentage}%)
            </div>
            <div class="quiz-points-earned">
                Points Earned: ${results.points_earned}
            </div>
            <div class="quiz-feedback">
                <h3>Detailed Feedback:</h3>
    `;
    
    results.results.forEach((result, index) => {
        feedbackHtml += `
            <div class="${result.is_correct ? 'quiz-feedback-correct' : 'quiz-feedback-incorrect'}">
                <strong>Question ${index + 1}: ${escapeHtml(result.question)}</strong><br>
                Your answer: ${escapeHtml(result.selected)}<br>
                ${!result.is_correct ? `Correct answer: ${escapeHtml(result.correct)}<br>` : ''}
                <em>${escapeHtml(result.explanation)}</em>
            </div>
        `;
    });
    
    feedbackHtml += `
            </div>
            <button class="btn btn-primary" onclick="location.reload()">Take Another Quiz</button>
        </div>
    `;
    
    if (quizContainer) {
        quizContainer.innerHTML = feedbackHtml;
    }
}

// ==================== SCENARIO FUNCTIONS ====================

// Load scenarios
async function loadScenarios() {
    try {
        const response = await fetch('/api/scenarios/list');
        if (response.ok) {
            const data = await response.json();
            displayScenarios(data.scenarios);
        }
    } catch (error) {
        console.error('Error loading scenarios:', error);
        showNotification('Error loading scenarios', 'danger');
    }
}

// Display scenarios
function displayScenarios(scenarios) {
    const grid = document.getElementById('scenariosGrid');
    if (!grid) return;
    
    grid.innerHTML = scenarios.map(scenario => `
        <div class="card scenario-card" onclick="viewScenario('${scenario.id}')">
            <div class="scenario-header">
                <h3>${escapeHtml(scenario.title)}</h3>
                <div class="scenario-meta">
                    <span class="badge ${scenario.difficulty === 'Beginner' ? 'badge-success' : scenario.difficulty === 'Intermediate' ? 'badge-warning' : 'badge-danger'}">
                        ${scenario.difficulty}
                    </span>
                    <span class="badge badge-info">${scenario.category}</span>
                    ${scenario.completed ? '<span class="badge badge-success">✓ Completed</span>' : ''}
                </div>
            </div>
            <div class="scenario-description">
                ${escapeHtml(scenario.description.substring(0, 100))}...
            </div>
        </div>
    `).join('');
}

// View scenario
async function viewScenario(scenarioId) {
    try {
        const response = await fetch(`/api/scenarios/${scenarioId}`);
        if (response.ok) {
            currentScenario = await response.json();
            showScenarioModal();
        }
    } catch (error) {
        console.error('Error loading scenario:', error);
        showNotification('Error loading scenario', 'danger');
    }
}

// Show scenario modal
function showScenarioModal() {
    if (!currentScenario) return;
    
    const modal = document.getElementById('scenarioModal');
    const modalContent = document.getElementById('modalContent');
    
    if (modal && modalContent) {
        modalContent.innerHTML = `
            <div class="modal-header">${escapeHtml(currentScenario.title)}</div>
            <p><strong>Difficulty:</strong> ${currentScenario.difficulty} | <strong>Category:</strong> ${currentScenario.category}</p>
            <p>${escapeHtml(currentScenario.description)}</p>
            
            <h3>📧 Suspicious Email/Message:</h3>
            <div class="scenario-email">${escapeHtml(currentScenario.email_content)}</div>
            
            <div class="red-flags">
                <strong>🚩 Red Flags to Watch For:</strong>
                <ul class="red-flag-list">
                    ${currentScenario.red_flags.map(flag => `<li>${escapeHtml(flag)}</li>`).join('')}
                </ul>
            </div>
            
            <div class="quiz-section">
                <h3>📝 Test Your Knowledge</h3>
                <p><strong>${escapeHtml(currentScenario.quiz.question)}</strong></p>
                <div id="scenarioQuizOptions">
                    ${currentScenario.quiz.options.map((opt, idx) => `
                        <div class="quiz-option" onclick="submitScenarioAnswer(${idx})">
                            ${String.fromCharCode(65 + idx)}. ${escapeHtml(opt)}
                        </div>
                    `).join('')}
                </div>
                <div id="scenarioFeedback"></div>
            </div>
            
            <div class="correct-action">
                <strong>✅ Recommended Action:</strong><br>
                ${escapeHtml(currentScenario.correct_action)}
            </div>
        `;
        
        modal.style.display = 'flex';
    }
}

// Submit scenario answer
async function submitScenarioAnswer(answerIndex) {
    if (!currentScenario) return;
    
    try {
        const response = await fetch('/api/scenarios/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_id: currentScenario.id,
                answer: answerIndex
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            const feedbackDiv = document.getElementById('scenarioFeedback');
            
            if (result.correct) {
                feedbackDiv.innerHTML = `
                    <div class="alert alert-success">
                        ✅ Correct! ${escapeHtml(result.explanation)}<br>
                        ⭐ +${result.points_earned} points earned!
                    </div>
                `;
                loadScenarios(); // Refresh list
            } else {
                feedbackDiv.innerHTML = `
                    <div class="alert alert-danger">
                        ❌ Incorrect. Correct answer: ${escapeHtml(result.correct_answer)}<br>
                        ${escapeHtml(result.explanation)}
                    </div>
                `;
            }
            
            // Disable options
            document.querySelectorAll('#scenarioQuizOptions .quiz-option').forEach(opt => {
                opt.style.opacity = '0.5';
                opt.style.cursor = 'default';
                opt.onclick = null;
            });
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        showNotification('Error submitting answer', 'danger');
    }
}

// ==================== CERTIFICATE FUNCTIONS ====================

// Generate certificate
async function generateCertificate() {
    try {
        const response = await fetch('/api/certificate/generate', { method: 'POST' });
        
        if (response.ok) {
            const data = await response.json();
            displayCertificate(data);
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to generate certificate', 'danger');
        }
    } catch (error) {
        console.error('Error generating certificate:', error);
        showNotification('Error generating certificate', 'danger');
    }
}

// Display certificate
function displayCertificate(certificateData) {
    const certificateContainer = document.getElementById('certificateContainer');
    if (!certificateContainer) return;
    
    certificateContainer.innerHTML = `
        <div class="certificate" id="certificate">
            <div class="certificate-title">Phishing Awareness Certificate</div>
            <div class="certificate-subtitle">of Completion</div>
            <div class="certificate-recipient">${escapeHtml(certificateData.username)}</div>
            <div class="certificate-details">
                <p>For successfully completing the Phishing Awareness Training Program</p>
                <p>Demonstrating proficiency in identifying and preventing phishing attacks</p>
                <p>Issued on: ${certificateData.issued_date}</p>
            </div>
            <div class="certificate-id">Certificate ID: ${certificateData.certificate_id}</div>
        </div>
        <button class="btn btn-success mt-3" onclick="downloadCertificate()">Download Certificate (PNG)</button>
    `;
}

// Download certificate as PNG
async function downloadCertificate() {
    const certificate = document.getElementById('certificate');
    if (!certificate) return;
    
    try {
        const canvas = await html2canvas(certificate, {
            scale: 2,
            backgroundColor: '#ffffff',
            logging: false
        });
        
        const link = document.createElement('a');
        link.download = `phishing_certificate_${Date.now()}.png`;
        link.href = canvas.toDataURL();
        link.click();
        
        showNotification('Certificate downloaded!', 'success');
    } catch (error) {
        console.error('Error downloading certificate:', error);
        showNotification('Error downloading certificate', 'danger');
    }
}

// ==================== DASHBOARD FUNCTIONS ====================

// Load dashboard data
async function loadDashboard() {
    try {
        const response = await fetch('/api/user/profile');
        if (response.ok) {
            const data = await response.json();
            updateDashboardUI(data);
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Update dashboard UI
function updateDashboardUI(data) {
    // Update stats
    const elements = {
        username: data.username,
        securityScore: Math.round(data.security_score) + '%',
        totalPoints: data.total_points,
        scenariosCompleted: data.scenarios_completed,
        certStatus: data.certificate_issued ? '✓ Earned' : 'Not Yet'
    };
    
    for (const [key, value] of Object.entries(elements)) {
        const element = document.getElementById(key);
        if (element) element.textContent = value;
    }
    
    // Update progress
    const progress = calculateProgress(data);
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
        progressFill.textContent = `${Math.round(progress)}% Complete`;
    }
}

// Calculate overall progress
function calculateProgress(data) {
    let progress = 0;
    if (data.quiz_completed) progress += 40;
    if (data.scenarios_completed >= 5) progress += 30;
    if (data.security_score >= 70) progress += 30;
    return progress;
}

// ==================== INITIALIZATION ====================

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = element.dataset.tooltip;
            tooltip.style.position = 'absolute';
            tooltip.style.background = '#333';
            tooltip.style.color = 'white';
            tooltip.style.padding = '0.5rem';
            tooltip.style.borderRadius = '5px';
            tooltip.style.fontSize = '0.875rem';
            tooltip.style.zIndex = '1000';
            
            const rect = element.getBoundingClientRect();
            tooltip.style.top = `${rect.top - 30}px`;
            tooltip.style.left = `${rect.left}px`;
            
            document.body.appendChild(tooltip);
            
            element.addEventListener('mouseleave', () => {
                tooltip.remove();
            }, { once: true });
        });
    });
}

// Initialize forms
function initForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    });
}

// Modal handling
function initModals() {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modals.forEach(modal => {
                modal.style.display = 'none';
            });
        });
    });
    
    window.addEventListener('click', (e) => {
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
}

// Event listeners for common elements
document.addEventListener('DOMContentLoaded', () => {
    initTooltips();
    initForms();
    initModals();
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Export functions for use in HTML
window.login = login;
window.register = register;
window.logout = logout;
window.startQuiz = startQuiz;
window.selectAnswer = selectAnswer;
window.nextQuestion = nextQuestion;
window.previousQuestion = previousQuestion;
window.submitQuiz = submitQuiz;
window.viewScenario = viewScenario;
window.submitScenarioAnswer = submitScenarioAnswer;
window.generateCertificate = generateCertificate;
window.downloadCertificate = downloadCertificate;
window.loadDashboard = loadDashboard;
window.showNotification = showNotification;
window.copyToClipboard = copyToClipboard;