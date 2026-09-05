from agent import run_agent

request = """
Create an Excel document report about AI systems.
Include:
- Introduction
- Architecture
- Comments
"""

print(f"Running E2E test with request:\n{request}\n")
res = run_agent(request)

print(f"Status: {res.status}")
print(f"Response:\n{res.answer}")

# verify file exists and is readable
if "File:" in res.answer:
    file_path = res.answer.split("File: ")[1].split("\n")[0].strip()
    import os
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"\n[VERIFY] File {file_path} exists! Size: {size} bytes")
    else:
        print(f"\n[VERIFY] File {file_path} DOES NOT EXIST!")
