from locust import HttpUser, task, between

class ShortLinkUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def redirect_link(self):
        self.client.get("/links/testcode/redirect")
    
    @task
    def create_link(self):
        self.client.post("/links/shorten", 
            json={"original_url": "https://example.com"},
            headers={"Authorization": "Bearer test_token"}
        )
    
    @task(2)
    def get_stats(self):
        self.client.get("/stats/testcode/stats")