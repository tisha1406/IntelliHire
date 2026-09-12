def resolve_interview_mode(campaign: dict) -> str:
    """
    Resolves the canonical mode_id from a campaign document.
    
    Provides backward compatibility for legacy campaigns (which may use 'interview_mode')
    and handles the current frontend schema which nests the type inside 'interview_settings.type'.
    
    Raises:
        ValueError: If no valid mode configuration is found.
    """
    # 1. Check legacy/direct assignment
    mode = campaign.get("interview_mode")
    
    # 2. Fallback to nested schema
    if not mode:
        settings = campaign.get("interview_settings", {})
        if isinstance(settings, dict):
            mode = settings.get("type")
            
    if not mode or not str(mode).strip():
        raise ValueError("Campaign is missing both 'interview_mode' and 'interview_settings.type'")
        
    # 3. Normalize to mode_id format (e.g. "Technical" -> "technical", "AI & Data Science" -> "ai_&_data_science")
    # For now, we assume simple lowercasing and replacing spaces with underscores.
    mode_id = str(mode).strip().lower().replace(" ", "_")
    
    return mode_id
