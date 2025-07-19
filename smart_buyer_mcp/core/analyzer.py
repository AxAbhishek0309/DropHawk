class ReviewAnalyzer:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def summarize_reviews(self, reviews):
        # Placeholder: Call LLM to summarize reviews
        return self.llm_client.summarize(reviews) 