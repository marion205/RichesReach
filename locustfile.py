from locust import HttpUser, task, between, events
import json
import random

class RichesReachUser(HttpUser):
    wait_time = between(1, 3)  # 1-3s think time

    def on_start(self):
        """Called when a user starts"""
        print("User starting load test")

    @task(2)  # 20% health checks
    def health_check(self):
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("mode") == "full":
                    response.success()
                else:
                    response.failure(f"Health check failed: {data}")
            else:
                response.failure(f"Health check failed with status {response.status_code}")

    @task(6)  # 60% GraphQL stocks
    def query_stocks(self):
        limit = random.randint(3, 10)
        query = f"""
        {{
          stocks(limit: {limit}) {{
            symbol
            name
            price
          }}
        }}
        """
        
        with self.client.post("/graphql", 
                            json={"query": query},
                            catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "stocks" in data["data"]:
                    stocks = data["data"]["stocks"]
                    if len(stocks) > 0:
                        response.success()
                    else:
                        response.failure("Empty stocks response")
                else:
                    response.failure(f"GraphQL failed: {data}")
            else:
                response.failure(f"GraphQL failed with status {response.status_code}")

    @task(1)  # 10% GraphQL beginner friendly
    def query_beginner_friendly(self):
        query = """
        {
          beginnerFriendlyStocks(limit: 3) {
            symbol
            name
            price
          }
        }
        """
        
        with self.client.post("/graphql", 
                            json={"query": query},
                            catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "beginnerFriendlyStocks" in data["data"]:
                    response.success()
                else:
                    response.failure(f"Beginner friendly query failed: {data}")
            else:
                response.failure(f"Beginner friendly query failed with status {response.status_code}")

    @task(1)  # 10% introspection
    def introspection(self):
        query = "{ __schema { types { name } } }"
        
        with self.client.post("/graphql", 
                            json={"query": query},
                            catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "__schema" in data["data"]:
                    response.success()
                else:
                    response.failure(f"Introspection failed: {data}")
            else:
                response.failure(f"Introspection failed with status {response.status_code}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("🚀 Load test started - monitor ECS scaling!")
    print("Target: http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com")
    print("Expected: Auto-scaling should trigger when CPU > 60%")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("✅ Load test completed!")
    print("Check CloudWatch for scaling events and performance metrics")
