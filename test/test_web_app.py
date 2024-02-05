

# tests for each page:

def test_home(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"<h1>Home</h1>" in response.data

def test_about(test_client):
    response = test_client.get("/about")
    assert response.status_code == 200
    assert b"<h1>About</h1>" in response.data
