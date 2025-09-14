"""
Database initialization script for StoryOS v2
Creates indexes and loads initial data
"""

from utils.db_utils import get_db_manager
from game.game_logic import parse_scenario_from_markdown
from logging_config import StoryOSLogger, get_logger
import os

def _check_initialization_status(db):
    """Check which parts of database initialization are needed"""
    logger = get_logger("initialize_db")
    
    status = {
        'indexes_needed': False,
        'system_prompt_needed': False,
        'scenarios_needed': False,
        'any_needed': False
    }
    
    try:
        # Check if indexes exist by trying to get index information
        if db.db is not None:
            collections = db.db.list_collection_names()
            
            # Check for basic collections and their indexes
            required_indexes = {
                'users': ['user_id_1'],
                'scenarios': ['scenario_id_1'], 
                'active_game_sessions': ['user_id_1_created_at_-1'],
                'chats': ['game_session_id_1'],
                'system_prompts': ['active_1']
            }
            
            for collection_name, expected_indexes in required_indexes.items():
                if collection_name in collections:
                    try:
                        existing_indexes = list(db.db[collection_name].list_indexes())
                        existing_index_names = [idx['name'] for idx in existing_indexes]
                        
                        for expected_index in expected_indexes:
                            if expected_index not in existing_index_names:
                                logger.debug(f"Missing index {expected_index} in collection {collection_name}")
                                status['indexes_needed'] = True
                                break
                    except Exception as e:
                        logger.debug(f"Error checking indexes for {collection_name}: {str(e)}")
                        status['indexes_needed'] = True
                else:
                    logger.debug(f"Collection {collection_name} does not exist")
                    status['indexes_needed'] = True
        else:
            logger.warning("Database not available for index checking")
            status['indexes_needed'] = True
        
        # Check if system prompt exists
        active_prompt = db.get_active_system_prompt()
        if not active_prompt:
            logger.debug("No active system prompt found")
            status['system_prompt_needed'] = True
        
        # Check if scenarios exist
        scenarios = db.get_all_scenarios()
        if not scenarios:
            logger.debug("No scenarios found")
            status['scenarios_needed'] = True
        
        # Set overall status
        status['any_needed'] = (status['indexes_needed'] or 
                               status['system_prompt_needed'] or 
                               status['scenarios_needed'])
        
        logger.debug(f"Initialization status check: {status}")
        
    except Exception as e:
        logger.error(f"Error checking initialization status: {str(e)}")
        # If we can't check status, assume initialization is needed
        status['any_needed'] = True
        status['indexes_needed'] = True
        status['system_prompt_needed'] = True
        status['scenarios_needed'] = True
    
    return status

