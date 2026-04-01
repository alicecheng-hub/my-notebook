import os
import json
import anthropic
from notion_client import Client

NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']

payload = json.loads(os.environ['NOTE_PAYLOAD'])

note_type = payload.get('type', '其他')
title_input = payload.get('title', '')
content = payload.get('content', '')
url = payload.get('url', '')
tags = payload.get('tags', [])
timestamp = payload.get('timestamp', '')

# AI 自動產生標題和摘要
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

prompt = f"""你是一個筆記整理助手，請根據以下筆記內容，回覆 JSON 格式（只回 JSON，不要其他文字）：

類型：{note_type}
內容：{content or '（無文字內容）'}
{f'網址：{url}' if url else ''}

請回覆：
{{
  "title": "簡短標題（15字內，繁體中文）",
  "summary": "一句話摘要（40字內，繁體中文）",
  "auto_tags": ["自動推薦標籤1", "自動推薦標籤2"]
}}
{f'注意：標題請使用使用者提供的「{title_input}」' if title_input else ''}"""

ai_title = title_input or note_type
ai_summary = ''
auto_tags = []

try:
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}]
    )
    text = response.content[0].text.strip()
    parsed = json.loads(text)
    ai_title = title_input or parsed.get('title', note_type)
    ai_summary = parsed.get('summary', '')
    auto_tags = parsed.get('auto_tags', [])
except Exception as e:
    print(f'AI 分析失敗，使用預設值：{e}')

# 合併標籤
all_tags = list(set(tags + auto_tags))

# 存入 Notion
notion = Client(auth=NOTION_TOKEN)

full_content = ''
if ai_summary:
    full_content += f'[摘要] {ai_summary}\n\n'
if content:
    full_content += content

properties = {
    '名稱': {
        'title': [{'text': {'content': ai_title}}]
    },
    '類型': {
        'select': {'name': note_type}
    },
    '內容': {
        'rich_text': [{'text': {'content': full_content[:2000]}}]
    },
}

if url:
    properties['網址'] = {'url': url}

if all_tags:
    properties['標籤'] = {
        'multi_select': [{'name': t} for t in all_tags[:10]]
    }

notion.pages.create(
    parent={'database_id': NOTION_DB_ID},
    properties=properties
)

print(f'✓ 已儲存：{ai_title}')
if ai_summary:
    print(f'  摘要：{ai_summary}')
if all_tags:
    print(f'  標籤：{", ".join(all_tags)}')
