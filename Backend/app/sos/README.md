# SOS Module - Frontend Integration Guide

This document outlines how the frontend should integrate with the SOS (Emergency Alert) features.

## 1. Triggering an SOS Alert (User Side)

When a user triggers an SOS, you must capture their current geolocation and send it to the backend.

- **Endpoint**: `POST /api/sos/`
- **Authentication**: Required (Attendee)
- **Content-Type**: `application/json`

### Request Payload
```json
{
  "event_id": "uuid-of-event",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "message": "Optional message (e.g., 'Medical emergency')"
}
```

### Getting User Location
The SOS feature relies on the browser's Geolocation API (`navigator.geolocation`). You must request permission and handle potential errors (e.g., user denied location).

**Basic Usage:**
```javascript
if ("geolocation" in navigator) {
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      // Send to backend...
    },
    (error) => {
      console.error("Error getting location:", error.message);
      // Handle error: Default to 0,0 or prompt user to enable location
    },
    {
      enableHighAccuracy: true, // Request best possible results (GPS)
      timeout: 5000,            // Give up after 5 seconds
      maximumAge: 0             // Do not use cached position
    }
  );
} else {
  alert("Geolocation is not supported by your browser");
}
```

### Complete Example (Triggering SOS)
```javascript
async function triggerSOS() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported.");
    return;
  }

  // 1. Get Coordinates
  navigator.geolocation.getCurrentPosition(async (position) => {
    const payload = {
      event_id: "your-event-id",
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      message: "Help needed!"
    };

    // 2. Send Request to Backend
    try {
      const response = await fetch("/api/sos/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userToken}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        alert("SOS sent! Help is on the way.");
      } else {
        const err = await response.json();
        alert(`Failed to send SOS: ${err.detail}`);
      }
    } catch (e) {
      console.error("Network error:", e);
    }
  }, (error) => {
    // Handle location errors
    switch(error.code) {
      case error.PERMISSION_DENIED:
        alert("Please enable location services to send an SOS.");
        break;
      case error.POSITION_UNAVAILABLE:
        alert("Location information is unavailable.");
        break;
      case error.TIMEOUT:
        alert("The request to get user location timed out.");
        break;
      default:
        alert("An unknown error occurred.");
        break;
    }
  }, { enableHighAccuracy: true });
}
```

---

## 2. Handling Notifications (Admin Side)

Admins and Organizers receive real-time notifications when an SOS is triggered via Socket.IO.

- **Socket Namespace**: `/` (default)
- **Room**: `admin_global` (Server automatically adds Admins to this room on connect)
- **Event Name**: `sos:alert`

### Socket Event Payload
The `sos:alert` event payload contains full details of the alert and the user:
```json
{
  "id": "alert-uuid",
  "event_id": "event-uuid",
  "user_id": "user-uuid",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "message": "Help needed!",
  "status": "active",
  "created_at": "ISO-8601-timestamp",
  "user": {
    "id": "user-uuid",
    "first_names": "Bob",
    "last_name": "Smith",
    "email": "bob@example.com"
  },
  "event": {
    "id": "event-uuid",
    "title": "Music Festival",
    "location": "Central Park"
  }
}
```

### Example (Socket.IO Client)
```javascript
const socket = io("https://api.yourdomain.com", {
  auth: { token: adminToken }
});

socket.on("connect", () => {
  console.log("Connected as Admin");
});

// Listen for SOS alerts
socket.on("sos:alert", (alert) => {
  console.error("SOS ALERT RECEIVED!", alert);
  // Display modal, play sound, or show notification toast
  showEmergencyModal(alert);
});
```

---

## 3. Managing Alerts (Admin/Organizer Dashboard)

### List Active Alerts for an Event
Fetch existing alerts to display in a dashboard list (e.g., if the admin refreshes the page).

- **Endpoint**: `GET /api/sos/event/{event_id}`
- **Response**: Array of alert objects (same structure as socket payload).

### Resolve an Alert
Mark an alert as handled.

- **Endpoint**: `PATCH /api/sos/{alert_id}`
- **Body**:
  ```json
  {
    "status": "resolved"
  }
  ```
- **Response**: The updated alert object.
