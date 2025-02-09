import re
from langchain_community.chat_models import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeSummarizer:
    def __init__(self):
        self.llm = ChatOllama(temperature=0, model="deepseek-r1:1.5b")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000, chunk_overlap=1000, separators=["\n\n", "\n", " ", ""]
        )
        
        self.map_prompt = PromptTemplate(
            template="""
            Summarize the following part of a YouTube video transcript:
            "{text}"
            
            KEY POINTS AND TAKEAWAYS:
            """,
            input_variables=["text"]
        )
        
        self.combine_prompt = PromptTemplate(
            template="""
            Create a detailed summary of the YouTube video based on these transcript summaries:
            "{text}"
            
            Please structure the summary as follows:
            1. Main Topic/Theme
            2. Key Points
            3. Important Details
            4. Conclusions/Takeaways
            
            DETAILED SUMMARY:
            """,
            input_variables=["text"]
        )
        
        self.chain = load_summarize_chain(
            llm=self.llm, chain_type="map_reduce", map_prompt=self.map_prompt, combine_prompt=self.combine_prompt, verbose=False
        )

    def extract_video_id(self, youtube_url: str):
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?]*)',
            r'(?:youtube\.com/shorts/)([^&\n?]*)'
        ]
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return None

    def get_transcript(self, video_id: str):
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript_list])
        except Exception as e:
            raise Exception(f"Error getting transcript: {str(e)}")

    def summarize_video(self, youtube_url: str):
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            return {"status": "error", "message": "Invalid YouTube URL"}
        
        try:
            transcript = self.get_transcript(video_id)
            texts = self.text_splitter.create_documents([transcript])
            summary = self.chain.run(texts)
            return {"status": "success", "summary": summary, "video_id": video_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    youtube_url = 'https://www.youtube.com/watch?v=iLom1WlqwS0'
    summarizer = YouTubeSummarizer()
    result = summarizer.summarize_video(youtube_url)
    if result["status"] == "success":
        print("\nSummary:")
        print(result["summary"])
    else:
        print("Error:", result["message"])
