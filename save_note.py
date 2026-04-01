import os
import json
from notion_client import Client
from datetime import datetime

NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']

payload = json.loads(os.environ['NOTE_PAYLOAD'])

note_type = payload.get('type', '其他')
title_input = payload.get('title', '')
content = payload.get('content', '')
url = payload.get('url', '')
tags = payload.get('tags', [])

# 標題：用使用者輸入的，沒有的話用「類型 + 日期」
if title_input:
    final_title = title_input
else:
    date_str = datetime.now().strftime('%m/%d')
    final_title = f'{note_type} {date_str}'

# 存入 Notion
notion = Client(auth=NOTION_TOKEN)

properties = {
    '名稱': {
        'title': [{'text': {'content': final_title}}]
    },
    '類型': {
        'select': {'name': note_type}
    },
    '內容': {
        'rich_text': [{'text': {'content': content[:2000]}}]
    },
}

if url:
    properties['網址'] = {'url': url}

if tags:
    properties['標籤'] = {
        'multi_select': [{'name': t} for t in tags[:10]]
    }

notion.pages.create(
    parent={'database_id': NOTION_DB_ID},
    properties=properties
)

print(f'✓ 已儲存：{final_title}')
