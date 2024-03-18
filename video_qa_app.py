import os
import whisper
import streamlit as st
import google.generativeai as genai
from moviepy.editor import VideoFileClip

# Title of the application
st.title("Video Based Q&A")

# Initialize chat history and video processed flag
if "messages" not in st.session_state:
    st.session_state.messages = []
if "video_processed" not in st.session_state:
    st.session_state.video_processed = False

# Video up-loader
uploaded_file = st.file_uploader("Upload a video", type=["avi", "mkv", "mov", "mp4"])

# Button to process video
if st.button("Process Video"):
    if uploaded_file is not None:
        
		# Extract audio from video
        video_bytes = uploaded_file.read()
        video_file_path = 'temp_video.mkv'
        
        with open(video_file_path, 'wb') as f:
            f.write(video_bytes)
        audio_file_path = 'audioFile.mp3'
        
        video = VideoFileClip(video_file_path)
        video.audio.write_audiofile(audio_file_path)
        
        # Transcribe Audio with Whisper
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(audio_file_path)
        text = result["text"]
        
        # Save the transcribed text to a file
        with open("transcribed_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        # Add transcribed text to chat history
        st.session_state.messages.append({"role": "assistant", "content": f"Transcribed Text: {text}"})
        
        # Set the video processed flag to True
        st.session_state.video_processed = True
    else:
        st.session_state.messages.append({"role": "assistant", "content": "Please upload a video."})

# Accept user input as a chat message
if prompt := st.chat_input("Enter question:"):
    
    # Check if the video has been processed
    if not st.session_state.video_processed:
        st.session_state.messages.append({"role": "assistant", "content": "Process the video first."})
        
    else:
        # Read the transcribed text from the file
        try:
            with open("transcribed_text.txt", "r", encoding="utf-8") as f:
                transcribed_text = f.read()
        except FileNotFoundError:
            st.session_state.messages.append({"role": "assistant", "content": "Please upload a video and process it first"})
        
        # Q&A with Gemini
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
        
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        context = transcribed_text
        response = model.generate_content(f"{context}\n{prompt}")
        
        # Add user's question to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response.text})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
