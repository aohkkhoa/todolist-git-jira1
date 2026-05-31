import os
import re
import yaml
import requests
from requests.auth import HTTPBasicAuth

JIRA_URL = os.environ.get("JIRA_URL")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

FILE_PATH = "jira-tasks/epic-breakdown.md" # Đường dẫn file của bạn

def parse_markdown_with_front_matter(filepath):
    """Đọc file và tách Front Matter với phần Body"""
    if not os.path.exists(filepath):
        print(f"Không tìm thấy file: {filepath}")
        return None, None
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    
    yaml_text = match.group(1)
    body = match.group(2)
    
    metadata = yaml.safe_load(yaml_text) or {}
    return metadata, body

def extract_epics(markdown_body):
    """Trích xuất Epic từ mục ## Epic List"""
    epics = []
    parts = re.split(r"##\s+Epic\s+List", markdown_body, flags=re.IGNORECASE)
    if len(parts) < 2:
        return epics
    
    epic_section = parts[1]
    pattern = r"###\s+(Epic\s+(\d+):\s*(.*?))\n(.*?)(?=\n###|\Z)"
    matches = re.finditer(pattern, epic_section, re.DOTALL)
    
    for m in matches:
        epic_num = m.group(2).strip()
        epic_name = m.group(3).strip()
        epic_content = m.group(4).strip()
        
        desc_lines = []
        frs_covered = ""
        for line in epic_content.split("\n"):
            if "FRs covered:" in line or "**FRs covered:**" in line:
                frs_covered = line.strip()
            else:
                desc_lines.append(line)
        
        description = "\n".join(desc_lines).strip()
        if frs_covered:
            description += f"\n\n{frs_covered}"
            
        epics.append({
            "id": f"Epic {epic_num}",
            "summary": epic_name,
            "description": description
        })
    return epics

def extract_stories(markdown_body):
    """Trích xuất Story từ Functional Requirements và FR Coverage Map"""
    stories = []
    
    # 1. Lấy mô tả tiếng Việt từ Functional Requirements
    fr_descriptions = {}
    fr_match = re.search(r"###\s+Functional\s+Requirements\n(.*?)(?=\n###|\Z)", markdown_body, re.DOTALL | re.IGNORECASE)
    if fr_match:
        lines = fr_match.group(1).strip().split("\n")
        for line in lines:
            # Match dạng "FR1: Người dùng có thể..."
            m = re.match(r"^(FR\d+):\s*(.*)", line.strip())
            if m:
                fr_id = m.group(1)
                fr_desc = m.group(2).strip()
                fr_descriptions[fr_id] = fr_desc

    # 2. Lấy ánh xạ Epic và Summary tiếng Anh từ FR Coverage Map
    coverage_match = re.search(r"###\s+FR\s+Coverage\s+Map\n(.*?)(?=\n###|\Z)", markdown_body, re.DOTALL | re.IGNORECASE)
    if coverage_match:
        lines = coverage_match.group(1).strip().split("\n")
        for line in lines:
            # Match dạng "FR1: Epic 1 - Enable users to..."
            m = re.match(r"^(FR\d+):\s*(Epic\s*\d+)\s*-\s*(.*)", line.strip())
            if m:
                fr_id = m.group(1)
                epic_ref = m.group(2).strip() # "Epic 1"
                summary_en = m.group(3).strip()
                
                # Mô tả kết hợp cả tiếng Anh và tiếng Việt cho rõ ràng trên Jira
                desc_vi = fr_descriptions.get(fr_id, "")
                full_description = f"{desc_vi}\n\n*English Specs:* {summary_en}" if desc_vi else summary_en
                
                stories.append({
                    "id": fr_id,
                    "epic_ref": epic_ref,
                    "summary": f"[{fr_id}] {summary_en}",
                    "description": full_description
                })
    return stories

def update_markdown_file(filepath, metadata, body):
    yaml_string = yaml.safe_dump(metadata, default_flow_style=False, allow_unicode=True)
    new_content = f"---\n{yaml_string}---\n\n{body}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

