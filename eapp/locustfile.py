from locust import HttpUser, task, between

class LibraryUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def view_homepage(self):
        self.client.get('/')

    @task(2)
    def search_books(self):
        self.client.get('/?kw=Python')

    @task(1)
    def view_details(self):
        self.client.get('/sach/1')