export interface Event {
  date: string;
  title: string;
}

export interface PersonEvents {
  name: string;
  events: Event[];
  daysSinceLastSeen: number;
  alertLevel: string;
  colorCodingDisabled: boolean;
}

export interface NameConflict {
  firstName: string;
  variations: string[];
}

export interface FriendsResponse {
  friends: PersonEvents[];
  nameConflicts: NameConflict[];
}