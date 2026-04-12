# Amity Social - Architecture Documentation

## Overview

Amity Social is a Django-based social media platform featuring posts, comments, likes, real-time chat, and notifications.

---

## Feature 1: Chat System

### Recent Chat Ordering

**Implementation:**
- Rooms are ordered by the timestamp of their latest message (most recent first)
- Uses `Coalesce(Max('messages__created_at'), F('created_at'))` annotation
- Dynamic updates via WebSocket when new messages arrive

**Key Files:**
- `accounts/views.py:room_chat()` - Orders rooms by last_message_time
- `accounts/consumers.py` - Broadcasts `room_list_update` events
- `templates/accounts/message.html` - JavaScript handles real-time reordering

**Data Flow:**
1. User sends message → WebSocket consumer
2. Consumer saves message → gets timestamp
3. Broadcasts `room_list_update` to all room participants
4. Frontend updates room list ordering

---

### Message Delivery Status

**Status Values:**
| Status | Value | Description |
|--------|-------|-------------|
| SENT | 1 | Message saved to database |
| DELIVERED | 2 | Receiver is online / message received |
| READ | 3 | Receiver opened the chat |

**Implementation:**
- `Message` model has `status`, `delivered_at`, `read_at` fields
- Status updated in real-time via WebSocket
- UI shows tick indicators:
  - Single tick (gray) = Sent
  - Double tick (gray) = Delivered
  - Double tick (blue) = Read

**Key Files:**
- `accounts/models.py:Message` - Status fields and indexes
- `accounts/consumers.py` - Status update logic
- `templates/accounts/message.html` - Status display & WebSocket handlers

**Database Indexes:**
```python
models.Index(fields=['receiver', 'status']),
models.Index(fields=['room', '-created_at']),
```

---

### Message Notifications (Offline Support)

**When Receiver is Offline:**
1. `MessageNotification` object created
2. Persistent notification stored in database
3. Notification cleared when receiver opens chat

**Key Model:**
```python
class MessageNotification(models.Model):
    user = ForeignKey(User)  # Notification recipient
    sender = ForeignKey(User)  # Message sender
    room = ForeignKey(Room)
    message = OneToOneField(Message)
    is_read = BooleanField(default=False)
```

---

## Feature 2: Comment Reply System

### Nested Comments

**Model Structure:**
```python
class Comment(models.Model):
    user = ForeignKey(User)
    post = ForeignKey(UserPosts, related_name='comments')
    parent = ForeignKey('self', null=True, related_name='replies')
    comment = TextField()
```

**Parent-Child Relationship:**
- Top-level comments: `parent = NULL`
- Replies: `parent = <parent_comment_id>`
- Each comment can have unlimited replies via `related_name='replies'`

**Key Files:**
- `list_posts/models.py:Comment` - Self-referential model
- `list_posts/views.py:add_comment()` - Handles replies with `parent_id`
- `list_posts/views.py:get_comments()` - Returns threaded structure

**API Response Structure:**
```json
{
  "comments": [
    {
      "id": 1,
      "comment": "Great post!",
      "parent_id": null,
      "is_reply": false,
      "reply_count": 2,
      "replies": [
        {
          "id": 2,
          "comment": "Thanks!",
          "parent_id": 1,
          "is_reply": true
        }
      ]
    }
  ]
}
```

---

## Database Schema

### Core Models

| Model | Purpose | Key Indexes |
|-------|---------|-------------|
| `UserPosts` | User posts | `post_slug` (unique) |
| `Like` | Post likes | `(user, post)` unique |
| `Comment` | Comments/replies | `post`, `parent` |
| `Room` | Chat rooms | `slug` (unique) |
| `Message` | Chat messages | `(receiver, status)`, `(room, -created_at)` |
| `MessageNotification` | Offline notifications | `(user, is_read)`, `(user, -created_at)` |

---

## WebSocket Architecture

### Consumer Events

| Event Type | Handler | Purpose |
|------------|---------|---------|
| `chat_message` | `handleMessage()` | Display incoming messages |
| `user_status` | `handleUserStatus()` | Online/offline updates |
| `message_status_update` | `handleStatusUpdate()` | Tick indicator updates |
| `room_list_update` | `handleRoomListUpdate()` | Reorder chat list |
| `new_notification` | - | Unread message indicator |

### Message Flow

```
Sender                    WebSocket                    Receiver
  |                         |                             |
  |-- send message -------> |                             |
  |                         |-- save_message() -----------|
  |                         |-- check online status ------|
  |                         |                             |
  |<-- status: SENT ------- |                             |
  |                         |-- if online: ---------------|
  |                         |     update DELIVERED        |
  |                         |-- mark_as_read() <----------|
  |<-- status: READ ------- |                             |
```

---

## Performance Optimizations

### Query Optimization
- `select_related()` for ForeignKey traversal
- `prefetch_related()` for ManyToMany/Reverse ForeignKey
- Database indexes on frequently queried fields
- Annotated queries for aggregations (unread counts, last message times)

### Caching
- Redis for WebSocket channel layer
- Online user status stored in Redis

