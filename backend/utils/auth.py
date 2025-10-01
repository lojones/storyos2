"""
Authentication module for StoryOS v2
Handles user login, registration, and session management with session state persistence
"""

import hashlib
from backend.utils.streamlit_shim import st
from typing import Optional, Dict, Any
from backend.utils.db_utils import get_db_manager
from backend.logging_config import get_logger, StoryOSLogger
import time
import secrets
import json
from urllib.parse import urlencode

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    logger = get_logger("auth")
    logger.debug("Hashing password")
    return hashlib.sha256(password.encode()).hexdigest()

def generate_auth_token(user_data: Dict[str, Any]) -> str:
    """Generate a secure authentication token for persistent login"""
    logger = get_logger("auth")
    try:
        # Create a secure token with user data and timestamp
        token_data = {
            'user_id': user_data.get('user_id'),
            'role': user_data.get('role'),
            'timestamp': int(time.time())
        }
        
        # Generate a random salt and hash the token data
        salt = secrets.token_hex(16)
        token_content = json.dumps(token_data, sort_keys=True)
        token_hash = hashlib.sha256((token_content + salt).encode()).hexdigest()
        
        # Combine salt and hash for the final token
        full_token = f"{salt}:{token_hash}:{token_content}"
        
        logger.debug(f"Generated auth token for user: {user_data.get('user_id')}")
        return full_token
        
    except Exception as e:
        logger.error(f"Error generating auth token: {str(e)}")
        StoryOSLogger.log_error_with_context("auth", e, {
            "action": "generate_auth_token",
            "user_id": user_data.get('user_id', 'unknown')
        })
        return ""

