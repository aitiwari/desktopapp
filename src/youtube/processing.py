from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt

from src.youtube.ytsumarize import YouTubeSummarizer
class YTWorker(QThread):
    """Worker thread to process AI-generated text asynchronously."""
    finished = pyqtSignal(dict)  # Signal to send back processed content

    def __init__(self, yt_url):
        super().__init__()
        self.yt_url = yt_url

    def run(self):
        """Runs AI processing in a separate thread to prevent UI freezing."""
        # obj_chat = Chat(self.text_content)
        # updated_text_content = obj_chat.call_ai_agent()
        youtube_url = self.yt_url
        summarizer = YouTubeSummarizer()
        updated_text_content = summarizer.summarize_video(youtube_url)
        print('pass - summarize_video')
        if updated_text_content["status"] == "success":
            print("\nSummary:")
            print(updated_text_content["summary"])
        else:
            print("Error:", updated_text_content["message"])

        # Extract think content, summary, and other content
        processed_content = self.process_text_content(updated_text_content["summary"])
        print('pass - process_text_content')

        # Emit signal with processed content
        self.finished.emit(processed_content)
        
    
    def process_text_content(self, text_content):
        """Extracts <think> and <summary> sections from text."""
        think_content = ""
        summary_content = ""
        rest_content = text_content

        # Extract <think> content
        if "<think>" in text_content and "</think>" in text_content:
            start_index = text_content.find("<think>") + len("<think>")
            end_index = text_content.find("</think>")
            think_content = text_content[start_index:end_index]
            rest_content = text_content.replace(f"<think>{think_content}</think>", "")
        
        return {
            "think_content": think_content,
            "rest_content": rest_content
        }