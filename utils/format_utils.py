from datetime import datetime
import pytz
import tzlocal

def human_readable_datetime(dt_str: str) -> str:
    """
    Convert an ISO datetime string to a human-readable format in EST (US Eastern Time),
    or local timezone if EST is not available.
    Returns the original string if parsing fails.
    """
    if not dt_str or dt_str == 'Unknown':
        return 'Unknown'
    try:
        dt = datetime.fromisoformat(dt_str)
        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        try:
            eastern = pytz.timezone('US/Eastern')
            dt_est = dt.astimezone(eastern)
        except Exception:
            # Fallback to local timezone
            local_tz = tzlocal.get_localzone()
            dt_est = dt.astimezone(local_tz)
        return dt_est.strftime('%b %d, %Y, %I:%M %p %Z')
    except Exception:
        return dt_str
