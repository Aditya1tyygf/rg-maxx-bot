import os
import asyncio
import aiohttp
import base64
from fastapi import FastAPI, Request
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from Crypto.Cipher import AES

# --- CONFIGURATIONS ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8271028373:AAF3DnEi9pXXS-kWRLbRQ9oHlR0Lw7GUG3k")
CHANNEL_URL = "https://t.me/your_channel"
LOGO_IMAGE_URL = "https://picsum.photos/800/400"

# Decryption Keys
DECRYPT_KEY = '638udh3829162018'
DECRYPT_IV = 'fedcba9876543210'

# Video Play Base URL
PLAY_BASE_URL = "weathered-forest-6f0e.adityalkkumar4321.workers.dev/mp4"

SEMAPHORE = asyncio.Semaphore(15)

# Initialize FastAPI and Bot
app = FastAPI()
bot = AsyncTeleBot(BOT_TOKEN)

# --- DECRYPTION UTILS ---
def decrypt_aes(encrypted_text: str, key: str, iv: str) -> str:
    if not encrypted_text:
        return ""
    try:
        key_bytes = key.encode('utf-8')
        iv_bytes = iv.encode('utf-8')
        
        try:
            encrypted_bytes = bytes.fromhex(encrypted_text)
        except ValueError:
            encrypted_bytes = base64.b64decode(encrypted_text)
            
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        decrypted = cipher.decrypt(encrypted_bytes)
        
        padding_len = decrypted[-1]
        if 1 <= padding_len <= 16:
            decrypted = decrypted[:-padding_len]
            
        return decrypted.decode('utf-8', errors='ignore').strip()
    except Exception:
        return encrypted_text

# --- API HELPER FUNCTION ---
async def fetch_json(session, url):
    async with SEMAPHORE:
        try:
            async with session.get(url, timeout=12) as r:
                if r.status == 200:
                    return await r.json()
        except Exception:
            pass
        return None

