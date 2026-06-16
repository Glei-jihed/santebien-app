from locust import HttpUser, between, task


class SanteBienUser(HttpUser):
    wait_time = between(1, 3)

    @task(4)
    def list_questions(self):
        self.client.get("/api/questions?sort=recent", name="GET /api/questions")

    @task(2)
    def stats(self):
        self.client.get("/api/stats", name="GET /api/stats")

    @task(1)
    def articles(self):
        self.client.get("/api/articles", name="GET /api/articles")

    @task(1)
    def health(self):
        self.client.get("/api/health", name="GET /api/health")
