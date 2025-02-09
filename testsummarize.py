import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional
import re

class YouTubeSummarizer:
    def __init__(self):
        self.llm = ChatOllama(temperature=0, model="deepseek-r1:1.5b")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=1000,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.map_prompt_template = """
        Summarize the following part of a YouTube video transcript:
        "{text}"
        
        KEY POINTS AND TAKEAWAYS:
        """
        
        self.combine_prompt_template = """
        Create a detailed summary of the YouTube video based on these transcript summaries:
        "{text}"
        
        Please structure the summary as follows:
        1. Main Topic/Theme
        2. Key Points
        3. Important Details
        4. Conclusions/Takeaways
        
        DETAILED SUMMARY:
        """
        
        self.map_prompt = PromptTemplate(
            template=self.map_prompt_template,
            input_variables=["text"]
        )
        
        self.combine_prompt = PromptTemplate(
            template=self.combine_prompt_template,
            input_variables=["text"]
        )
        
        self.chain = load_summarize_chain(
            llm=self.llm,
            chain_type="map_reduce",
            map_prompt=self.map_prompt,
            combine_prompt=self.combine_prompt,
            verbose=False
        )

    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?]*)',
            r'(?:youtube\.com\/shorts\/)([^&\n?]*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return None

    def get_transcript(self, video_id: str) -> str:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript_list])
        except Exception as e:
            raise Exception(f"Error getting transcript: {str(e)}")

    def summarize_video(self, youtube_url: str) -> dict:
        try:
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                return {
                    "status": "error",
                    "message": "Invalid YouTube URL"
                }

            transcript = self.get_transcript(video_id)
            texts = self.text_splitter.create_documents([transcript])
            summary = self.chain.run(texts)
            
            return {
                "status": "success",
                "summary": summary,
                "video_id": video_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

def main():
    st.set_page_config(
        page_title="YouTube Video Summarizer",
        page_icon="🎥",
        layout="wide"
    )

    # Add custom CSS
    st.markdown("""
        <style>
        .big-font {
            font-size:24px !important;
            font-weight: bold;
        }
        .summary-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #f0f2f6;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<p class="big-font">🎥 YouTube Video Summarizer</p>', unsafe_allow_html=True)
    st.markdown("Powered by LangChain and Ollama")
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### About")
        st.markdown("""
        This app uses AI to create summaries of YouTube videos.
        
        **Features:**
        - Supports regular YouTube videos and shorts
        - Provides structured summaries
        - Uses local Ollama model
        
        **Note:** Videos must have closed captions/transcripts available.
        """)
        
        st.markdown("### Instructions")
        st.markdown("""
        1. Paste a YouTube URL
        2. Click 'Generate Summary'
        3. Wait for the AI to process the video
        """)

    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # URL input
        youtube_url = st.text_input("Enter YouTube URL:", placeholder="https://youtube.com/watch?v=...")
        
        # Generate button
        if st.button("Generate Summary", type="primary"):
            if youtube_url:
                try:
                    # Show loading spinner
                    with st.spinner("Generating summary... This may take a few moments."):
                        summarizer = YouTubeSummarizer()
                        result = summarizer.summarize_video(youtube_url)
                        
                        if result["status"] == "success":
                            # Display video thumbnail
                            video_id = result["video_id"]
                            st.image(f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg", 
                                   use_column_width=True)
                            
                            # Display summary
                            st.markdown("### Summary")
                            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
                            st.markdown(result["summary"])
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Add copy button
                            st.markdown("### Actions")
                            if st.button("Copy Summary to Clipboard"):
                                st.write("Summary copied!")
                                st.session_state.clipboard = result["summary"]
                        else:
                            st.error(f"Error: {result['message']}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter a YouTube URL")
    
    with col2:
        if youtube_url and 'video_id' in locals():
            st.markdown("### Original Video")
            st.video(youtube_url)

if __name__ == "__main__":
    main()