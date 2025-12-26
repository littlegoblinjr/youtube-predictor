import os
import sys
import pandas as pd
from googleapiclient.discovery import build
import requests
from datetime import datetime

API_KEY = os.getenv('API_KEY')
blocks = {
    1: ['minecraft tutorial', 'GTA 6', 'GTA 5', 'fortnite tips', 'valorant guide', 'roblox hacks',
        'minecraft survival', 'minecraft houses', 'minecraft redstone', 'minecraft mods',
        'warzone strategy', 'warzone loadout', 'python tutorial', 'python tutorial 2025', 'python project',
        'javascript tutorial', 'react tutorial', 'coding interview', 'tech review iphone', 'ai tutorial', 
        'machine learning tutorial', 'web development 2025', 'GTA 6 leaks', 'call of duty tips',
        'genshin impact guide', 'mrbeast challenge', 'python project ideas'],
    
    2: ['leetcode python', 'nextjs tutorial', 'tailwind css tutorial', 'docker tutorial',
        'kubernetes tutorial', 'aws tutorial', 'devops project', 'chatgpt tutorial',
        'stable diffusion tutorial', 'midjourney tutorial', 'iphone 17 review', 'fortnite chapter 6',
        'roblox obby', 'valorant rank up', 'cod zombies guide', 'poppy playtime chapter 4',
        'solo leveling gameplay', 'kingdom come deliverance 2', 'monster hunter wilds',
        'javascript project', 'react native tutorial', 'coding interview python', 'tech review samsung s25',
        'macbook pro m4 review', 'rtx 5090 review'],
    
    3: ['minecraft tutorial', 'GTA 6', 'fortnite tips', 'python tutorial', 'javascript project',
        'ai tutorial', 'warzone loadout', 'mrbeast gaming', 'roblox story', 'minecraft parkour',
        'tech review iphone', 'python tutorial 2025', 'machine learning tutorial', 'web development 2025',
        'coding interview', 'minecraft survival', 'valorant guide', 'roblox hacks', 'GTA 6 leaks',
        'genshin impact guide', 'python project', 'leetcode python', 'nextjs tutorial',
        'docker tutorial', 'chatgpt tutorial'],
    
    4: ['ai tutorial', 'stable diffusion tutorial', 'iphone 17 review', 'fortnite chapter 6',
        'warzone strategy', 'call of duty tips', 'react tutorial', 'tech review samsung s25',
        'macbook pro m4 review', 'rtx 5090 review', 'minecraft tutorial', 'GTA 6', 'python tutorial',
        'javascript tutorial', 'coding interview', 'valorant rank up', 'roblox obby',
        'mrbeast challenge', 'genshin impact guide', 'aws tutorial', 'devops project',
        'midjourney tutorial', 'kingdom come deliverance 2', 'monster hunter wilds', 'solo leveling gameplay']
}


all_videos = []
def collect_block(block_num):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    queries = blocks[block_num][:25]  # Full 25 queries
    all_videos = []
    
    # Step 1: Search videos
    print(f"🔍 Searching {len(queries)} queries...")
    video_ids = []  # Collect ALL video IDs first
    
    for query in queries:
        request = youtube.search().list(
            part='id,snippet', 
            q=query,
            type='video', 
            maxResults=50, 
            order='viewCount'
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['id']['videoId']
            video_ids.append(video_id)  # COLLECT IDs
            all_videos.append({
                'video_id': video_id,
                'title': item['snippet']['title'],
                'query': query,
                'channel_id': item['snippet']['channelId'],
                'channel_title': item['snippet']['channelTitle'],
                'search_timestamp': datetime.now().isoformat()
            })
    
    # Step 2: BATCH FETCH views + subs (SAME BLOCK)
    print(f"📊 Fetching stats for {len(video_ids)} videos...")
    
    # Get video stats (views, duration, etc.)
    video_details = {}
    for i in range(0, len(video_ids), 50):  # Batch 50
        batch = video_ids[i:i+50]
        request = youtube.videos().list(
            part='statistics,snippet,contentDetails',
            id=','.join(batch)
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['id']
            stats = item.get('statistics', {})
            content = item.get('contentDetails', {})
            
            video_details[video_id] = {
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'duration_secs': parse_duration(content.get('duration', 'PT0S')),
                'publish_time': item['snippet'].get('publishedAt', ''),
                'category_id': int(item['snippet'].get('categoryId', 0))
            }
    
    # Step 3: Get subscriber counts (unique channels)
    channel_ids = list(set([v['channel_id'] for v in all_videos]))
    print(f"📺 Fetching subs for {len(channel_ids)} channels...")
    
    subs_dict = {}
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i+50]
        request = youtube.channels().list(
            part='statistics',
            id=','.join(batch)  # FIXED: comma, no space
        )
        response = request.execute()
        
        for item in response['items']:
            subs_dict[item['id']] = int(item.get('statistics', {}).get('subscriberCount', 0))
    
    # Step 4: MERGE everything into final dataset
    for video in all_videos:
        vid_id = video['video_id']
        video.update(video_details.get(vid_id, {}))  # Add views/duration
        video['subscriber_count'] = subs_dict.get(video['channel_id'], 0)  # Add subs
    
    # Step 5: Save COMPLETE dataset
    df = pd.DataFrame(all_videos)
    os.makedirs('data', exist_ok=True)
    filename = f"data/batch_block{block_num}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"✅ Block {block_num}: {len(df)} videos → {filename}")
    print(f"   Views: {df.views.min():,} - {df.views.max():,} | Subs: {df.subscriber_count.min()} - {df.subscriber_count.max()}")
    return filename

def parse_duration(duration_str):
    import re
    if not duration_str or duration_str == 'PT0S':
        return 0
    
    # Safe regex match
    duration = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if duration is None:
        return 0  # Fallback for weird formats
    
    # Safe group extraction
    hours = int(duration.group(1) or 0)
    minutes = int(duration.group(2) or 0)
    seconds = int(duration.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


# Test it

