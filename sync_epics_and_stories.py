import os
import re
import yaml
import requests
from requests.auth import HTTPBasicAuth

JIRA_URL = os.environ.get("JIRA_URL")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

FILE_PATH = "jira-tasks/epic-breakdown.md" # Sửa lại cho đúng đường dẫn file .md của bạn nếu đặt ở root

def parse_markdown_with_front_matter(filepath):
    """Đọc file, tự động loại bỏ ký tự BOM ẩn và dấu xuống dòng Windows (CRLF)"""
    if not os.path.exists(filepath):
        print(f"Không tìm thấy file: {filepath}")
        return None, None
        
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()
    
    content = content.replace("\r\n", "\n")
    
    parts = content.split("---\n")
    if len(parts) >= 3 and content.startswith("---"):
        yaml_text = parts[1]
        body = "---\n".join(parts[2:]).strip()
        try:
            metadata = yaml.safe_load(yaml_text) or {}
            return metadata, body
        except Exception as e:
            print(f"Lỗi cú pháp YAML trong Front Matter: {e}")
            return {}, content
            
    return {}, content

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
    
    fr_descriptions = {}
    fr_match = re.search(r"###\s+Functional\s+Requirements\n(.*?)(?=\n###|\Z)", markdown_body, re.DOTALL | re.IGNORECASE)
    if fr_match:
        lines = fr_match.group(1).strip().split("\n")
        for line in lines:
            m = re.match(r"^(FR\d+):\s*(.*)", line.strip())
            if m:
                fr_id = m.group(1)
                fr_desc = m.group(2).strip()
                fr_descriptions[fr_id] = fr_desc

    coverage_match = re.search(r"###\s+FR\s+Coverage\s+Map\n(.*?)(?=\n###|\Z)", markdown_body, re.DOTALL | re.IGNORECASE)
    if coverage_match:
        lines = coverage_match.group(1).strip().split("\n")
        for line in lines:
            m = re.match(r"^(FR\d+):\s*(Epic\s*\d+)\s*-\s*(.*)", line.strip())
            if m:
                fr_id = m.group(1)
                epic_ref = m.group(2).strip()
                summary_en = m.group(3).strip()
                
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
    # Thêm dòng này để kiểm tra xem script có nhận được thông tin từ GitHub Secrets không
    print(f"DEBUG - JIRA_URL: {JIRA_URL}, JIRA_EMAIL: {JIRA_EMAIL}")

    metadata, body = parse_markdown_with_front_matter(FILE_PATH)
    if not metadata:
        return
    
    project_key = metadata.get("projectKey")
    if not project_key:
        print("Lỗi: Thiếu 'projectKey' trong Front Matter.")
        return

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
        epic_id = epic["id"]
        existing_epic_key = metadata["jiraKeys"]["epics"].get(epic_id)
        
        # Payload mặc định kèm trường customfield_10011 (Epic Name) cho Classic project
        payload_epic = {
            "fields": {
                "project": {"key": project_key},
                "summary": epic["summary"],
                "description": epic["description"],
                "issuetype": {"name": "Epic"},
                "customfield_10011": epic["summary"] # Epic Name Field
            }
        }
        
        if existing_epic_key:
            print(f"Cập nhật {epic_id} ({existing_epic_key})...")
            url = f"{JIRA_URL}/rest/api/2/issue/{existing_epic_key}"
            res = requests.put(url, headers=headers, auth=auth, json={
                "fields": {
                    "summary": epic["summary"], 
                    "description": epic["description"],
                    "customfield_10011": epic["summary"]
                }
            })
            if res.status_code != 204:
                # Nếu update lỗi do customfield_10011, thử lại không có nó
                if "customfield_10011" in res.text:
                    requests.put(url, headers=headers, auth=auth, json={
                        "fields": {"summary": epic["summary"], "description": epic["description"]}
                    })
        else:
            print(f"Tạo mới {epic_id} trên Jira...")
            url = f"{JIRA_URL}/rest/api/2/issue"
            res = requests.post(url, headers=headers, auth=auth, json=payload_epic)
            
            # Thử lại không có customfield_10011 nếu Jira báo lỗi không hỗ trợ trường này (Team-managed)
            if res.status_code != 201 and "customfield_10011" in res.text:
                print(f"-> Thử lại tạo mới {epic_id} không có trường Epic Name (Team-managed)...")
                payload_epic["fields"].pop("customfield_10011", None)
                res = requests.post(url, headers=headers, auth=auth, json=payload_epic)
                
            if res.status_code == 201:
                new_key = res.json()["key"]
                metadata["jiraKeys"]["epics"][epic_id] = new_key
                has_changes = True
                print(f"✅ Đã tạo Epic {epic_id} -> {new_key}")
            else:
                print(f"❌ Lỗi khi tạo Epic {epic_id}: {res.status_code} - {res.text}")

    epic_keys_map = metadata["jiraKeys"]["epics"]

    # ================= PART 2: ĐỒNG BỘ STORY =================
    stories = extract_stories(body)
    for story in stories:
        story_id = story["id"]
        epic_ref = story["epic_ref"]
        existing_story_key = metadata["jiraKeys"]["stories"].get(story_id)
        
        parent_epic_key = epic_keys_map.get(epic_ref)
        
        payload_story = {
            "fields": {
                "project": {"key": project_key},
                "summary": story["summary"],
                "description": story["description"],
                "issuetype": {"name": "Story"}
            }
        }
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
                
            res = requests.put(url, headers=headers, auth=auth, json=update_payload)
            if res.status_code != 204:
                print(f"❌ Lỗi khi cập nhật Story {story_id}: {res.status_code} - {res.text}")
        else:
            print(f"Tạo mới Story {story_id} liên kết với {epic_ref} ({parent_epic_key})...")
            url = f"{JIRA_URL}/rest/api/2/issue"
            res = requests.post(url, headers=headers, auth=auth, json=payload_story)
            if res.status_code == 201:
                new_key = res.json()["key"]
                metadata["jiraKeys"]["stories"][story_id] = new_key
                has_changes = True
                print(f"✅ Đã tạo Story {story_id} -> {new_key}")
            else:
                print(f"❌ Lỗi khi tạo Story {story_id}: {res.status_code} - {res.text}")

    if has_changes:
        update_markdown_file(FILE_PATH, metadata, body)
        print("Đã cập nhật toàn bộ khóa Jira thành công.")

if __name__ == "__main__":
    sync_all()