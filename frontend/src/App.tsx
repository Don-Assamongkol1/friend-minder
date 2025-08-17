import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PersonEvents, FriendsResponse, NameConflict } from './types';
import './App.css';

type SortOption = 'name-asc' | 'name-desc' | 'recent-first' | 'recent-last';
type ViewFilter = 'active' | 'disabled';

const App: React.FC = () => {
  const [friends, setFriends] = useState<PersonEvents[]>([]);
  const [sortedFriends, setSortedFriends] = useState<PersonEvents[]>([]);
  const [nameConflicts, setNameConflicts] = useState<NameConflict[]>([]);
  const [showConflictDialog, setShowConflictDialog] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('recent-first');
  const [viewFilter, setViewFilter] = useState<ViewFilter>('active');

  useEffect(() => {
    fetchFriends();
  }, []);

  useEffect(() => {
    sortFriends();
  }, [friends, sortBy, viewFilter]);

  const fetchFriends = async (): Promise<void> => {
    try {
      setLoading(true);
      const response = await axios.get<FriendsResponse>('http://localhost:8000/api/friends');
      setFriends(response.data.friends);
      setNameConflicts(response.data.nameConflicts);
      setShowConflictDialog(response.data.nameConflicts.length > 0);
      setError(null);
    } catch (err) {
      setError('Failed to fetch friends data. Make sure the backend is running.');
      console.error('Error fetching friends:', err);
    } finally {
      setLoading(false);
    }
  };

  const sortFriends = (): void => {
    // First filter based on view preference
    const filtered = friends.filter(friend => {
      if (viewFilter === 'active') {
        return !friend.colorCodingDisabled;
      } else {
        return friend.colorCodingDisabled;
      }
    });

    // Then sort the filtered results
    const sorted = filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name-asc':
          return a.name.localeCompare(b.name);
        case 'name-desc':
          return b.name.localeCompare(a.name);
        case 'recent-first':
          const aDate = a.events[0]?.date || '0000-00-00';
          const bDate = b.events[0]?.date || '0000-00-00';
          return bDate.localeCompare(aDate);
        case 'recent-last':
          const aDateLast = a.events[0]?.date || '9999-99-99';
          const bDateLast = b.events[0]?.date || '9999-99-99';
          return aDateLast.localeCompare(bDateLast);
        default:
          return 0;
      }
    });
    setSortedFriends(sorted);
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const toggleColorCoding = async (personName: string, disabled: boolean): Promise<void> => {
    try {
      await axios.post('http://localhost:8000/api/toggle-color-coding', {
        personName: personName,
        disabled: disabled
      });
      
      // Refresh the data to get updated color coding status
      await fetchFriends();
    } catch (err) {
      console.error('Error toggling color coding:', err);
      // Could add a toast notification here
    }
  };

  const getCardClassName = (friend: PersonEvents): string => {
    let className = "friend-row";
    if (!friend.colorCodingDisabled) {
      if (friend.alertLevel === "urgent") {
        className += " alert-urgent";
      } else if (friend.alertLevel === "warning") {
        className += " alert-warning";
      }
    }
    return className;
  };

  const formatDaysText = (days: number): string => {
    if (days === 0) return "Today";
    if (days === 1) return "1 day ago";
    if (days < 30) return `${days} days ago`;
    if (days < 60) return "1 month ago";
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  };

  if (loading) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>Friend Minder</h1>
        </header>
        <div className="loading">Loading your social connections...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>Friend Minder</h1>
        </header>
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchFriends}>Retry</button>
        </div>
      </div>
    );
  }

  const ConflictDialog: React.FC = () => (
    <div className="dialog-overlay">
      <div className="dialog">
        <h2>Name Conflicts Detected</h2>
        <p>The following names might refer to different people and need manual resolution:</p>
        
        <div className="conflicts-list">
          {nameConflicts.map((conflict, index) => (
            <div key={index} className="conflict-item">
              <h3>First name: "{conflict.firstName}"</h3>
              <ul>
                {conflict.variations.map((variation, varIndex) => (
                  <li key={varIndex}>{variation}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        
        <div className="dialog-instructions">
          <h3>To resolve these conflicts:</h3>
          <ol>
            <li>Update the <code>NICKNAME_MAP</code> in <code>backend/main.py</code></li>
            <li>Add entries to map variations to a single canonical name</li>
            <li>Restart the backend server</li>
          </ol>
          <p>
            <strong>Example:</strong> If "Jack Zhang" and "Jack Kim" are different people, no action needed. 
            If "Jack" and "Jack Zhang" are the same person, add: <code>'jack': 'jack zhang'</code>
          </p>
        </div>
        
        <button 
          className="dialog-close"
          onClick={() => setShowConflictDialog(false)}
        >
          Got it, I'll resolve manually
        </button>
      </div>
    </div>
  );

  return (
    <div className="app">
      {showConflictDialog && <ConflictDialog />}
      
      <header className="app-header">
        <h1>Friend Minder</h1>
        <p>Track your social interactions</p>
      </header>
      
      <main className="main-content">
        {friends.length === 0 ? (
          <div className="no-data">
            <p>No social events found in your calendar.</p>
            <p>Make sure you have a "Social" calendar with events formatted as "Activity w/ Person1, Person2"</p>
          </div>
        ) : (
          <>
            <div className="controls">
              <div className="view-controls">
                <span className="view-label">View:</span>
                <button 
                  className={`view-btn ${viewFilter === 'active' ? 'active' : ''}`}
                  onClick={() => setViewFilter('active')}
                >
                  Color Coding Enabled ({friends.filter(f => !f.colorCodingDisabled).length})
                </button>
                <button 
                  className={`view-btn ${viewFilter === 'disabled' ? 'active' : ''}`}
                  onClick={() => setViewFilter('disabled')}
                >
                  Color Coding Disabled ({friends.filter(f => f.colorCodingDisabled).length})
                </button>
              </div>

              <div className="sort-controls">
                <span className="sort-label">Sort by:</span>
                <button 
                  className={`sort-btn ${sortBy === 'recent-first' ? 'active' : ''}`}
                  onClick={() => setSortBy('recent-first')}
                >
                  Most Recent
                </button>
                <button 
                  className={`sort-btn ${sortBy === 'recent-last' ? 'active' : ''}`}
                  onClick={() => setSortBy('recent-last')}
                >
                  Least Recent
                </button>
                <button 
                  className={`sort-btn ${sortBy === 'name-asc' ? 'active' : ''}`}
                  onClick={() => setSortBy('name-asc')}
                >
                  A-Z
                </button>
                <button 
                  className={`sort-btn ${sortBy === 'name-desc' ? 'active' : ''}`}
                  onClick={() => setSortBy('name-desc')}
                >
                  Z-A
                </button>
              </div>
              
              {viewFilter === 'active' && (
                <div className="color-legend">
                  <span className="legend-label">Color coding:</span>
                  <div className="legend-item">
                    <div className="legend-color warning"></div>
                    <span>3+ months</span>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color urgent"></div>
                    <span>6+ months</span>
                  </div>
                </div>
              )}
            </div>
            <div className="friends-grid">
              {sortedFriends.map((friend, index) => (
                <div key={index} className={getCardClassName(friend)}>
                  <div className="friend-info">
                    <h2 className="friend-name">{friend.name}</h2>
                    <div className="friend-meta">
                      <span className="last-seen">Last seen: {formatDaysText(friend.daysSinceLastSeen)}</span>
                      <button 
                        className={`toggle-btn ${friend.colorCodingDisabled ? 'enable' : 'disable'}`}
                        onClick={() => toggleColorCoding(friend.name, !friend.colorCodingDisabled)}
                      >
                        {friend.colorCodingDisabled ? 'Enable Color Coding' : 'Disable Color Coding'}
                      </button>
                    </div>
                  </div>
                  <div className="events-list">
                    {friend.events.map((event, eventIndex) => (
                      <div key={eventIndex} className="event-item">
                        <div className="event-title">{event.title}</div>
                        <div className="event-date">{formatDate(event.date)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default App;