from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(1, 5)  # Simulate user think time

    @task
    def search_query(self):
        headers = {"Content-Type": "application/json"}
        payload = {
            "query": "waterproof trail running shoes for wide feet",
            "user_id": f"locust_user_{self.environment.runner.user_count}"
        }
        self.client.post("/search", json=payload, headers=headers, name="/search")