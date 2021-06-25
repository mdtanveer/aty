import requests
import json
import pyperclip
import os, logging
from pathlib import Path

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

class ProjectClient:
    def __init__(self, projectId, cdsUrl):
        clip = pyperclip.paste()
        if clip.startswith('Bearer '):
            os.environ["PROJECT_BEARER_TOKEN"] = pyperclip.paste()
        self.aad_token = os.environ["PROJECT_BEARER_TOKEN"]
        self.pcs_token = None
        self.projectId = projectId.upper()
        self.cdsUrl = cdsUrl
        self.work_dir = Path.cwd().joinpath('json', self.projectId)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def fetch_aad_token(self):
        if not self.aad_token:
            jsondata = json.load(open('json/project_auth.json'))
            x = requests.post("https://login.microsoftonline.com/common/oauth2/token",
                data=jsondata
            )
            x.raise_for_status()
            self.aad_token =  x.json()["access_token"]

    def get_headers(self):
        return {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "x-project-client-type": "ModernProjectFamily",
                "x-requested-with": "XMLHttpRequest"
            }

    def open_project(self):
        headers = self.get_headers()
        headers["authorization"] = self.aad_token
        x = requests.post("https://portfolios.officeppe.com/pss/api/v1.0/xrm/openproject",
            data=f'{{"xrmUrl":"{self.cdsUrl}","xrmProjectId":"{self.projectId}"}}',
            headers=headers
        )

        x.raise_for_status()
        data = x.json()
        self.pcs_token = data["accessToken"]
        self.pcs_url = data["projectSessionApiUrl"]
        return data

    def get_projectdata_helper(self, suffix):
        if not self.pcs_token or not self.pcs_url:
            raise
    
        headers = self.get_headers()
        headers["authorization"] = f"Bearer {self.pcs_token}"

        x = requests.get(f"{self.pcs_url}/{suffix}",
            headers=headers
        )
        x.raise_for_status()
        return x.json()

    def fetch_full_data(self):
        data = self.open_project()
        with open(self.work_dir.joinpath('project.json'), "w") as fout:
            fout.write(json.dumps(data, indent=4))
        DATA_SUFFIXES = ["tasks", "assignments", "resources", "buckets", "links", "attachments", "tasks/fields"]
        for suffix in DATA_SUFFIXES:
            filename = suffix.split("/")[-1]
            print(f"Fetching...{suffix}")
            data = self.get_projectdata_helper(suffix)
            with open(self.work_dir.joinpath(f"{filename}.json"), "w") as fout:
                fout.write(json.dumps(data, indent=4))

    def get_incremental_data(self, revId):
        return self.get_projectdata_helper(f"?$since={revId}")

def fetch_full_data():
    proj_client = ProjectClient("b9238313-9e29-4cde-88cc-2fb4673fc4b9", "https://msdefault.crm.dynamics.com")
    proj_client.fetch_full_data()

def fetch_incremental_data():
    proj_client = ProjectClient()
    #proj_client.fetch_aad_token()
    proj_client.open_project("https://msdefault.crm.dynamics.com", "b9238313-9e29-4cde-88cc-2fb4673fc4b9")
    data = proj_client.get_incremental_data("msxrm_msdefault.crm.dynamics.com_7575f8b2-3989-4878-86e2-d65c434c4562_0000000004") 
    return data

data = fetch_full_data()