---

## Real-Time Chat Fixes Applied (2026-04-11)

### Issues Fixed

**1. Redis Connection Initialization**
- Moved `self.redis_conn = redis.Redis()` to `connect()` method
- Ensures Redis is available before `set_user_status()` is called

**2. User.is_online Database Sync**
- `set_user_status()` now updates both Redis AND `User.is_online` field
- Fixes offline detection for `MessageNotification` creation

**3. Message Status Broadcast**
- Replaced sync `send_status_update()` with async `broadcast_status_updates()`
- Properly broadcasts status changes after `mark_messages_as_read()`
- Uses `asyncio.gather()` for parallel execution (prevents race conditions)

**4. Frontend Event Type Matching**
- Added `type: 'user_status'` to backend response
- Frontend now correctly identifies `user_status` events
- Added `handleRoomListUpdate()` function

**5. Multi-Room Presence Tracking (2026-04-11)**
- Users can now be connected to multiple rooms simultaneously
- Class-level `_active_connections` tracks user -> rooms mapping
- User only marked offline when ALL room connections are closed
- Room-specific presence sets: `room_{slug}_online`
- Global presence set: `global_online_users`

**6. Redis Cleanup Mechanism (2026-04-11)**
- Periodic cleanup runs every 5 minutes on first connection
- Removes stale presence sets for deleted rooms
- Management command: `python manage.py cleanup_redis_presence`
- Can be scheduled via cron for regular cleanup

**7. Missing Import Fixed**
- Added `datetime` to imports (was only used inline)
- Added `asyncio` for parallel status updates

### Files Modified
- `accounts/consumers.py` - Full rewrite of presence system
- `templates/accounts/message.html` - Event type check, room list handler
- `accounts/management/commands/cleanup_redis_presence.py` - New cleanup command

---

## Presence System Architecture

### Data Flow

```
User connects to Room A:
1. Add to global_online_users (Redis SET)
2. Add to room_A_online (Redis SET)
3. Update User.is_online = True (Database)
4. Track in ChatConsumer._active_connections[user_id] = {room_A}

User connects to Room B (while still in Room A):
1. Add to room_B_online (Redis SET)
2. Track in ChatConsumer._active_connections[user_id] = {room_A, room_B}
3. User.is_online stays True (already online)

User disconnects from Room A:
1. Remove from room_A_online
2. Remove from tracking: {room_B}
3. User still online (has Room B connection)
4. Notify Room A users: user offline

User disconnects from Room B (last connection):
1. Remove from room_B_online
2. Remove from global_online_users
3. Update User.is_online = False
4. Notify Room B users: user offline
```

### Redis Keys

| Key | Type | Purpose |
|-----|------|---------|
| `global_online_users` | SET | All currently online user IDs |
| `room_{slug}_online` | SET | User IDs online in specific room |

### Cleanup Strategy

1. **On-connect cleanup**: First connection after 5 min triggers cleanup
2. **Management command**: `python manage.py cleanup_redis_presence`
3. **Cron recommendation**: Run every 15 minutes for production

---

## Next Agent Instructions

### Backend Agent
1. **Verify Presence System**: Test that `User.is_online` toggles correctly on WebSocket connect/disconnect
2. **Test Message Status Flow**: Ensure messages transition SENT → DELIVERED → READ correctly
3. **Check Race Conditions**: Verify concurrent messages don't cause duplicate status updates (now batched with asyncio.gather)
4. **Redis Cleanup**: Consider scheduling the management command via cron
5. **Edge Case**: Multi-room presence now handled - test user in 2+ rooms simultaneously

### Frontend Agent
1. **Status Indicator Colors**: Verify tick colors (gray for sent/delivered, blue for read)
2. **Room List Updates**: Test that room list reorders when new message arrives
3. **Receiver Status**: Ensure "Online"/"Offline" text updates in real-time
4. **Error Handling**: Add reconnection logic for WebSocket drops
5. **Mobile Testing**: Verify status indicators visible on small screens

### QA Agent
1. **Presence Test Matrix**:
   - User A opens chat → User B sees "Online" immediately
   - User A closes chat → User B sees "Offline" within 2 seconds
   - Both users in same room → messages auto-mark as READ

2. **Message Status Test Matrix**:
   | Scenario | Expected Status |
   |----------|-----------------|
   | Receiver offline | SENT (single tick) |
   | Receiver online, different room | DELIVERED (double gray) |
   | Receiver in same room | READ (double blue) |
   | Receiver opens chat | READ (double blue) |

3. **Notification Test**: Verify `MessageNotification` created only when receiver offline
4. **Room Ordering**: Verify rooms sort by latest message time
5. **Comment Replies**: Test nested comments render correctly on mobile

---

## Security Considerations

- CSRF protection on comment/like endpoints
- User authentication required for all actions
- Room access validation in WebSocket `connect()`
- SQL injection prevention via Django ORM

---

## Security Considerations

- CSRF protection on comment/like endpoints
- User authentication required for all actions
- Room access validation in WebSocket `connect()`
- SQL injection prevention via Django ORM