def validate_auth_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate an authentication token and return user data if valid"""
    logger = get_logger("auth")
    
    if not token:
        return None
    
    try:
        # Parse the token
        parts = token.split(':', 2)
        if len(parts) != 3:
            logger.debug("Invalid token format")
            return None
        
        salt, token_hash, token_content = parts
        
        # Verify the hash
        expected_hash = hashlib.sha256((token_content + salt).encode()).hexdigest()
        if token_hash != expected_hash:
            logger.debug("Token hash verification failed")
            return None
        
        # Parse the token data
        token_data = json.loads(token_content)
        
        # Check token age (expire after 30 days)
        token_age = time.time() - token_data.get('timestamp', 0)
        if token_age > 30 * 24 * 60 * 60:  # 30 days in seconds
            logger.debug("Token expired")
            return None
        
        # Verify user still exists in database
        db = get_db_manager()
        if not db.is_connected():
            logger.warning("Database not connected during token validation")
            return None
        
        user = db.get_user(token_data.get('user_id'))
        if not user:
            logger.debug(f"User no longer exists for token: {token_data.get('user_id')}")
            return None
        
        logger.debug(f"Token validated successfully for user: {user.get('user_id')}")
        return user
        
    except Exception as e:
        logger.debug(f"Error validating auth token: {str(e)}")
        return None

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    logger = get_logger("auth")
    logger.debug("Verifying password hash")
    return hash_password(password) == hashed_password

def save_login_to_session(user_data: Dict[str, Any]) -> None:
    """Save user login data to session state with persistent auth token"""
    logger = get_logger("auth")
    try:
        user_id = user_data.get('user_id', '')
        user_role = user_data.get('role', 'user')
        
        # Store user data in session state
        st.session_state["storyos_user_id"] = user_id
        st.session_state["storyos_user_role"] = user_role
        st.session_state["storyos_logged_in"] = True
        
        # Generate and store auth token for persistence
        auth_token = generate_auth_token(user_data)
        if auth_token:
            st.session_state["storyos_auth_token"] = auth_token
            
            # Set query parameter for URL-based persistence
            try:
                # Try newer Streamlit API first
                st.query_params["auth"] = auth_token
            except Exception:
                try:
                    # Fallback to older API
                    query_params = dict(st.experimental_get_query_params())
                    query_params["auth"] = [auth_token]
                    st.experimental_set_query_params(**query_params)
                except Exception as query_error:
                    logger.debug(f"Could not set query params: {query_error}")
            
            logger.info(f"Session saved with persistent auth for user: {user_id} with role: {user_role}")
        else:
            logger.warning(f"Failed to generate auth token for user: {user_id}")
        
    except Exception as e:
        StoryOSLogger.log_error_with_context("auth", e, {"action": "save_login_to_session", "user_data": user_data})
        st.error(f"Error saving login to session: {str(e)}")

def load_login_from_session() -> Optional[Dict[str, Any]]:
    """Load user login data from session state with persistent auth support"""
    logger = get_logger("auth")
    try:
        # First check if already logged in via session state
        logged_in = st.session_state.get("storyos_logged_in", False)
        logger.debug(f"Session login status: {logged_in}")
        
        if logged_in:
            user_id = st.session_state.get("storyos_user_id")
            user_role = st.session_state.get("storyos_user_role")
            if user_id:
                logger.debug(f"Loading session for user: {user_id} with role: {user_role}")
                return {
                    'user_id': user_id,
                    'role': user_role or 'user'
                }
            else:
                logger.warning("Session marked as logged in but no user_id found")
        
        # If not logged in via session state, check for persistent auth token
        auth_token = None
        
        # Try to get auth token from query params
        try:
            # Try newer Streamlit API first
            auth_token = st.query_params.get("auth")
        except Exception:
            try:
                # Fallback to older API
                query_params = st.experimental_get_query_params()
                auth_token_list = query_params.get("auth", [])
                auth_token = auth_token_list[0] if auth_token_list else None
            except Exception as query_error:
                logger.debug(f"Could not get query params: {query_error}")
        
        # If no token in URL, check session state for stored token
        if not auth_token:
            auth_token = st.session_state.get("storyos_auth_token")
        
        if auth_token:
            logger.debug("Found auth token, attempting validation")
            user_data = validate_auth_token(auth_token)
            if user_data:
                # Restore session state from valid token
                st.session_state["storyos_user_id"] = user_data['user_id']
                st.session_state["storyos_user_role"] = user_data['role']
                st.session_state["storyos_logged_in"] = True
                st.session_state["storyos_auth_token"] = auth_token
                
                logger.info(f"Restored session from persistent auth for user: {user_data['user_id']}")
                StoryOSLogger.log_user_action(user_data['user_id'], "session_restored_from_token", {
                    "role": user_data['role']
                })
                
                return user_data
            else:
                logger.debug("Auth token validation failed, clearing stale token")
                # Clear invalid token from session state
                st.session_state.pop("storyos_auth_token", None)
        
    except Exception as e:
        StoryOSLogger.log_error_with_context("auth", e, {"action": "load_login_from_session"})
        st.error(f"Error loading login from session: {str(e)}")
    
    return None

def clear_login_from_session() -> None:
    """Clear user login data from session state and persistent auth"""
    logger = get_logger("auth")
    try:
        user_id = st.session_state.get("storyos_user_id", "unknown")
        
        # Clear session state
        st.session_state.pop("storyos_user_id", None)
        st.session_state.pop("storyos_user_role", None)
        st.session_state.pop("storyos_logged_in", None)
        st.session_state.pop("storyos_auth_token", None)
        
        # Clear auth token from URL query params
        try:
            # Try newer Streamlit API first
            if "auth" in st.query_params:
                query_params = dict(st.query_params)
                del query_params["auth"]
                st.query_params.clear()
                st.query_params.update(query_params)
        except Exception:
            try:
                # Fallback to older API
                query_params = dict(st.experimental_get_query_params())
                if "auth" in query_params:
                    del query_params["auth"]
                    st.experimental_set_query_params(**query_params)
            except Exception as query_error:
                logger.debug(f"Could not clear query params: {query_error}")
        
        logger.info(f"Session and persistent auth cleared for user: {user_id}")
        
    except Exception as e:
        StoryOSLogger.log_error_with_context("auth", e, {"action": "clear_login_from_session"})
        st.error(f"Error clearing login from session: {str(e)}")

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with username and password"""
    logger = get_logger("auth")
    start_time = time.time()
    
    logger.info(f"Authentication attempt for user: {username}")
    
    db = get_db_manager()
    
    if not db.is_connected():
        logger.error("Database connection failed during authentication")
        st.error("Database connection failed")
        return None
    
    try:
        # Get user from database
        user = db.get_user(username)
        if not user:
            logger.warning(f"Authentication failed - user not found: {username}")
            StoryOSLogger.log_user_action(username, "login_attempt_failed", {"reason": "user_not_found"})
            return None
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            logger.warning(f"Authentication failed - invalid password for user: {username}")
            StoryOSLogger.log_user_action(username, "login_attempt_failed", {"reason": "invalid_password"})
            return None
        
        # Success
        duration = time.time() - start_time
        logger.info(f"Authentication successful for user: {username} (role: {user.get('role', 'user')})")
        StoryOSLogger.log_user_action(username, "login_successful", {"role": user.get('role', 'user')})
        StoryOSLogger.log_performance("auth", "authenticate_user", duration, {"username": username})
        
        return user
        
    except Exception as e:
        StoryOSLogger.log_error_with_context("auth", e, {"action": "authenticate_user", "username": username})
        return None

