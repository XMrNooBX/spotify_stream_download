import requests as r
from urllib.parse import urlencode
import streamlit as st
import re
import yt_dlp
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import urllib.parse


st.markdown(""" 
    <style>
    body {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #fff;
        font-family: 'Courier New', Courier, monospace;
    }
    .stTextInput>div>input {
        background-color: #ee1d3c;
        color: white;
        border-radius: 8px;
        padding: 8px;
    }
    .stRadio>div>label>div {
        color: #b7f1f3 !important;
    }
    h1 {
        text-shadow: 2px 2px #4ea2e8;
        animation: flicker 2.5s infinite alternate;
    }
    @keyframes flicker {
        0% {opacity: 1;}
        50% {opacity: 0.8;}
        100% {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)


def audio_element(song):
    return f"""
    <style>
        /* Wrapper for the custom audio player */
        .audio-wrapper {{
            position: relative;
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
            border-radius: 15px;
            background: linear-gradient(to right, #ff7e5f, #feb47b); /* Gradient Background */
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            padding: 10px;
            transition: background 2s ease; /* Gradient background transition */
        }}

        /* Hover effect on wrapper */
        .audio-wrapper:hover {{
            background: linear-gradient(to right, #feb47b, #ff7e5f); /* Reverse gradient on hover */
            transform: scale(1.05);
        }}

        /* Audio player styling */
        #audioPlayer {{
            width: 100%;
            height: 60px;
            border: none;
            border-radius: 10px;
            outline: none;
            background-color: transparent;
            position: relative;
            z-index: 2; /* Ensures the player controls stay on top */
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}

        /* Music note icon with animation */
        .audio-icon {{
            position: absolute;
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
            font-size: 30px;
            color: #fff;
            z-index: 1;
            animation: bounce 1s infinite, float 2s ease-in-out infinite; /* Float animation added */
        }}

        /* Bounce animation */
        @keyframes bounce {{
            0%, 100% {{
                transform: translateY(-50%);
            }}
            50% {{
                transform: translateY(-70%);
            }}
        }}

        /* Floating animation */
        @keyframes float {{
            0% {{
                transform: translateY(-50%);
            }}
            50% {{
                transform: translateY(-40%);
            }}
            100% {{
                transform: translateY(-50%);
            }}
        }}

        /* Play Button and other controls styling */
        audio::-webkit-media-controls-panel {{
            background: transparent !important;
            border-radius: 10px;
        }}

        /* Custom styling for play/pause button */
        audio::-webkit-media-controls-play-button {{
            background-color: #fff !important;
            border-radius: 50% !important;
            width: 50px;
            height: 50px;
        }}

        /* Custom volume slider */
        audio::-webkit-media-controls-volume-slider {{
            background: #feb47b !important;
            border-radius: 10px !important;
        }}

        /* Hide default controls but let native controls display */
        audio::-webkit-media-controls {{
            background: transparent;
        }}

        /* Song name hover effect */
        .song-name:hover {{
            color: #ff7e5f;
            cursor: pointer;
            transform: scale(1.1);
            transition: transform 0.3s ease, color 0.3s ease;
        }}

        /* General style for song selection options */
        .song-selection {{
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            color: #333;
            padding: 10px;
            background-color: #f7f7f7;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}
        
        .song-selection:hover {{
            background-color: #ff7e5f;
            color: white;
            transform: scale(1.05);
        }}
    </style>

    <div class="audio-wrapper">
        <!-- Music Note Icon -->
        <i class="audio-icon">&#127926;</i>
        <!-- Custom Audio Player -->
        <audio id="audioPlayer" controls autoplay loop>
            <source src="{song}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    </div>
    """


# Base URL and parameters
llm = ChatGroq(temperature=0.2, model="llama-3.3-70b-versatile", api_key='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')
def get_playlist(link):
    base_url = 'https://api.fabdl.com/spotify/get'
    params = {
        'url': link
    }
    encoded_params = urlencode(params)
    url = f"{base_url}?{encoded_params}"
    resp = r.get(url)
    data = resp.json()

    tracks = data['result']['tracks']
    playlist_id = data['result']['gid']
    songs = {}
    for i in tracks:
        songs[i["name"]+" "+i["artists"]] = i['id']
    return songs, playlist_id

# Function to get the streaming URL
def get_song_url(playlist_id, song_id):
    mid_url = f'https://api.fabdl.com/spotify/mp3-convert-task/{playlist_id}/{song_id}'
    resp = r.get(mid_url).json()
    dl_id = resp['result']['tid']
    streaming_url = f'https://api.fabdl.com/spotify/download-mp3/{dl_id}'
    try:
        _ = r.get(streaming_url).headers['Content-Length']
        return streaming_url
    except :
        return False


def closest_title_jio(query, titles, llm):
    system = f"""
    Given a user search query song name: "{query}" and a list of YouTube video titles:
    {titles},
    return ONLY the complete and correct song title from the list that most closely matches the user's intent, prioritizing exact or near-exact matches to the query. 
    If the query matches part of a song title exactly (e.g., words or phrases), return the full title of that match even if other titles are longer or contain additional details.
    If no potential match is found, return "False".
    Do not add any explanation or extra content, only return the exact title of the best match or "False".
    """

    user = f"{query}"

    filtering_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", user)
        ]
    )

    filtering_chain = filtering_prompt | llm | StrOutputParser()

    response = filtering_chain.invoke({"query": query})

    return response if response else "False"

def jio_song_data(name: str):
    results = {}
    url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&query={name}&_format=json&_marker=0&ctx=wap6dot0"
    info = r.get(url)
    if info.status_code == 200:
        resp = info.json().get("songs", {}).get("data", [])
        for i in resp:
            results[f"{i['title']} - {i['description']}"] = i['url']
    try: 
        link = results[closest_title_jio(name, list(results.keys()), llm)]
        song_id = re.findall(r'song/(.*?)/(.*)', link)[0]
        url = f'https://www.jiosaavn.com/api.php?__call=webapi.get&api_version=4&_format=json&_marker=0&ctx=wap6dot0&token={song_id[1]}&type=song'
        resp = r.get(url)
        response = resp.json()
        final_url = urllib.parse.quote(response['songs'][0]['more_info']['encrypted_media_url'])
        dwn_url = f'https://www.jiosaavn.com/api.php?__call=song.generateAuthToken&url={final_url}&bitrate=320&api_version=4&_format=json&ctx=wap6dot0'
        dwn_r = r.get(dwn_url)
        return re.findall(r"(.+?(?=Expires))", dwn_r.json()['auth_url'])[0].replace('.cf.', '.').replace('?', '').replace('ac', 'aac')
    except:
        return False


def closest_title(query, titles, llm):
    system = f"""
    You are tasked with analyzing a list of YouTube video titles to find the most relevant match for a given song query.
    The query: "{query}"
    The list of YouTube titles: {titles}
    
    Your goal:
    - Always prioritize the closest match to the query.
    - If an exact or near-exact match for the query is found, return that title, even if other versions like mixes or remixes are present.
    - If there are multiple plausible matches, choose the one that is closest to the query in wording and intent.
    - If none of the titles plausibly match the query, return the first title from the list.
    - Do not add any explanations, reasoning, or extra content. Only return the most plausible title as your output.
    """
    
    user = f"The query is: {query}"
    
    filtering_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", user)
        ]
    )
    
    filtering_chain = filtering_prompt | llm | StrOutputParser()
    
    response = filtering_chain.invoke({"query": query})

    return response.strip()

def get_yt_song(query: str):
    query = query.replace(' ', '+')
    url = f'https://www.youtube.com/results?search_query={query}'
    response = r.get(url).text
    resp = re.findall(r'videoId\":\"(.*?)\"', response)
    
    if len(resp) > 0:
        v_ids = list(dict.fromkeys(resp))[:7]
        songs = {}
        for i in v_ids:
            ydl_opts = {}
            lnk = f'https://www.youtube.com/watch?v={i}'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.sanitize_info(ydl.extract_info(lnk,download=False))
                duration = info['duration']
                if duration > 60:
                    songs[info['title']] = i
        
        yt_id = songs[closest_title(query, list(songs.keys()), llm)]
        URL = f'https://www.youtube.com/watch?v={yt_id}'
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(URL, download=False)
            sanitized_info = ydl.sanitize_info(info)['formats']
            for i in sanitized_info:
                if i['resolution'] == "audio only" and "audio_channels" in i:
                    return i['url']

def get_search_data(query: str):
    results = {}
    url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&query={query}&_format=json&_marker=0&ctx=wap6dot0"
    info = r.get(url)
    if info.status_code == 200:
        resp = info.json().get("songs", {}).get("data", [])
        for i in resp:
            results[f"{i['title']} - {i['description']}"] = i['url']
    
    query = query.replace(' ', '+')
    url = f'https://www.youtube.com/results?search_query={query}'
    response = r.get(url).text
    resp = re.findall(r'videoId\":\"(.*?)\"', response)
    
    if len(resp) > 0:
        v_ids = list(dict.fromkeys(resp))[:7]
        for i in v_ids:
            ydl_opts = {}
            lnk = f'https://www.youtube.com/watch?v={i}'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.sanitize_info(ydl.extract_info(lnk,download=False))
                duration = info['duration']
                if duration > 60:
                    results[info['title']] = i
    return results

def get_search_download(name, results):
    link = results[name]
    if 'jiosaavn' in link:    
        try: 
            song_id = re.findall(r'song/(.*?)/(.*)', link)[0]
            url = f'https://www.jiosaavn.com/api.php?__call=webapi.get&api_version=4&_format=json&_marker=0&ctx=wap6dot0&token={song_id[1]}&type=song'
            resp = r.get(url)
            response = resp.json()
            final_url = urllib.parse.quote(response['songs'][0]['more_info']['encrypted_media_url'])
            dwn_url = f'https://www.jiosaavn.com/api.php?__call=song.generateAuthToken&url={final_url}&bitrate=320&api_version=4&_format=json&ctx=wap6dot0'
            dwn_r = r.get(dwn_url)
            return re.findall(r"(.+?(?=Expires))", dwn_r.json()['auth_url'])[0].replace('.cf.', '.').replace('?', '').replace('ac', 'aac')
        except:
            return False
    else:
        URL = f'https://www.youtube.com/watch?v={link}'
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(URL, download=False)
            sanitized_info = ydl.sanitize_info(info)['formats']
            for i in sanitized_info:
                if i['resolution'] == "audio only" and "audio_channels" in i:
                    return i['url']


st.title(':rainbow[Good boy Vibes]')

playlist = st.text_input(':rainbow[Search for something or Enter Spotify playlist link: ]')

if 'downloaded_songs' not in st.session_state:
    # Initialize a global dictionary for downloaded songs
    st.session_state['downloaded_songs'] = {}

if playlist and 'spotify' in playlist:
    # Fetch playlist only if it's new
    if 'playlist_link' not in st.session_state or st.session_state.playlist_link != playlist:
        try:
            songs, playlist_id = get_playlist(playlist)
            st.session_state['playlist_link'] = playlist
            st.session_state['songs'] = songs
            st.session_state['playlist_id'] = playlist_id
        except Exception as e:
            st.error(f"Failed to fetch playlist: {e}")

    if 'songs' in st.session_state and 'playlist_id' in st.session_state:
        selected_song = st.sidebar.radio(":violet[Select a song:]", list(st.session_state.songs.keys()))
        song_id = st.session_state.songs[selected_song]

        # Check if the song is already downloaded
        if selected_song in st.session_state['downloaded_songs']:
            song = st.session_state['downloaded_songs'][selected_song]
        else:
            # Try fetching song URL
            with st.spinner(":green[Getting Your Tunes ready....]"):
                song = get_song_url(st.session_state.playlist_id, song_id) or jio_song_data(selected_song) or get_yt_song(selected_song)

            if song:
                # Save the downloaded song URL in global session state
                st.session_state['downloaded_songs'][selected_song] = song
            else:
                st.error('Failed to fetch song URL.')
        if song:
            html_code = audio_element(song)
            st.components.v1.html(html_code, height=150)


elif playlist and 'spotify' not in playlist:
    if 'search_query' not in st.session_state or st.session_state.search_query != playlist:
        try:
            with st.spinner(":green[searching web...]"):
                st.session_state['search_results'] = get_search_data(playlist)
                st.session_state['search_query'] = playlist
        except Exception as e:
            st.error(f"Failed to fetch search: {e}")
    
    if 'search_results' in st.session_state:
        selected_song = st.sidebar.radio(":violet[Select a song:]", list(st.session_state.search_results.keys()))
        song_id = st.session_state.search_results[selected_song]

        if selected_song in st.session_state['downloaded_songs']:
            song = st.session_state['downloaded_songs'][selected_song]
        else:
            with st.spinner(":green[Getting Your Tunes ready....]"):
                song = get_search_download(selected_song, st.session_state.search_results)
            if song:
                # Save the downloaded song URL in global session state
                st.session_state['downloaded_songs'][selected_song] = song
            else:
                st.error('Failed to fetch song URL.')
        if song:
            html_code = audio_element(song)
            st.components.v1.html(html_code, height=100)
