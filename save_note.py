import os
import json
from notion_client import Client
from datetime import datetime

NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']

payload = json.loads(os.environ['NOTE_PAYLOAD'])
action = payload.get('action', 'create')
notion = Client(auth=NOTION_TOKEN)

def get_text(prop):
    items = prop.get('rich_text', [])
    return items[0]['text']['content'] if items else ''

def get_title(prop):
    items = prop.get('title', [])
    return items[0]['text']['content'] if items else ''

def get_url(prop):
    return prop.get('url') or ''

def get_select(prop):
    s = prop.get('select')
    return s['name'] if s else ''

def rebuild_export():
    """從 Notion 讀取全部資料，存成 export.json"""
    results = []
    cursor = None
    while True:
        kwargs = {'database_id': NOTION_DB_ID, 'page_size': 100}
        if cursor:
            kwargs['start_cursor'] = cursor
        resp = notion.databases.query(**kwargs)
        results.extend(resp.get('results', []))
        if not resp.get('has_more'):
            break
        cursor = resp.get('next_cursor')

    notes = []
    for page in results:
        props = page.get('properties', {})
        note_id = get_text(props.get('note_id', {}))
        if not note_id:
            continue
        created = page.get('created_time', '')[:16].replace('T', ' ')
        notes.append({
            'id': note_id,
            'type': get_select(props.get('類型', {})),
            'title': get_title(props.get('名稱', {})),
            'content': get_text(props.get('內容', {})),
            'url': get_url(props.get('網址', {})),
            'imgUrl': get_url(props.get('圖片網址', {})),
            'date': created,
        })

    with open('export.json', 'w', encoding='utf-8') as f:
        json.dump({'notes': notes, 'exported_at': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    print(f'✓ export.json 更新完成，共 {len(notes)} 筆')

if action == 'create':
    note_type = payload.get('type', '其他')
    title_input = payload.get('title', '')
    content = payload.get('content', '')
    url = payload.get('url', '')
    img_url = payload.get('img_url', '')
    note_id = payload.get('id', '')
    final_title = title_input if title_input else ''

    properties = {
        '名稱': {'title': [{'text': {'content': final_title}}]},
        '類型': {'select': {'name': note_type}},
        '內容': {'rich_text': [{'text': {'content': content[:2000]}}]},
        'note_id': {'rich_text': [{'text': {'content': note_id}}]},
    }
    if url:
        properties['網址'] = {'url': url}
    if img_url:
        properties['圖片網址'] = {'url': img_url}

    notion.pages.create(parent={'database_id': NOTION_DB_ID}, properties=properties)
    print(f'✓ 已建立：{final_title or "(無標題)"}')
    rebuild_export()

elif action == 'update':
    note_id = payload.get('id', '')
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
    img_url = payload.get('img_url', '')
    note_type = payload.get('type', '其他')

    properties = {
        '名稱': {'title': [{'text': {'content': title}}]},
        '類型': {'select': {'name': note_type}},
        '內容': {'rich_text': [{'text': {'content': content[:2000]}}]},
    }
    properties['網址'] = {'url': url if url else None}
    properties['圖片網址'] = {'url': img_url if img_url else None}

    notion.pages.update(page_id=page_id, properties=properties)
    print(f'✓ 已更新：{title}')
    rebuild_export()

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
    rebuild_export()

elif action == 'export':
    rebuild_export()
    print('✓ 匯出完成')
