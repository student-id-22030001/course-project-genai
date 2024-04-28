import os
import whisper
import vertexai
import streamlit as st
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
from moviepy.editor import VideoFileClip, AudioFileClip
from pytube import YouTube
from fpdf import FPDF

def genReport():
    # Ensure there is transcribed text available
    try:
        with open("transcribed_text.txt", "r", encoding="utf-8") as f:
            transcribed_text = f.read()
    except FileNotFoundError:
        st.error("No transcribed text available. Please upload and process a file first.")
        return
    
    credentials = service_account.Credentials.from_service_account_info({
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        })
    vertexai.init(project="997948407242", location="us-central1", credentials=credentials)
    gemini_model = GenerativeModel("projects/997948407242/locations/us-central1/endpoints/2036231762966740992")
    # Generate summary using the model
    # prompt = "Write a summary for the following text:"
    # response = gemini_model.generate_content(f"{transcribed_text}\n{prompt}")

    # # Prepare PDF
    # pdf = FPDF()
    # pdf.add_page()
    # pdf.set_font("Arial", size = 12)

    # # Adding response as multi_cell
    # pdf.multi_cell(0, 10, response.text)

    # # Save PDF
    # pdf_file_path = "Comprehensive_Report.pdf"
    # pdf.output(pdf_file_path)
    # st.success(f"Report generated and saved as {pdf_file_path}")
        # Prepare model prompts
    summary_prompt = "Write a summary for the following text:"
    points_prompt = "List the 10 most important points from the following text:"
    qa_prompt = "Generate 10 questions and their answers based on the following text:"

    # Generate responses using the model
    summary_response = gemini_model.generate_content(f"{transcribed_text}\n{summary_prompt}")
    points_response = gemini_model.generate_content(f"{transcribed_text}\n{points_prompt}")
    qa_response = gemini_model.generate_content(f"{transcribed_text}\n{qa_prompt}")

    # Prepare PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    
    # Adding Summary
    pdf.cell(0, 10, 'Summary:', 0, 1)
    pdf.multi_cell(0, 10, summary_response.text)
    pdf.ln(10)  # Add a line break

    # Adding Important Points
    pdf.cell(0, 10, 'Important Points:', 0, 1)
    pdf.multi_cell(0, 10, points_response.text)
    pdf.ln(10)  # Add a line break

    # Adding Q&A
    pdf.cell(0, 10, 'Questions and Answers:', 0, 1)
    pdf.multi_cell(0, 10, qa_response.text)

    # Save PDF
    pdf_file_path = "Comprehensive_Report.pdf"
    pdf.output(pdf_file_path)
    st.success(f"Report generated and saved as {pdf_file_path}")
# Title of the application
st.title("Video & Audio Based Chatbot")

# Layout for top-right button
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Generate Comprehensive Report"):
        genReport()


# Initialize chat history and file processed flag
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False

# Choose between uploading a file or entering a YouTube URL
input_option = st.radio("Choose your input method:", ("Upload a file", "Enter YouTube URL"))

if input_option == "Upload a file":
    # File uploader for video and audio files
    uploaded_file = st.file_uploader("Upload a video or audio file", type=["avi", "mkv", "mov", "mp4", "mp3", "wav"])

    # Button to process file
    if st.button("Process File"):
        if uploaded_file is not None:
            # Display status message indicating processing has started
            with st.status("Processing file...", expanded=True) as status:
                
                # Check extension to determine type of file
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension in [".avi", ".mkv", ".mov", ".mp4"]:
                    
                    # Process video file
                    video_bytes = uploaded_file.read()
                    video_file_path = 'temp_video.mp4'
                    
                    with open(video_file_path, 'wb') as f:
                        f.write(video_bytes)
                    audio_file_path = 'audio_file.mp3'
                    
                    # Update status
                    st.write("Converting video to audio")
                    
                    # Extract audio from video
                    video_clip = VideoFileClip(video_file_path)
                    video_clip.audio.write_audiofile(audio_file_path)
                    video_clip.close()
                    os.remove(video_file_path)
                
                elif file_extension in [".mp3", ".wav"]:
                    # Process audio file directly
                    audio_bytes = uploaded_file.read()
                    audio_file_path = 'audio_file' + file_extension
                    
                    with open(audio_file_path, 'wb') as f:
                        f.write(audio_bytes)
                
                # Update status
                st.write("Transcribing audio")
                
                # Transcribe audio with Whisper
                whisper_model = whisper.load_model("base")
                result = whisper_model.transcribe(audio_file_path)
                text = result["text"]
                
                # Save the transcribed text to a file
                with open("transcribed_text.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                os.remove(audio_file_path)
                
                # Add transcribed text to chat history
                st.session_state.messages.append({"role": "assistant", "content": f"Transcribed Text: {text}"})
                
                # Update status
                status.update(label="Processing complete!", state="complete", expanded=False)
                
                # Set the file processed flag to True
                st.session_state.file_processed = True
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please upload a file."})

elif input_option == "Enter YouTube URL":
    # Input field for YouTube URL
    youtube_url = st.text_input("Enter YouTube video URL:")

    # Button to process file
    if st.button("Process URL"):
        if youtube_url:
            # Display status message indicating processing has started
            with st.status("Processing URL...", expanded=True) as status:

                # Update status
                st.write("Fetching video from YouTube")
                
                # Download YouTube video
                yt = YouTube(youtube_url)
                video = yt.streams.filter(only_audio=True).first()
                video_file_path = 'temp_video.mp4'
                video.download(filename=video_file_path)

                # Update status
                st.write("Converting video to audio")
                
                # Extract audio from video
                audio_file_path = 'audio_file.mp3'
                audio_clip = AudioFileClip(video_file_path)
                audio_clip.write_audiofile(audio_file_path)
                os.remove(video_file_path)

                # Update status
                st.write("Transcribing audio")

                # Transcribe audio with Whisper
                whisper_model = whisper.load_model("base")
                result = whisper_model.transcribe(audio_file_path)
                text = result["text"]
                    
                # Save the transcribed text to a file
                with open("transcribed_text.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                os.remove(audio_file_path)
                
                # Add transcribed text to chat history
                st.session_state.messages.append({"role": "assistant", "content": f"Transcribed Text: {text}"})

                # Update status
                status.update(label="Processing complete!", state="complete", expanded=False)

                # Set the file processed flag to True
                st.session_state.file_processed = True
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please enter a YouTube URL."})

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
        credentials = service_account.Credentials.from_service_account_info({
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        })

        vertexai.init(project="997948407242", location="us-central1", credentials=credentials)
        gemini_model = GenerativeModel("projects/997948407242/locations/us-central1/endpoints/2036231762966740992")
        
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
