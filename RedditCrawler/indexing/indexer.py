import lucene
import os
import json
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.document import Document, Field, TextField, StringField, StoredField

lucene.initVM()

def index_jsonl(jsonl_dir, index_dir='reddit_index'):
    store = SimpleFSDirectory(Paths.get(index_dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    for file_name in os.listdir(jsonl_dir):
        if file_name.endswith('.jsonl'):
            with open(os.path.join(jsonl_dir, file_name), 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        post = json.loads(line.strip())
                        doc = Document()

                        
                        doc.add(StringField("id", post.get("id", "") or "", Field.Store.YES))
                        author = post.get("author")
                        if author and isinstance(author, str):
                            doc.add(StringField("author", author, Field.Store.YES))

                        doc.add(StringField("subreddit", post.get("subreddit", "") or "", Field.Store.YES))
                        doc.add(StringField("url", post.get("url", "") or "", Field.Store.YES))

                        
                        doc.add(TextField("title", post.get("title", "") or "", Field.Store.YES))
                        doc.add(TextField("selftext", post.get("selftext", "") or "", Field.Store.YES))

                        doc.add(StoredField("reddit_score", float(post.get("score", 0))))

                        subreddits_str = " ".join(post.get("author_recent_subreddits", []) or [])
                        doc.add(TextField("author_recent_subreddits", subreddits_str, Field.Store.NO))

                        writer.addDocument(doc)

                    except Exception as e:
                        print(f"Error indexing document: {e}")

    writer.close()

if __name__ == "__main__":
    index_jsonl("../../final") # location of folder with data .jsonl files inside of it
    
    