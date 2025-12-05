# 🍞 Bread Van App CLI

This project provides a command-line interface (CLI) for managing and interacting with the Bread Van App. It is built with Flask CLI and click, and supports multiple roles: **User**, **Driver**, and **Resident**.

## 🚀 Setup

### Install dependencies:
```bash
$ pip install -r requirements.txt
```

### Initialize the database:
```bash
flask init
```
This creates and initializes the database with default accounts and tables.

### Run any CLI command using:
```bash
flask <group> <command> [args...]
```

---

## 👤 User Commands | Group: `flask user`
Available to all users regardless of role.

### Login
```bash
flask user login <username> <password>
```

### Logout
```bash
flask user logout
```

### List All Users
```bash
flask user list
```

### View Drives on a Street
```bash
flask user view_street_drives
```
Prompts to select an area and street, then lists scheduled drives.

### View All Areas
```bash
flask user view_all_areas
```

### View All Streets
```bash
flask user view_all_streets
```

---

## 🚐 Driver Commands | Group: `flask driver`
Requires being logged in as a Driver.

### Create Driver
```bash
flask driver create_driver <username> <password>
```

### Delete Driver
```bash
flask driver delete_driver <driver_id>
```

### Schedule Drive
```bash
flask driver schedule_drive YYYY-MM-DD HH:MM
```
Prompts to select area, street, optional menu, and optional ETA.

### Cancel Drive
```bash
flask driver cancel_drive <drive_id>
```

### Update Drive Menu
```bash
flask driver update_drive_menu <drive_id> <menu>
```

### Update Drive ETA
```bash
flask driver update_drive_eta <drive_id> HH:MM
```

### View My Drives
```bash
flask driver view_my_drives
```

### Start Drive
```bash
flask driver start_drive <drive_id>
```

### End Drive
```bash
flask driver end_drive
```

### View Requested Stops
```bash
flask driver view_requested_stops <drive_id>
```

---

## 🏠 Resident Commands | Group: `flask resident`
Requires being logged in as a Resident.

### Create Resident
```bash
flask resident create <username> <password>
```
Prompts for area, street, and house number.

### Add Area
```bash
flask resident add_area <name>
```

### Add Street
```bash
flask resident add_street <area_id> <name>
```

### Delete Area
```bash
flask resident delete_area <area_id>
```

### Delete Street
```bash
flask resident delete_street <street_id>
```

### Request Stop
```bash
flask resident request_stop
```
Lists upcoming drives on your street and prompts to select one.

### Cancel Stop
```bash
flask resident cancel_stop <drive_id>
```

### View Inbox
```bash
flask resident view_inbox
```
Option: `--unread-only` to show only unread notifications.

### Notification Stats
```bash
flask resident notification_stats
```

### Mark Notification as Read
```bash
flask resident mark_notification_read <notification_index>
```

### Mark All Notifications Read
```bash
flask resident mark_all_read
```

### Clear Inbox
```bash
flask resident clear_inbox
```

### Update Notification Preferences
```bash
flask resident update_preferences
```

### View Driver Stats
```bash
flask resident view_driver_stats <driver_id>
```

### Subscribe to Drive
```bash
flask resident subscribe_drive <drive_id>
```

### Unsubscribe from Drive
```bash
flask resident unsubscribe_drive <drive_id>
```

### View Subscribed Drives
```bash
flask resident view_subscribed_drives
```

---

## 🧪 Test Commands | Group: `flask test`

### Run User Tests
```bash
flask test user <unit|int|all>
```

---

## 🔑 Role Requirements Summary
- **General User Commands** – Available to all logged-in users
- **Driver Commands** – Require login as a Driver
- **Resident Commands** – Require login as a Resident
