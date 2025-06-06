import lucene, math
from flask import Flask, render_template, request
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.queryparser.classic import QueryParser

#########################################################
# one-time Lucene VM start-up + constants
#########################################################
lucene.initVM(vmargs=["-Djava.awt.headless=true"])
INDEX_DIR = "RedditCrawler/indexing/reddit_index"
ANALYZER  = StandardAnalyzer()
PARSER    = QueryParser("selftext", ANALYZER)        # default search field

#########################################################
# helper: open a *fresh* reader / searcher every request
#########################################################
def get_searcher() -> IndexSearcher:
    reader = DirectoryReader.open(SimpleFSDirectory(Paths.get(INDEX_DIR)))
    return IndexSearcher(reader)

#########################################################
# Flask
#########################################################
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("search.html")

@app.route("/search", methods=["POST"])
def search():
    lucene.getVMEnv().attachCurrentThread()

    qstring = request.form.get("q", "").strip()
    rank_method = request.form.get("rank_method", "combined") # ec
    if not qstring:
        return render_template("search.html", error="Enter a query")

    searcher     = get_searcher()                        # fresh reader
    lucene_query = PARSER.parse(QueryParser.escape(qstring))
    hits         = searcher.search(lucene_query, 100).scoreDocs
    print("Hits:", len(hits))

    
    results = []
    for h in hits:
        # old method for scoring
        # score = 0.8 * BM25 + 0.2 * log(1+upvotes)
        # doc         = searcher.doc(h.doc)
        # lucene_score = h.score
        # upvotes      = float(doc.get("reddit_score") or 0)
        # final_score  = 0.8 * lucene_score + 0.2 * math.log1p(upvotes)

        # ec scoring method
        doc          = searcher.doc(h.doc)
        lucene_score = h.score
        upvotes      = float(doc.get("reddit_score") or 0)
        pagerank     = float(doc.get("pagerank") or 0)

        if rank_method == "relevance":
            final_score = lucene_score
        elif rank_method == "upvotes":
            final_score = upvotes
        # elif rank_method == "pagerank":
        #     final_score = pagerank
        else:  # default to combined
            final_score = 0.8 * lucene_score + 0.2 * math.log1p(upvotes)
        
        author = doc.get("author")
        if not author:
            author = "blank"                          # deleted user, etc.

        results.append({
            "final"     : final_score,
            "lucene"    : lucene_score,
            "title"     : doc.get("title") or "",
            "subreddit" : doc.get("subreddit") or "",
            "author"    : author,
            "url"       : doc.get("url") or "#"
        })

    results.sort(key=lambda r: r["final"], reverse=True)
    if results:
        print("Sample result:", results[0])
    return render_template("results.html", q=qstring, hits=results[:10])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
