# StoryOS v2


# StoryOS v2 - Comprehensive Logging Implementation

## Overview
This section outlines the comprehensive server-side logging system implemented for StoryOS v2, providing detailed visibility into application operations, user actions, performance metrics, and error conditions.

## Logging Components

### 1. Central Logging Configuration (`logging_config.py`)
- **StoryOSLogger**: Main logging utility class with centralized configuration
- **ColoredFormatter**: Enhanced console output with color-coded log levels
- **File rotation**: Automatic log file management with size-based rotation
- **Performance logging**: Standardized performance metric collection
- **Error context logging**: Rich error information with contextual data

### 2. Module-Specific Logging Implementation

#### Authentication Module (`auth.py`)
- User login/logout tracking
- Authentication failure logging
- Session management monitoring
- Performance metrics for auth operations

#### Database Module (`db_utils.py`)
- MongoDB connection status and health
- CRUD operation logging with timing
- Query performance metrics
- Database error context and troubleshooting info

#### LLM Integration (`llm_utils.py`)
- API call logging with request/response details
- Streaming response monitoring
- Token usage tracking
- API error handling and retry logging

#### Game Logic (`game_logic.py`)
- Game session creation and management
- Player input processing with detailed context
- AI response generation monitoring
- Game state updates and summary management

#### Main Application (`app.py`)
- Page navigation tracking
- User action logging
- Application startup and initialization
- Route handling and error management

## Log File Structure

### Log Files Location
```
logs/
├── storyos.log           # Main application log (rotated)
├── storyos.log.1         # Previous rotation
├── storyos.log.2         # Older rotation
└── ...
```

### Log Entry Format
```
[TIMESTAMP] [LEVEL] [MODULE] MESSAGE
[2024-01-15 10:30:15,123] [INFO] [auth] User alice logged in successfully (duration: 0.15s)
[2024-01-15 10:30:16,234] [DEBUG] [db_utils] Database query executed: get_user_game_sessions (rows: 3, duration: 0.05s)
[2024-01-15 10:30:17,345] [PERF] [game_logic] process_player_input completed (duration: 2.34s, session: abc123, input_length: 45, response_length: 234)
```

## Logging Levels and Usage

### DEBUG Level
- Detailed execution flow
- Variable values and state changes
- Function entry/exit points
- Development and troubleshooting information

### INFO Level  
- User actions and workflows
- System operations and status
- Business logic milestones
- Performance summaries

### WARNING Level
- Recoverable errors and issues
- Missing optional data
- Deprecated functionality usage
- Performance concerns

### ERROR Level
- Application errors and exceptions
- Failed operations with context
- Data validation failures
- Critical system issues

### PERFORMANCE Level (Custom)
- Execution timing metrics
- Resource usage statistics
- API call performance
- Database query optimization data

## Key Logging Features

### 1. User Action Tracking
```python
StoryOSLogger.log_user_action(user_id, "player_input", {
    "session_id": session_id,
    "input_length": input_length
})
```

### 2. Performance Monitoring
```python
StoryOSLogger.log_performance("module", "operation", duration, {
    "additional_metrics": "value"
})
```

### 3. Error Context Logging
```python
StoryOSLogger.log_error_with_context("module", exception, {
    "operation": "function_name",
    "context_data": "relevant_info"
})
```

### 4. API Call Tracking
- Request/response logging for xAI Grok API
- Token usage monitoring
- Streaming response chunk tracking
- Error rate and retry analysis

## Production Monitoring Capabilities

### Server-Side Visibility
- Real-time application health monitoring
- User interaction patterns analysis
- Performance bottleneck identification
- Error trend analysis

### Debugging Support
- Detailed error context for issue resolution
- User session replay capability through logs
- Performance profiling data
- Database operation optimization insights

### Operational Metrics
- Active user sessions
- API usage patterns
- Response time distributions
- Error rates by module/operation

## Implementation Benefits

1. **Comprehensive Coverage**: Every major operation logged with context
2. **Performance Tracking**: Built-in timing and metrics collection
3. **Error Diagnostics**: Rich error information for fast issue resolution
4. **User Behavior Insights**: Detailed user action tracking
5. **Production Ready**: File rotation, structured format, appropriate levels
6. **Development Friendly**: Color-coded console output for local development

## Usage Examples

### Monitoring User Sessions
```bash
# View all user login activity
grep "logged in successfully" logs/storyos.log

# Track specific user's actions  
grep "user_id.*alice" logs/storyos.log

# Monitor game session performance
grep "PERF.*process_player_input" logs/storyos.log
```

### Error Analysis
```bash
# View all errors with context
grep "ERROR" logs/storyos.log

# Database-related issues
grep "ERROR.*db_utils" logs/storyos.log

# API call failures
grep "ERROR.*llm_utils" logs/storyos.log
```

### Performance Monitoring
```bash
# View performance metrics
grep "PERF" logs/storyos.log

# Slow operations (> 2 seconds)
grep "duration: [2-9]\." logs/storyos.log
```

This comprehensive logging system provides the detailed server-side visibility requested, enabling effective monitoring, debugging, and performance optimization of the StoryOS v2 application.


---


# Log File Rotation Configuration Guide

## Overview
The StoryOS v2 logging system now supports automatic log file rotation to prevent log files from growing too large and consuming disk space.