def create_user(username: str, password: str, role: str = 'user') -> bool:
    """Create a new user"""
    logger = get_logger("auth")
    start_time = time.time()
    
    logger.info(f"Creating new user: {username} with role: {role}")
    
    db = get_db_manager()
    
    if not db.is_connected():
        logger.error("Database connection failed during user creation")
        st.error("Database connection failed")
        return False
    
    try:
        # Check if user already exists
        if db.user_exists(username):
            logger.warning(f"User creation failed - user already exists: {username}")
            StoryOSLogger.log_user_action(username, "user_creation_failed", {"reason": "user_exists"})
            return False
        
        # Hash password and create user
        password_hash = hash_password(password)
        result = db.create_user(username, password_hash, role)
        
        duration = time.time() - start_time
        
        if result:
            logger.info(f"User created successfully: {username} with role: {role}")
            StoryOSLogger.log_user_action(username, "user_created", {"role": role})
            StoryOSLogger.log_performance("auth", "create_user", duration, {"username": username, "role": role})
        else:
            logger.error(f"User creation failed for unknown reason: {username}")
            StoryOSLogger.log_user_action(username, "user_creation_failed", {"reason": "database_error"})
        
        return result
        
    except Exception as e:
        StoryOSLogger.log_error_with_context("auth", e, {"action": "create_user", "username": username, "role": role})
        return False

