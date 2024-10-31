# Telegram Anti-Impersonation Bot

A security bot that prevents impersonation attacks in Telegram groups by monitoring name changes and profile pictures.

## Quick Start
For experienced users:
1. `pip install python-telegram-bot pillow imagehash requests`
2. Get bot token from @BotFather
3. Edit `bot.py` with your token
4. Create `setup.py` with admin IDs (get from @userinfobot)
5. Run `python setup.py` once
6. Run `python bot.py`

For detailed instructions, see Setup Guide below.

## Features

### Name Protection
- Prevents any user from using a display name that's already taken by another member
- Extra protection for designated moderators/admins
- Automatic banning of users who attempt impersonation
- Complete history tracking of all name changes

### Profile Picture Protection
- Prevents copying of protected members' profile pictures
- Uses perceptual hashing to detect similar images
- Configurable similarity threshold
- Can detect modified versions of protected photos

### Database Tracking
- Maintains member information in SQLite database
- Tracks all name changes historically
- Stores protected member profile photo hashes

## Step-by-Step Setup Guide

### 1. Install Python Requirements
First, make sure you have Python 3.7 or higher installed. Then install the required packages:
```bash
pip install python-telegram-bot pillow imagehash requests
```

### 2. Create Your Telegram Bot
1. Open Telegram and search for "@BotFather"
2. Start a chat with BotFather
3. Send the command: `/newbot`
4. Choose a name for your bot (e.g., "My Group Security Bot")
5. Choose a username for your bot (must end in 'bot', e.g., "mygroupsecurity_bot")
6. BotFather will reply with a message containing your bot token
7. Save this token - it looks like: `123456789:ABCdefGHIjklmNOPqrstUVwxyz`

### 3. Set Up the Code
1. Download `bot.py` to your computer/server
2. Open `bot.py` in a text editor
3. Find the line: `BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"`
4. Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token
5. Save the file

### 4. Add Bot to Your Group
1. Open your Telegram group
2. Click the group name at the top
3. Click 'Edit' or the pencil icon
4. Select 'Administrators'
5. Click 'Add Admin'
6. Search for your bot's username
7. Enable these permissions:
   - ✅ Delete messages
   - ✅ Ban users
   - ❌ All other permissions can be left disabled

### 5. Get Admin/Mod User IDs
1. Add "@userinfobot" to your group
2. Have each admin/mod send any message in the group
3. @userinfobot will reply with their user ID
4. Write down each admin's:
   - User ID (e.g., 123456789)
   - Display name (e.g., "John Admin")

### 6. Create Setup File
1. Create a new file called `setup.py` with this content:
```python
from bot import SecurityBot
import asyncio

async def setup_protected_members():
    bot = SecurityBot("YOUR-BOT-TOKEN-HERE")
    
    # Add each admin/mod (replace with real info)
    await bot.add_protected_member(user_id=123456789, name="John Admin")
    await bot.add_protected_member(user_id=987654321, name="Mary Mod")
    
    await bot.start()

if __name__ == "__main__":
    asyncio.run(setup_protected_members())
```
2. Replace:
   - `YOUR-BOT-TOKEN-HERE` with your actual bot token
   - The user_id and name values with your actual admin information

3. Run the setup file once to register your admins:
```bash
python setup.py
```
4. After setup completes successfully, you can close it

### 7. Run the Bot
1. Open terminal/command prompt
2. Navigate to the folder containing your files
3. Run the bot:
```bash
python bot.py
```
4. Keep this terminal window open - the bot only works while running
5. Consider using a process manager like PM2 or running on a server for 24/7 operation

### 8. Verify Operation
1. The bot should start without errors
2. Try changing your name to an admin's name - the bot should ban you
3. Try copying an admin's profile picture - the bot should ban you

## How It Works

The bot automatically:
- Tracks all member names in the group
- Prevents duplicate display names
- Bans users who try to copy protected members' profile pictures
- Keeps history of all name changes
- Sends ban notifications to the group

## Database Structure

Three SQLite tables are used:

1. `members`:
   - Current member information
   - user_id, username, display_name, join_date

2. `name_changes`:
   - History of name changes
   - user_id, old_name, new_name, change_date

3. `protected_photos`:
   - Protected members' profile photos
   - user_id, photo_hash

## Troubleshooting

Common issues:

1. Bot won't start:
   - Check your bot token
   - Verify all packages are installed
   - Ensure Python 3.7+ is installed

2. Can't ban users:
   - Verify bot is group admin
   - Check ban permission is enabled

3. Profile picture protection not working:
   - Verify protected members were added correctly
   - Check bot can access profile pictures

## Requirements

- Python 3.7 or higher
- Stable internet connection
- Storage for SQLite database
- Bot must be group admin
- Required packages:
  - python-telegram-bot
  - pillow
  - imagehash
  - requests

## Security Notes

- Keep your bot token secret
- Don't share your database file
- Regularly backup the database
- Monitor bot logs for issues
- Keep Python and packages updated

## Limitations

- Only protects against name and photo impersonation
- Must be running continuously
- Requires manual setup of protected members
- Works only in groups where bot is admin