def sync_all():
    metadata, body = parse_markdown_with_front_matter(FILE_PATH)
    if not metadata:
        return
    
    project_key = metadata.get("projectKey")
    if not project_key:
        print("Lỗi: Thiếu 'projectKey' trong Front Matter.")
        return

    # Khởi tạo cấu trúc lưu trữ khóa Jira trong Front Matter
    if "jiraKeys" not in metadata:
        metadata["jiraKeys"] = {}
    if "epics" not in metadata["jiraKeys"]:
        metadata["jiraKeys"]["epics"] = {}
    if "stories" not in metadata["jiraKeys"]:
        metadata["jiraKeys"]["stories"] = {}
        
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    has_changes = False

    # ================= PART 1: ĐỒNG BỘ EPIC =================
    epics = extract_epics(body)
    for epic in epics:
        epic_id = epic["id"] # Ví dụ: "Epic 1"
        existing_epic_key = metadata["jiraKeys"]["epics"].get(epic_id)
        
        payload_epic = {
            "fields": {
                "project": {"key": project_key},
                "summary": epic["summary"],
                "description": epic["description"],
                "issuetype": {"name": "Epic"}
            }
        }
        
        if existing_epic_key:
            print(f"Cập nhật {epic_id} ({existing_epic_key})...")
            url = f"{JIRA_URL}/rest/api/2/issue/{existing_epic_key}"
            requests.put(url, headers=headers, auth=auth, json={
                "fields": {"summary": epic["summary"], "description": epic["description"]}
            })
        else:
            print(f"Tạo mới {epic_id} trên Jira...")
            url = f"{JIRA_URL}/rest/api/2/issue"
            res = requests.post(url, headers=headers, auth=auth, json=payload_epic)
            if res.status_code == 201:
                new_key = res.json()["key"]
                metadata["jiraKeys"]["epics"][epic_id] = new_key
                has_changes = True
                print(f"Đã tạo Epic {epic_id} -> {new_key}")

    # Đọc lại metadata để chắc chắn các Epic Key mới đã được áp dụng cho phần Story tiếp theo
    epic_keys_map = metadata["jiraKeys"]["epics"]

    # ================= PART 2: ĐỒNG BỘ STORY =================
    stories = extract_stories(body)
    for story in stories:
        story_id = story["id"] # Ví dụ: "FR1"
        epic_ref = story["epic_ref"] # Ví dụ: "Epic 1"
        existing_story_key = metadata["jiraKeys"]["stories"].get(story_id)
        
        # Tìm Jira Key của Epic cha tương ứng
        parent_epic_key = epic_keys_map.get(epic_ref)
        
        payload_story = {
            "fields": {
                "project": {"key": project_key},
                "summary": story["summary"],
                "description": story["description"],
                "issuetype": {"name": "Story"}
            }
        }
        # Gắn Story vào Epic tương ứng
        if parent_epic_key:
            payload_story["fields"]["parent"] = {"key": parent_epic_key}
            
        if existing_story_key:
            print(f"Cập nhật Story {story_id} ({existing_story_key})...")
            url = f"{JIRA_URL}/rest/api/2/issue/{existing_story_key}"
            
            update_payload = {
                "fields": {
                    "summary": story["summary"],
                    "description": story["description"]
                }
            }
            if parent_epic_key:
                update_payload["fields"]["parent"] = {"key": parent_epic_key}
                
            requests.put(url, headers=headers, auth=auth, json=update_payload)
        else:
            print(f"Tạo mới Story {story_id} liên kết với {epic_ref} ({parent_epic_key})...")
            url = f"{JIRA_URL}/rest/api/2/issue"
            res = requests.post(url, headers=headers, auth=auth, json=payload_story)
            if res.status_code == 201:
                new_key = res.json()["key"]
                metadata["jiraKeys"]["stories"][story_id] = new_key
                has_changes = True
                print(f"Đã tạo Story {story_id} -> {new_key}")

    if has_changes:
        update_markdown_file(FILE_PATH, metadata, body)
        print("Đã lưu lại toàn bộ khóa Jira của Epic và Story vào file .md.")

if __name__ == "__main__":
    sync_all()