def initialize_database():
    """Initialize the database with indexes and initial data"""
    logger = get_logger("initialize_db")
    db = get_db_manager()
    
    if not db.is_connected():
        logger.error("Database connection failed during initialization")
        return False
    
    logger.debug("Connected to database for initialization")
    
    # Check which collections/indexes need to be created
    initialization_needed = _check_initialization_status(db)
    
    if not initialization_needed['any_needed']:
        logger.info("Database already fully initialized, skipping initialization")
        return True
    
    logger.info(f"Database initialization needed: {[k for k, v in initialization_needed.items() if v and k != 'any_needed']}")
    
    initialized_items = 0
    
    # Create indexes if needed
    if initialization_needed['indexes_needed'] and db.db is not None:
        logger.info("Creating database indexes")
        try:
            # Users collection - unique index on user_id
            try:
                db.db.users.create_index("user_id", unique=True)
                logger.info("Created index on users.user_id")
                initialized_items += 1
            except Exception as e:
                if "duplicate key error" not in str(e).lower():
                    logger.warning(f"Could not create users.user_id index: {str(e)}")
            
            # Scenarios collection - unique index on scenario_id
            try:
                db.db.scenarios.create_index("scenario_id", unique=True)
                logger.info("Created index on scenarios.scenario_id")
                initialized_items += 1
            except Exception as e:
                if "duplicate key error" not in str(e).lower():
                    logger.warning(f"Could not create scenarios.scenario_id index: {str(e)}")
            
            # Active game sessions - compound index
            try:
                db.db.active_game_sessions.create_index([("user_id", 1), ("created_at", -1)])
                logger.info("Created index on active_game_sessions")
                initialized_items += 1
            except Exception as e:
                if "duplicate key error" not in str(e).lower():
                    logger.warning(f"Could not create active_game_sessions index: {str(e)}")
            
            # Chats collection - index on game_session_id
            try:
                db.db.chats.create_index("game_session_id")
                logger.info("Created index on chats.game_session_id")
                initialized_items += 1
            except Exception as e:
                if "duplicate key error" not in str(e).lower():
                    logger.warning(f"Could not create chats.game_session_id index: {str(e)}")
            
            # System prompts - index on active flag
            try:
                db.db.system_prompts.create_index("active")
                logger.info("Created index on system_prompts.active")
                initialized_items += 1
            except Exception as e:
                if "duplicate key error" not in str(e).lower():
                    logger.warning(f"Could not create system_prompts.active index: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            StoryOSLogger.log_error_with_context("initialize_db", e, {
                "operation": "create_indexes"
            })
    elif initialization_needed['indexes_needed']:
        logger.error("Database not available for index creation")
    else:
        logger.debug("Database indexes already exist, skipping index creation")
    
    # Load system prompt if needed
    if initialization_needed['system_prompt_needed']:
        logger.info("Loading system prompt from file")
        try:
            with open('data/system_prompt.md', 'r', encoding='utf-8') as f:
                system_prompt_content = f.read()
            
            prompt_data = {
                'name': 'Default StoryOS System Prompt',
                'version': '1.0.0',
                'content': system_prompt_content,
                'active': True
            }
            
            if db.create_system_prompt(prompt_data):
                logger.info("Successfully loaded system prompt from data/system_prompt.md")
                initialized_items += 1
            else:
                logger.error("Failed to create system prompt in database")
                
        except FileNotFoundError:
            logger.warning("data/system_prompt.md not found - admin will need to create system prompt manually")
        except Exception as e:
            logger.error(f"Error loading system prompt: {str(e)}")
            StoryOSLogger.log_error_with_context("initialize_db", e, {
                "operation": "load_system_prompt"
            })
    else:
        logger.debug("System prompt already exists, skipping")
    
    # Load scenarios if needed
    if initialization_needed['scenarios_needed']:
        logger.info("Loading scenarios from file")
        try:
            with open('data/scenario_firstyearuni.md', 'r', encoding='utf-8') as f:
                scenario_content = f.read()
            
            scenario_data = parse_scenario_from_markdown(scenario_content)
            
            if scenario_data and db.create_scenario(scenario_data):
                logger.info(f"Successfully loaded scenario: {scenario_data.get('name', 'unnamed')} from data/scenario_firstyearuni.md")
                initialized_items += 1
            else:
                logger.error("Failed to create scenario in database")
                
        except FileNotFoundError:
            logger.warning("data/scenario_firstyearuni.md not found - scenarios will need to be added manually")
        except Exception as e:
            logger.error(f"Error loading scenario: {str(e)}")
            StoryOSLogger.log_error_with_context("initialize_db", e, {
                "operation": "load_scenarios"
            })
    else:
        scenarios = db.get_all_scenarios()
        logger.debug(f"Found {len(scenarios)} existing scenarios, skipping scenario loading")
    
    logger.info(f"Database initialization complete! Initialized {initialized_items} items")
    
    StoryOSLogger.log_user_action("system", "database_initialization", {
        "items_initialized": initialized_items,
        "indexes_needed": initialization_needed['indexes_needed'],
        "system_prompt_needed": initialization_needed['system_prompt_needed'],
        "scenarios_needed": initialization_needed['scenarios_needed']
    })
    
    return True

if __name__ == "__main__":
    initialize_database()