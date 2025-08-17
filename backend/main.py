from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import importlib.util
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

NICKNAME_MAP = {
    'bons': 'bonnie',
    'na': 'nanut', 
    'ed': 'edward'
}

def load_disabled_color_coding():
    """Load the list of friends with disabled color coding from friend_preferences.py"""
    try:
        from friend_preferences import DISABLED_COLOR_CODING
        return DISABLED_COLOR_CODING
    except ImportError:
        print("⚠️  friend_preferences.py not found, using empty list")
        return []

def save_disabled_color_coding(disabled_list):
    """Save the updated list to friend_preferences.py"""
    content = f"""# Friend Minder Preferences
# List of friends for whom color coding should be disabled
# Add names here for friends you're OK not seeing regularly (e.g., hometown friends)

DISABLED_COLOR_CODING = {disabled_list!r}

# You can edit this file directly or use the toggle in the web interface
# Changes to this file require restarting the backend server"""
    
    with open('friend_preferences.py', 'w') as f:
        f.write(content)

def calculate_alert_level(days_since_last_seen: int, color_disabled: bool) -> str:
    """Calculate alert level based on days since last seen"""
    if color_disabled:
        return "normal"
    elif days_since_last_seen >= 180:  # 6 months
        return "urgent"
    elif days_since_last_seen >= 90:   # 3 months
        return "warning"
    else:
        return "normal"

class Event(BaseModel):
    date: str
    title: str

class PersonEvents(BaseModel):
    name: str
    events: List[Event]
    daysSinceLastSeen: int
    alertLevel: str  # "normal", "warning", "urgent"
    colorCodingDisabled: bool

class NameConflict(BaseModel):
    firstName: str
    variations: List[str]

class FriendsResponse(BaseModel):
    friends: List[PersonEvents]
    nameConflicts: List[NameConflict]

class ToggleColorCodingRequest(BaseModel):
    personName: str
    disabled: bool

def normalize_name(name: str) -> str:
    """Normalize name by converting to lowercase and handling nicknames"""
    name = name.strip().lower()
    return NICKNAME_MAP.get(name, name)

def consolidate_names(person_events: Dict[str, List[Event]]) -> tuple[Dict[str, List[Event]], List[NameConflict]]:
    """
    Consolidate names where first name only and first+last name likely refer to same person.
    Returns consolidated events and list of conflicts that need manual resolution.
    """
    # Group names by first name
    first_name_groups: Dict[str, List[str]] = {}
    
    for full_name in person_events.keys():
        first_name = full_name.split()[0]
        if first_name not in first_name_groups:
            first_name_groups[first_name] = []
        first_name_groups[first_name].append(full_name)
    
    consolidated_events: Dict[str, List[Event]] = {}
    name_conflicts: List[NameConflict] = []
    
    for first_name, name_variations in first_name_groups.items():
        if len(name_variations) == 1:
            # Only one variation, keep as is
            name = name_variations[0]
            consolidated_events[name] = person_events[name]
        else:
            # Multiple variations - check for conflicts
            single_names = [n for n in name_variations if len(n.split()) == 1]
            full_names = [n for n in name_variations if len(n.split()) > 1]
            
            if len(full_names) <= 1:
                # No conflict: either multiple single names or one full name
                # Consolidate under the full name if available, otherwise use first single name
                primary_name = full_names[0] if full_names else single_names[0]
                
                # Combine all events
                all_events = []
                for name_var in name_variations:
                    all_events.extend(person_events[name_var])
                
                consolidated_events[primary_name] = all_events
                print(f"✅ Consolidated {name_variations} -> {primary_name}")
            else:
                # Conflict: multiple different full names with same first name
                # This needs manual resolution
                name_conflicts.append(NameConflict(
                    firstName=first_name,
                    variations=name_variations
                ))
                
                # For now, keep them separate
                for name_var in name_variations:
                    consolidated_events[name_var] = person_events[name_var]
                
                print(f"⚠️  Name conflict detected for '{first_name}': {name_variations}")
    
    return consolidated_events, name_conflicts

def parse_event_title(title: str) -> List[str]:
    """Parse event title to extract person names. Returns empty list if format doesn't match."""
    # Pattern: "<Activity> w/ <person1>, <person2>, <etc>"
    match = re.search(r'w/\s*(.+)', title, re.IGNORECASE)
    if not match:
        return []
    
    people_str = match.group(1)
    # Split by comma and clean up
    people = [normalize_name(person.strip()) for person in people_str.split(',')]
    return people

def get_google_calendar_service():
    """Authenticate and return Google Calendar service"""
    creds = None
    
    # Load existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

