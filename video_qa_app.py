import os
import whisper
import streamlit as st
import google.generativeai as genai
from moviepy.editor import VideoFileClip

# Title of the application
st.title("Video & Audio Based Chatbot")

# Initialize chat history and file processed flag
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False

# File uploader for video and audio files
uploaded_file = st.file_uploader("Upload a video or audio file", type=["avi", "mkv", "mov", "mp4", "mp3", "wav"])

# Button to process file
if st.button("Process File"):
    if uploaded_file is not None:
        
        # Check extension to determine type of file
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension in [".avi", ".mkv", ".mov", ".mp4"]:
            
            # Process video file
            video_bytes = uploaded_file.read()
            video_file_path = 'temp_video.mkv'
            
            with open(video_file_path, 'wb') as f:
                f.write(video_bytes)
            audio_file_path = 'audio_file.mp3'
            
            # Extract audio from video
            video = VideoFileClip(video_file_path)
            video.audio.write_audiofile(audio_file_path)
        
        elif file_extension in [".mp3", ".wav"]:
            # Process audio file directly
            audio_bytes = uploaded_file.read()
            audio_file_path = 'audio_file' + file_extension
            
            with open(audio_file_path, 'wb') as f:
                f.write(audio_bytes)
        
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Unsupported file format. Please upload a supported video or audio file."})
            st.stop()
        
        # Transcribe audio with Whisper
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(audio_file_path)
        text = result["text"]
        
        # Save the transcribed text to a file
        with open("transcribed_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        # Add transcribed text to chat history
        st.session_state.messages.append({"role": "assistant", "content": f"Transcribed Text: {text}"})
        
        # Set the file processed flag to True
        st.session_state.file_processed = True
    else:
        st.session_state.messages.append({"role": "assistant", "content": "Please upload a file."})

# Accept user input as a chat message
if prompt := st.chat_input("Enter question:"):
    
    # Check if the file has been processed
    if not st.session_state.file_processed:
        st.session_state.messages.append({"role": "assistant", "content": "Process the file first."})
        
    else:
        # Read the transcribed text from the file
        try:
            with open("transcribed_text.txt", "r", encoding="utf-8") as f:
                transcribed_text = f.read()
        except FileNotFoundError:
            st.session_state.messages.append({"role": "assistant", "content": "Please upload a file and process it first"})
        
        # Q&A with Gemini
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
        
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-pro')
        
        context = transcribed_text
        response = gemini_model.generate_content(f"{context}\n{prompt}")
        
        # Add user's question to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Add assistant's response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response.text})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