# --- HTML TEMPLATE GENERATOR ---
def generate_html(batch_name, data_list):
    accordion_html = ""
    for subject_name, topics in data_list.items():
        accordion_html += f'<div class="subject-card"><h3>📚 {subject_name}</h3>'
        for topic_name, items in topics.items():
            accordion_html += f'<div class="topic-box"><h4>📌 {topic_name}</h4><div class="items-list">'
            for item in items:
                if item.get('video_url'):
                    accordion_html += f'''
                    <div class="item-row">
                        <span class="item-title">🎥 {item["name"]}</span>
                        <a href="{item["video_url"]}" target="_blank" class="btn btn-video">Play Video</a>
                    </div>'''
                if item.get('pdf1'):
                    accordion_html += f'''
                    <div class="item-row">
                        <span class="item-title">📄 PDF 1: {item["name"]}</span>
                        <a href="{item["pdf1"]}" target="_blank" class="btn btn-pdf">Open PDF</a>
                    </div>'''
                if item.get('pdf2'):
                    accordion_html += f'''
                    <div class="item-row">
                        <span class="item-title">📄 PDF 2: {item["name"]}</span>
                        <a href="{item["pdf2"]}" target="_blank" class="btn btn-pdf2">Open PDF 2</a>
                    </div>'''
            accordion_html += '</div></div>'
        accordion_html += '</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{batch_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #38bdf8; margin-bottom: 30px; }}
        .subject-card {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .subject-card h3 {{ margin-top: 0; color: #f43f5e; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
        .topic-box {{ background: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 15px; }}
        .topic-box h4 {{ margin: 0 0 10px 0; color: #10b981; }}
        .items-list {{ display: flex; flex-direction: column; gap: 10px; }}
        .item-row {{ display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 10px 15px; border-radius: 6px; }}
        .item-title {{ font-size: 14px; max-width: 70%; }}
        .btn {{ text-decoration: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 12px; text-transform: uppercase; transition: 0.3s; }}
        .btn-video {{ background: #0284c7; color: white; }}
        .btn-video:hover {{ background: #0369a1; }}
        .btn-pdf {{ background: #b91c1c; color: white; }}
        .btn-pdf:hover {{ background: #991b1b; }}
        .btn-pdf2 {{ background: #4f46e5; color: white; }}
        .btn-pdf2:hover {{ background: #4338ca; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 {batch_name}</h1>
        {accordion_html}
    </div>
</body>
</html>"""
    return html_content

# --- BOT COMMAND HANDLERS ---

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 Hello {user_name}!\n\n"
        "Welcome to RG Maxx Bot.\n"
        "Please join our channel to access the courses, then type /maxx to begin."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
    markup.add(types.InlineKeyboardButton("✅ Joined / Next", callback_data="check_joined"))
    
    try:
        await bot.send_photo(message.chat.id, LOGO_IMAGE_URL, caption=welcome_text, reply_markup=markup)
    except Exception:
        await bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
async def check_joined_callback(call):
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, "Aapka swagat hai! Ab courses dekhne ke liye /maxx type karein.")

@bot.message_handler(commands=['maxx'])
async def show_courses(message):
    status_msg = await bot.send_message(message.chat.id, "Getting courses, please wait...")
    async with aiohttp.ClientSession() as session:
        batches_data = await fetch_json(session, "https://rgmaxx-api.vercel.app/api/all-batches")
        
    if not batches_data:
        await bot.edit_message_text("Kuch error aaya batches fetch karne me.", status_msg.chat.id, status_msg.message_id)
        return
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    for batch in batches_data:
        markup.add(types.InlineKeyboardButton(f"📘 {batch.get('name')}", callback_data=f"batch_{batch.get('id')}"))
        
    await bot.delete_message(status_msg.chat.id, status_msg.message_id)
    await bot.send_message(message.chat.id, "📚 **Select your Course / Batch:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("batch_"))
async def handle_batch_selection(call):
    await bot.answer_callback_query(call.id)
    batch_id = call.data.split("_")[1]
    status_msg = await bot.edit_message_text("⏳ Processing... Batch details and links are being extracted.", call.message.chat.id, call.message.message_id)
    
    async with aiohttp.ClientSession() as session:
        subjects = await fetch_json(session, f"https://rgmaxx-api.vercel.app/api/get-subjects?courseid={batch_id}")
        if not subjects:
            await bot.edit_message_text("Subjects fetch nahi ho paye.", status_msg.chat.id, status_msg.message_id)
            return
            
        final_structure = {}
        
        async def process_subject(subject):
            sub_id = subject.get('id')
            sub_name = subject.get('name')
            topics = await fetch_json(session, f"https://rgmaxx-api.vercel.app/api/get-topics?courseid={batch_id}&subjectid={sub_id}")
            if not topics: return
            
            final_structure[sub_name] = {}
            
            async def process_topic(topic):
                top_id = topic.get('id')
                top_name = topic.get('name')
                videos = await fetch_json(session, f"https://rgmaxx-api.vercel.app/api/get-videos?courseid={batch_id}&subjectid={sub_id}&topicid={top_id}")
                if not videos: return
                
                final_structure[sub_name][top_name] = []
                
                async def process_video(video):
                    vid_id = video.get('id')
                    vid_name = video.get('name')
                    enc_pdf1 = video.get('pdf_link', '')
                    enc_pdf2 = video.get('pdf_link2', '')
                    
                    pdf1_dec = decrypt_aes(enc_pdf1, DECRYPT_KEY, DECRYPT_IV) if enc_pdf1 else ""
                    pdf2_dec = decrypt_aes(enc_pdf2, DECRYPT_KEY, DECRYPT_IV) if enc_pdf2 else ""
                    
                    vid_details = await fetch_json(session, f"https://rgmaxx-api.vercel.app/api/get-video-details?course_id={batch_id}&video_id={vid_id}")
                    video_url_formatted = ""
                    if vid_details:
                        enc_link = vid_details.get('encrypted_links', '')
                        enc_key = vid_details.get('key', '')
                        dec_url = decrypt_aes(enc_link, DECRYPT_KEY, DECRYPT_IV)
                        dec_key = decrypt_aes(enc_key, DECRYPT_KEY, DECRYPT_IV)
                        if dec_url:
                            video_url_formatted = f"https://{PLAY_BASE_URL}?key={dec_key}&url={dec_url}"
                            
                    final_structure[sub_name][top_name].append({
                        "name": vid_name, "video_url": video_url_formatted, "pdf1": pdf1_dec, "pdf2": pdf2_dec
                    })
                await asyncio.gather(*(process_video(v) for v in videos))
            await asyncio.gather(*(process_topic(t) for t in topics))
        await asyncio.gather(*(process_subject(s) for s in subjects))

    if not final_structure:
        await bot.edit_message_text("Data fetch nahi kiya ja saka.", status_msg.chat.id, status_msg.message_id)
        return

    # Generate txt content
    txt_content = ""
    for sub, topics in final_structure.items():
        txt_content += f"Subject: {sub}\n" + "="*40 + "\n"
        for top, items in topics.items():
            txt_content += f"  Topic: {top}\n" + "-"*30 + "\n"
            for item in items:
                txt_content += f"    - Name: {item['name']}\n"
                if item['video_url']: txt_content += f"      Play Link: {item['video_url']}\n"
                if item['pdf1']: txt_content += f"      PDF 1: {item['pdf1']}\n"
                if item['pdf2']: txt_content += f"      PDF 2: {item['pdf2']}\n"
                txt_content += "\n"

    # Send files directly using bytes to avoid Vercel read-only filesystem errors
    txt_bytes = txt_content.encode('utf-8')
    html_content = generate_html(f"Batch {batch_id}", final_structure)
    html_bytes = html_content.encode('utf-8')

    await bot.delete_message(status_msg.chat.id, status_msg.message_id)
    
    await bot.send_document(call.message.chat.id, txt_bytes, visible_file_name=f"Batch_{batch_id}.txt", caption="📋 Here is your TXT File.")
    await bot.send_document(call.message.chat.id, html_bytes, visible_file_name=f"Batch_{batch_id}.html", caption="🌐 Here is your Premium HTML Player.")

@bot.message_handler(content_types=['document'])
async def handle_txt_to_html(message):
    if message.document.file_name.endswith('.txt'):
        status = await bot.reply_to(message, "Converting your TXT to HTML format...")
        file_info = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        raw_text = downloaded_file.decode('utf-8', errors='ignore')
        lines = raw_text.split('\n')
        parsed_structure = {}
        curr_sub = "Default Subject"
        curr_top = "Default Topic"
        parsed_structure[curr_sub] = {curr_top: []}
        
        item_name, video_url, pdf1, pdf2 = "", "", "", ""
        
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("Subject:"):
                curr_sub = line_str.replace("Subject:", "").strip()
                parsed_structure[curr_sub] = {}
            elif line_str.startswith("Topic:"):
                curr_top = line_str.replace("Topic:", "").strip()
                parsed_structure[curr_sub][curr_top] = []
            elif line_str.startswith("- Name:") or line_str.startswith("Name:"):
                if item_name:
                    parsed_structure[curr_sub][curr_top].append({
                        "name": item_name, "video_url": video_url, "pdf1": pdf1, "pdf2": pdf2
                    })
                item_name = line_str.split(":", 1)[1].strip()
                video_url, pdf1, pdf2 = "", "", ""
            elif "Play Link:" in line_str or "URL:" in line_str:
                video_url = line_str.split(":", 1)[1].strip()
            elif "PDF 1:" in line_str:
                pdf1 = line_str.split(":", 1)[1].strip()
            elif "PDF 2:" in line_str:
                pdf2 = line_str.split(":", 1)[1].strip()
                
        if item_name:
            parsed_structure[curr_sub][curr_top].append({
                "name": item_name, "video_url": video_url, "pdf1": pdf1, "pdf2": pdf2
            })
            
        html_out = generate_html(message.document.file_name.replace(".txt", ""), parsed_structure)
        html_bytes = html_out.encode('utf-8')
        
        await bot.send_document(message.chat.id, html_bytes, visible_file_name=message.document.file_name.replace(".txt", ".html"), caption="✅ Converted HTML.")
        await bot.delete_message(status.chat.id, status.message_id)

# --- VERCEL ROUTE HANDLER ---
# Post requests ke liye (Telegram updates)
@app.post("/")
@app.post("/api/index")
async def process_update(request: Request):
    try:
        json_data = await request.json()
        update = types.Update.de_json(json_data)
        await bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}")
    return {"status": "ok"}

# Get requests ke liye (Browser check)
@app.get("/")
@app.get("/api/index")
def read_root():
    return {"status": "Bot is running successfully!"}
