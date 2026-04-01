import os
import json
from notion_client import Client
from datetime import datetime

NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']

payload = json.loads(os.environ['NOTE_PAYLOAD'])
action = payload.get('action', 'create')
notion = Client(auth=NOTION_TOKEN)

if action == 'create':
    note_type = payload.get('type', '其他')
    title_input = payload.get('title', '')
    content = payload.get('content', '')
    url = payload.get('url', '')
    note_id = payload.get('id', '')

    final_title = title_input

    properties = {
        '名稱': {'title': [{'text': {'content': final_title}}]},
        '類型': {'select': {'name': note_type}},
        '內容': {'rich_text': [{'text': {'content': content[:2000]}}]},
        'note_id': {'rich_text': [{'text': {'content': note_id}}]},
    }
    if url:
        properties['網址'] = {'url': url}

    notion.pages.create(parent={'database_id': NOTION_DB_ID}, properties=properties)
    print(f'✓ 已建立：{final_title}')

elif action == 'update':
    note_id = payload.get('id', '')
    # 先找到對應頁面
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={'property': 'note_id', 'rich_text': {'equals': note_id}}
    ).get('results', [])

    if not results:
        print(f'找不到 note_id={note_id}')
        exit(1)

    page_id = results[0]['id']
    title = payload.get('title', '')
    content = payload.get('content', '')
    url = payload.get('url', '')
    note_type = payload.get('type', '其他')

    properties = {
        '名稱': {'title': [{'text': {'content': title or note_type}}]},
        '類型': {'select': {'name': note_type}},
        '內容': {'rich_text': [{'text': {'content': content[:2000]}}]},
    }
    if url:
        properties['網址'] = {'url': url}
    else:
        properties['網址'] = {'url': None}

    notion.pages.update(page_id=page_id, properties=properties)
    print(f'✓ 已更新：{title}')

elif action == 'delete':
    note_id = payload.get('id', '')
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={'property': 'note_id', 'rich_text': {'equals': note_id}}
    ).get('results', [])

    if not results:
        print(f'找不到 note_id={note_id}')
        exit(1)

    page_id = results[0]['id']
    notion.pages.update(page_id=page_id, archived=True)
    print(f'✓ 已刪除 note_id={note_id}')
