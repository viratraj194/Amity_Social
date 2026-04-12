---
name: Chat Presence System Architecture
description: Multi-room WebSocket presence tracking with Redis, global + room-specific presence sets, periodic cleanup
type: project
---

**Chat Presence System Architecture (2026-04-11)**

The real-time chat system uses a two-tier presence tracking approach:

**Redis Structure:**
- `global_online_users` (SET) - All online user IDs globally
- `room_{slug}_online` (SET) - User IDs online in each specific room

**Key Design Decisions:**
1. Users can be connected to multiple rooms simultaneously via different WebSocket connections
2. User marked offline globally ONLY when ALL room connections are closed
3. Class-level `_active_connections` dict tracks user_id -> set of room_slugs
4. Periodic cleanup (5 min interval) removes stale presence sets for deleted rooms
5. Management command `cleanup_redis_presence` for external scheduling

**Why:** Previous implementation only tracked single-room presence, causing incorrect offline status when users had multiple chat tabs open. Also needed cleanup mechanism to prevent Redis memory leaks.

**How to apply:** When modifying chat consumers, remember:
- Always update both global AND room-specific presence sets together
- Use `get_online_users_in_room(slug)` for per-room checks (not `get_online_users()`)
- Disconnect logic must check `len(user_rooms) == 0` before setting offline
- Message delivery checks use room-specific presence, not global
