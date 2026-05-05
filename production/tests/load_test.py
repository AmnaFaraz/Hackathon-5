import random
from locust import HttpUser, task, between

class WebFormUser(HttpUser):
    wait_time = between(2, 10)
    weight = 3

    @task
    def submit_support_form(self):
        name = random.choice(["Ali", "Sara", "Ahmed", "Zainab"])
        email = f"user{random.randint(1,1000)}@example.com"
        subject = random.choice(["Help me", "Bug report", "Billing question"])
        category = random.choice(["general", "technical", "billing", "feedback", "bug_report"])
        
        self.client.post("/support/submit", json={
            "name": name,
            "email": email,
            "subject": subject,
            "category": category,
            "message": "This is an automated load test message to verify the stability of the AI FTE processor. It needs to be at least ten characters long."
        })

class HealthCheckUser(HttpUser):
    wait_time = between(5, 15)
    weight = 1

    @task
    def check_health(self):
        self.client.get("/health")

    @task
    def check_metrics(self):
        self.client.get("/metrics/channels")
        
if __name__ == "__main__":
    # To run: locust -f production/tests/load_test.py
    pass
