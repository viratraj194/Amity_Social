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

## Next Agent Instructions

### Backend Agent
1. Verify message status transitions are atomic
2. Add database migration for any new fields
3. Ensure `MessageNotification` cleanup on read
4. Test concurrent message delivery edge cases

### Frontend Agent
1. Verify status tick colors match design
2. Test room list reordering on message send/receive
3. Ensure nested comments render with proper indentation
4. Add loading states for comment replies

### QA Agent
1. Test message flow: sender offline → receiver online
2. Verify nested comments display correctly on mobile
3. Test chat ordering with 10+ rooms
4. Verify status ticks update in real-time
5. Test comment reply depth (ensure no circular references)

---

## Security Considerations

- CSRF protection on comment/like endpoints
- User authentication required for all actions
- Room access validation in WebSocket `connect()`
- SQL injection prevention via Django ORM