## Rotation Types

### 1. Size-Based Rotation (Default)
Files rotate when they reach a specified size limit:
- **Main logs**: `storyos.log` → `storyos.log.1` → `storyos.log.2` etc.
- **Error logs**: `storyos_errors.log` → `storyos_errors.log.1` etc.

### 2. Time-Based Rotation  
Files rotate daily at midnight:
- **Main logs**: `storyos.log` → `storyos.log.20250914` → `storyos.log.20250913` etc.
- **Error logs**: Always use size-based rotation (errors are typically smaller)

## Configuration Methods

### Method 1: Environment Variables (.env file)
Create or update your `.env` file:

```env
# Log rotation settings
STORYOS_LOG_LEVEL=INFO
STORYOS_LOG_TO_FILE=true
STORYOS_LOG_MAX_SIZE_MB=10          # Max file size in MB (size-based rotation)
STORYOS_LOG_BACKUP_COUNT=5          # Number of backup files to keep
STORYOS_LOG_ROTATION_TYPE=size      # 'size' or 'time'
```

### Method 2: Direct Configuration (in code)
```python
from logging_config import StoryOSLogger

# Configure logging with custom rotation settings
StoryOSLogger.setup_logging(
    log_level="INFO",
    log_to_file=True,
    max_file_size_mb=20,      # 20MB per file
    backup_count=10,          # Keep 10 backup files
    rotation_type="time"      # Daily rotation
)
```

## Configuration Options

### `max_file_size_mb` (Size-based rotation)
- **Default**: 10 MB
- **Range**: 1-100 MB recommended
- **Effect**: When log file reaches this size, it rotates

### `backup_count`
- **Default**: 5 files
- **Range**: 1-50 recommended  
- **Effect**: Number of old log files to keep
- **Total disk usage**: `max_file_size_mb * (backup_count + 1)`

### `rotation_type`
- **Options**: 
  - `"size"` - Rotate when file size limit reached
  - `"time"` - Rotate daily at midnight
- **Default**: `"size"`

## File Structure Examples

### Size-Based Rotation (10MB, 5 backups):
```
logs/
├── storyos.log              # Current log (0-10MB)
├── storyos.log.1            # Previous rotation (10MB)
├── storyos.log.2            # Older rotation (10MB)  
├── storyos.log.3            # Older rotation (10MB)
├── storyos.log.4            # Older rotation (10MB)
├── storyos.log.5            # Oldest rotation (10MB)
├── storyos_errors.log       # Current errors (0-5MB)
├── storyos_errors.log.1     # Previous error log (5MB)
└── ...
```

### Time-Based Rotation (daily):
```
logs/
├── storyos.log              # Today's log
├── storyos.log.20250914     # Yesterday's log  
├── storyos.log.20250913     # Day before yesterday
├── storyos.log.20250912     # 3 days ago
├── storyos.log.20250911     # 4 days ago
└── storyos_errors.log       # Error logs (still size-based)
```

## Recommended Settings

### Development Environment:
```env
STORYOS_LOG_LEVEL=DEBUG
STORYOS_LOG_MAX_SIZE_MB=5
STORYOS_LOG_BACKUP_COUNT=3
STORYOS_LOG_ROTATION_TYPE=size
```

### Production Environment:
```env
STORYOS_LOG_LEVEL=INFO
STORYOS_LOG_MAX_SIZE_MB=50
STORYOS_LOG_BACKUP_COUNT=10
STORYOS_LOG_ROTATION_TYPE=time
```

### High-Traffic Production:
```env
STORYOS_LOG_LEVEL=WARNING
STORYOS_LOG_MAX_SIZE_MB=100
STORYOS_LOG_BACKUP_COUNT=20
STORYOS_LOG_ROTATION_TYPE=size
```

## Monitoring Disk Usage

### Calculate Total Log Storage:
- **Size-based**: `max_file_size_mb × (backup_count + 1) × 2` (main + error logs)
- **Time-based**: `daily_log_size × backup_count × 2`

### Examples:
- **Default settings**: 10MB × 6 × 2 = ~120MB maximum
- **Production settings**: 50MB × 11 × 2 = ~1.1GB maximum

## Troubleshooting

### Logs not rotating:
1. Check file permissions on the `logs/` directory
2. Verify environment variables are loaded correctly
3. Check for file locks (close log viewers)

### Too many old files:
- Reduce `backup_count` setting
- Consider switching to time-based rotation for predictable cleanup

### Files too small/large:
- Adjust `max_file_size_mb` setting
- Monitor actual log volume over time

### Disk space issues:
- Reduce `backup_count`
- Reduce `max_file_size_mb`
- Increase log level to reduce verbosity

## Manual Log Management

### View current settings:
```bash
grep "Logging configured" logs/storyos.log
```

### Force rotation (size-based):
```python
import logging.handlers
handler = logging.getLogger().handlers[1]  # File handler
if isinstance(handler, logging.handlers.RotatingFileHandler):
    handler.doRollover()
```

### Clean old logs manually:
```bash
# Remove logs older than 7 days
find logs/ -name "*.log.*" -mtime +7 -delete
```

This rotation system ensures your log files stay manageable while preserving important debugging and monitoring information.