from telegram import Update
from telegram.ext import Application, ContextTypes, ChatMemberHandler
import asyncio
import sqlite3
from datetime import datetime, timedelta
import imagehash
from PIL import Image
import io
import requests

# Initialize database
def init_db():
    conn = sqlite3.connect('member_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (user_id INTEGER, username TEXT, display_name TEXT, 
                  join_date TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS name_changes
                 (user_id INTEGER, old_name TEXT, new_name TEXT, 
                  change_date TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS protected_photos
                 (user_id INTEGER, photo_hash TEXT)''')
    conn.commit()
    conn.close()

class SecurityBot:
    def __init__(self, token):
        self.token = token
        self.protected_names = set()
        self.protected_user_ids = set()
        self.hash_threshold = 10
        init_db()

    async def start(self):
        self.app = Application.builder().token(self.token).build()
        
        # Only keep member tracking handler
        self.app.add_handler(ChatMemberHandler(self.track_members, ChatMemberHandler.CHAT_MEMBER))
        
        await self.app.initialize()
        await self.app.start()
        await self.app.run_polling()

    async def add_protected_member(self, user_id: int, name: str):
        """Add a member to the protected list and store their profile photo hash"""
        self.protected_names.add(name.lower())
        self.protected_user_ids.add(user_id)
        
        # Get user's profile photos
        photos = await self.app.bot.get_user_profile_photos(user_id, limit=1)
        if photos.photos:
            photo_file = await self.app.bot.get_file(photos.photos[0][-1].file_id)
            photo_url = photo_file.file_path
            
            # Download and hash the image
            response = requests.get(photo_url)
            img = Image.open(io.BytesIO(response.content))
            photo_hash = str(imagehash.average_hash(img))
            
            # Store the hash in database
            conn = sqlite3.connect('member_history.db')
            c = conn.cursor()
            c.execute('INSERT INTO protected_photos VALUES (?, ?)', (user_id, photo_hash))
            conn.commit()
            conn.close()

    async def check_profile_photo(self, user_id: int) -> bool:
        """Check if user's profile photo matches any protected member's photo"""
        # Get user's current profile photo
        photos = await self.app.bot.get_user_profile_photos(user_id, limit=1)
        if not photos.photos:
            return False
            
        photo_file = await self.app.bot.get_file(photos.photos[0][-1].file_id)
        photo_url = photo_file.file_path
        
        # Download and hash the image
        response = requests.get(photo_url)
        img = Image.open(io.BytesIO(response.content))
        current_hash = imagehash.average_hash(img)
        
        # Compare with protected photos
        conn = sqlite3.connect('member_history.db')
        c = conn.cursor()
        c.execute('SELECT photo_hash FROM protected_photos')
        protected_hashes = c.fetchall()
        conn.close()
        
        for (protected_hash,) in protected_hashes:
            hash_difference = abs(current_hash - imagehash.hex_to_hash(protected_hash))
            if hash_difference <= self.hash_threshold:
                return True
                
        return False

    async def track_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track member joins and name changes"""
        if not update.chat_member:
            return

        member = update.chat_member.new_chat_member
        user_id = member.user.id
        username = member.user.username
        display_name = member.user.first_name
        
        # Skip checks for protected members
        if user_id in self.protected_user_ids:
            return
            
        # Check for profile photo impersonation
        if await self.check_profile_photo(user_id):
            await self.ban_user(update, user_id, "Impersonating protected member's profile photo")
            return
        
        conn = sqlite3.connect('member_history.db')
        c = conn.cursor()
        
        # Check if display name is already taken by any other member
        c.execute('''SELECT user_id FROM members 
                     WHERE display_name = ? AND user_id != ?''', 
                  (display_name, user_id))
        existing_user = c.fetchone()
        if existing_user:
            await self.ban_user(update, user_id, "Impersonating another member")
            conn.close()
            return
        
        # Check for name changes
        c.execute('SELECT display_name FROM members WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if result:
            old_name = result[0]
            if old_name != display_name:
                # Record name change
                c.execute('''INSERT INTO name_changes 
                            VALUES (?, ?, ?, ?)''',
                         (user_id, old_name, display_name, 
                          datetime.now().isoformat()))
                
                c.execute('''UPDATE members 
                            SET display_name = ?
                            WHERE user_id = ?''', 
                         (display_name, user_id))
        else:
            # New member
            c.execute('''INSERT INTO members 
                        VALUES (?, ?, ?, ?)''',
                     (user_id, username, display_name, 
                      datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    async def ban_user(self, update: Update, user_id: int, reason: str):
        """Ban user and notify admins"""
        chat_id = update.effective_chat.id
        try:
            await self.app.bot.ban_chat_member(chat_id, user_id)
            await self.app.bot.send_message(
                chat_id,
                f"🚫 Banned user {user_id} for {reason}"
            )
        except Exception as e:
            print(f"Failed to ban user: {e}")

if __name__ == "__main__":
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    bot = SecurityBot(BOT_TOKEN)
    asyncio.run(bot.start()) 