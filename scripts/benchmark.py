import time
import requests
import json

API_URL = "http://127.0.0.1:8001"

def run_query(name: str, message: str):
    print(f"--- Running {name} ---")
    start = time.time()
    try:
        response = requests.post(
            f"{API_URL}/chat", 
            data={"message": message},
            timeout=120
        )
        end = time.time()
        elapsed = end - start
        if response.status_code == 200:
            print(f"SUCCESS: {elapsed:.2f}s")
            # print(f"Response: {response.json().get('reply', '')[:100]}...\n")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
        return elapsed
    except Exception as e:
        print(f"ERROR: {e}")
        return -1.0

if __name__ == "__main__":
    print("Wait for server to be ready...")
    # Health check
    for _ in range(5):
        try:
            r = requests.get(f"{API_URL}/health")
            if r.status_code == 200:
                print("Server is up!")
                break
        except:
            pass
        time.sleep(1)
        
    queries = {
        "Chat (Hello)": "Hello, how are you?",
        "RAG (Procedure)": "What is the procedure for maintenance?",
        "Document (Generate DOCX)": "Generate a maintenance report in DOCX format."
    }
    
    results = {}
    for name, msg in queries.items():
        # run twice, once to warmup, once to measure
        print(f"Warmup {name}...")
        run_query(name + " Warmup", msg)
        print(f"Measure {name}...")
        results[name] = run_query(name, msg)
        
    print("\n=== BENCHMARK RESULTS ===")
    for k, v in results.items():
        print(f"{k}: {v:.2f}s")
