# Friend Minder

A React + TypeScript application that helps you track your social interactions by connecting to your Google Calendar.

## Upcoming Features

- In my Social Plans sheet, sort / find by person name to do an event using cmd + f. 

## Features

- Connects to your Google Calendar "Social" calendar
- Parses events formatted as "Activity w/ Person1, Person2"
- Shows the 3 most recent events with each person
- Handles nickname mapping (e.g., "Bons" → "Bonnie")
- Beautiful, responsive UI built with React and TypeScript

## Setup

### Prerequisites

- Python 3.13.0 (accessible via `python3`)
- Node.js v22.18.0
- Google Calendar API credentials

### Google Calendar API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create credentials (OAuth 2.0 Client ID for a desktop application)
5. Download the credentials JSON file
6. Save it as `backend/credentials.json`

### Running the Application

1. Clone this repository
2. Set up your Google Calendar API credentials (see above)
3. Run the application:

```bash
./start-app.sh
```

This will:
- Set up Python virtual environment and install backend dependencies
- Install frontend dependencies
- Start the FastAPI backend on http://localhost:8000
- Start the React frontend on http://localhost:3000

### Calendar Format

Create events in your "Social" calendar with this format:
- "Lunch w/ Alice, Bob" 
- "Coffee w/ Charlie"
- "Dinner w/ alice, bob" (case insensitive)

The app will ignore events that don't follow this format.

### Nickname Mapping

The app handles these nickname mappings:
- "Bons" → "Bonnie"  
- "Na" → "Nanut"
- "Ed" → "Edward"

To add more nicknames, edit the `NICKNAME_MAP` in `backend/main.py`.

## Development

- Backend: FastAPI with Python 3.13
- Frontend: React with TypeScript
- API Documentation: http://localhost:8000/docs (when backend is running)