@app.get("/api/friends", response_model=FriendsResponse)
async def get_friends():
    try:
        print("📅 Connecting to Google Calendar...")
        service = get_google_calendar_service()
        
        # Get calendar list to find "Social" calendar
        print("📋 Fetching calendar list...")
        calendar_list = service.calendarList().list().execute()
        social_calendar_id = None
        
        print(f"📅 Found {len(calendar_list.get('items', []))} calendars:")
        for calendar in calendar_list['items']:
            calendar_name = calendar['summary']
            print(f"  - {calendar_name}")
            if calendar_name.lower() == 'social':
                social_calendar_id = calendar['id']
                print(f"✅ Found Social calendar: {social_calendar_id}")
                break
        
        if not social_calendar_id:
            print("❌ Social calendar not found")
            raise HTTPException(status_code=404, detail="Social calendar not found. Please create a calendar named 'Social'")
        
        # Get events from past 12 months
        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=360)
        
        print(f"📅 Fetching events from {six_months_ago.date()} to {now.date()}...")
        events_result = service.events().list(
            calendarId=social_calendar_id,
            timeMin=six_months_ago.isoformat() + 'Z',
            timeMax=now.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"📋 Found {len(events)} total events")
        
        # Group events by person
        person_events: Dict[str, List[Event]] = {}
        valid_events = 0
        
        for event in events:
            title = event.get('summary', '')
            start = event.get('start', {})
            
            # Skip events that don't match the expected format
            people = parse_event_title(title)
            if not people:
                print(f"⏭️  Skipping event (wrong format): {title}")
                continue
            
            valid_events += 1
            print(f"✅ Processing event: {title} -> {people}")
            
            # Get date
            date_str = start.get('date') or start.get('dateTime', '')
            if not date_str:
                continue
                
            # Parse date
            try:
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"❌ Date parsing error for {title}: {e}")
                continue
            
            for person in people:
                if person not in person_events:
                    person_events[person] = []
                
                person_events[person].append(Event(
                    date=formatted_date,
                    title=title
                ))
        
        print(f"📊 Processed {valid_events} valid events for {len(person_events)} people")
        
        # Consolidate names before creating final result
        print("🔗 Consolidating names...")
        consolidated_events, name_conflicts = consolidate_names(person_events)
        
        # Load color coding preferences
        disabled_color_coding = load_disabled_color_coding()
        
        # Sort events for each person by date (most recent first) and keep only top 3
        result = []
        today = datetime.now().date()
        
        for person, events in consolidated_events.items():
            sorted_events = sorted(events, key=lambda x: x.date, reverse=True)[:3]
            
            # Calculate days since last seen
            if sorted_events:
                last_seen_date = datetime.strptime(sorted_events[0].date, '%Y-%m-%d').date()
                days_since_last_seen = (today - last_seen_date).days
            else:
                days_since_last_seen = 999  # Very high number if no events
            
            # Check if color coding is disabled for this person
            color_disabled = person.title() in disabled_color_coding
            alert_level = calculate_alert_level(days_since_last_seen, color_disabled)
            
            result.append(PersonEvents(
                name=person.title(),
                events=sorted_events,
                daysSinceLastSeen=days_since_last_seen,
                alertLevel=alert_level,
                colorCodingDisabled=color_disabled
            ))
            print(f"👤 {person.title()}: {len(sorted_events)} recent events, {days_since_last_seen} days ago, {alert_level}")
        
        # Sort people by most recent event date
        result.sort(key=lambda x: x.events[0].date if x.events else '', reverse=True)
        
        print(f"✅ Returning data for {len(result)} people with {len(name_conflicts)} conflicts")
        return FriendsResponse(
            friends=result,
            nameConflicts=name_conflicts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/toggle-color-coding")
async def toggle_color_coding(request: ToggleColorCodingRequest):
    try:
        disabled_list = load_disabled_color_coding()
        
        if request.disabled:
            # Add person to disabled list if not already there
            if request.personName not in disabled_list:
                disabled_list.append(request.personName)
                print(f"✅ Disabled color coding for {request.personName}")
        else:
            # Remove person from disabled list if present
            if request.personName in disabled_list:
                disabled_list.remove(request.personName)
                print(f"✅ Enabled color coding for {request.personName}")
        
        # Save updated preferences
        save_disabled_color_coding(disabled_list)
        
        return {"success": True, "message": f"Color coding {'disabled' if request.disabled else 'enabled'} for {request.personName}"}
        
    except Exception as e:
        print(f"❌ Error toggling color coding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)