def is_first_run() -> bool:
    """Check if this is the first run (no users in database)"""
    logger = get_logger("auth")
    db = get_db_manager()
    
    if not db.is_connected():
        logger.error("Database connection failed during first run check")
        return False
    
    try:
        user_count = db.get_user_count()
        is_first = user_count == 0
        logger.info(f"First run check: {is_first} (user count: {user_count})")
        return is_first
        
    except Exception as e:
        StoryOSLogger.log_error_with_context("auth", e, {"action": "is_first_run"})
        return False

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current logged-in user from session state"""
    logger = get_logger("auth")
    
    # First check session state
    if 'user' in st.session_state:
        user = st.session_state.user
        logger.debug(f"Current user from session state: {user.get('user_id', 'unknown')}")
        return user
    
    # Then check session persistence
    user_data = load_login_from_session()
    if user_data:
        logger.debug(f"Attempting to restore user from persistent session: {user_data.get('user_id')}")
        # Verify user still exists in database
        db = get_db_manager()
        if db.is_connected():
            try:
                full_user = db.get_user(user_data['user_id'])
                if full_user:
                    # Update session state
                    st.session_state.user = full_user
                    logger.info(f"User session restored: {full_user.get('user_id')}")
                    return full_user
                else:
                    # User no longer exists, clear session
                    logger.warning(f"User no longer exists in database, clearing session: {user_data.get('user_id')}")
                    clear_login_from_session()
            except Exception as e:
                StoryOSLogger.log_error_with_context("auth", e, {"action": "get_current_user", "user_data": user_data})
                clear_login_from_session()
        else:
            logger.error("Database connection failed during user session check")
    
    return None

def login_user(user_data: Dict[str, Any]) -> None:
    """Log in a user (save to session state)"""
    logger = get_logger("auth")
    user_id = user_data.get('user_id', 'unknown')
    
    logger.info(f"Logging in user: {user_id}")
    st.session_state.user = user_data
    save_login_to_session(user_data)
    
    StoryOSLogger.log_user_action(user_id, "user_logged_in", {"role": user_data.get('role', 'user')})

def logout_user() -> None:
    """Log out the current user"""
    logger = get_logger("auth")
    
    user_id = "unknown"
    if 'user' in st.session_state:
        user_id = st.session_state.user.get('user_id', 'unknown')
        del st.session_state.user
    
    clear_login_from_session()
    logger.info(f"User logged out: {user_id}")
    StoryOSLogger.log_user_action(user_id, "user_logged_out")

def is_admin() -> bool:
    """Check if current user is an admin"""
    logger = get_logger("auth")
    user = get_current_user()
    is_admin_user = user is not None and user.get('role') == 'admin'
    
    if user:
        logger.debug(f"Admin check for user {user.get('user_id')}: {is_admin_user}")
    else:
        logger.debug("Admin check: No user logged in")
    
    return is_admin_user

def require_auth() -> Optional[Dict[str, Any]]:
    """Require authentication, return user data if authenticated, None otherwise"""
    return get_current_user()

def require_admin() -> Optional[Dict[str, Any]]:
    """Require admin authentication, return user data if admin, None otherwise"""
    user = get_current_user()
    if user and user.get('role') == 'admin':
        return user
    return None

def show_login_form() -> bool:
    """
    Show login/registration form
    Returns True if user successfully logged in, False otherwise
    """
    logger = get_logger("auth")
    logger.debug("Showing login form")
    
    st.header("Welcome to StoryOS v2")
    
    # Check if this is first run
    if is_first_run():
        st.info("👋 Welcome! This appears to be your first time running StoryOS. Please create an admin account.")
        
        with st.form("first_run_form"):
            st.subheader("Create Admin Account")
            username = st.text_input("Admin Username")
            password = st.text_input("Admin Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Admin Account")
            
            if submitted:
                logger.info(f"First-run admin creation attempt for username: {username}")
                if not username or not password:
                    logger.warning("First-run admin creation failed: missing username or password")
                    st.error("Please provide both username and password")
                elif password != confirm_password:
                    logger.warning("First-run admin creation failed: passwords do not match")
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    logger.warning("First-run admin creation failed: password too short")
                    st.error("Password must be at least 6 characters long")
                else:
                    if create_user(username, password, 'admin'):
                        logger.info(f"First-run admin account created successfully: {username}")
                        st.success("Admin account created successfully! Please log in.")
                        st.rerun()
                    else:
                        logger.error(f"Failed to create first-run admin account: {username}")
                        st.error("Failed to create admin account")
        
        return False
    
    # Regular login form
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                logger.info(f"Login form submitted for username: {username}")
                if not username or not password:
                    logger.warning("Login attempt failed: missing username or password")
                    st.error("Please provide both username and password")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        login_user(user)
                        logger.info(f"Login successful, redirecting user: {user['user_id']}")
                        st.success(f"Welcome back, {user['user_id']}!")
                        st.rerun()
                    else:
                        logger.warning(f"Login form: authentication failed for username: {username}")
                        st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_new_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                logger.info(f"Registration form submitted for username: {new_username}")
                if not new_username or not new_password:
                    logger.warning("Registration attempt failed: missing username or password")
                    st.error("Please provide both username and password")
                elif new_password != confirm_new_password:
                    logger.warning("Registration attempt failed: passwords do not match")
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    logger.warning("Registration attempt failed: password too short")
                    st.error("Password must be at least 6 characters long")
                else:
                    if create_user(new_username, new_password, 'user'):
                        logger.info(f"Registration successful for username: {new_username}")
                        st.success("Account created successfully! Please log in.")
                        st.rerun()
                    else:
                        logger.warning(f"Registration failed for username: {new_username}")
                        st.error("Username already exists or registration failed")
    
    return False