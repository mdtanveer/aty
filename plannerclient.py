import requests
import os
import json
import pickle
import logging
import pyperclip
from pathlib import Path

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
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

class PlannerClientState:
    def __init__(self):
        self.id_lookup = {}
        self.etag_lookup = {}
        self.last_saved_revision = None
    
class PlannerClient:
    def __init__(self, projectId, planId=None):
        self.projectId = projectId.upper()
        self.work_dir = Path.cwd().joinpath('json', self.projectId)
        self.pkl_file = self.work_dir.joinpath('state.pkl')
        clip = pyperclip.paste()
        if clip.startswith('Bearer '):
            os.environ["PLANNER_BEARER_TOKEN"] = pyperclip.paste()
        
        self.aad_token = os.environ["PLANNER_BEARER_TOKEN"]
        self.planId = planId
        try:
            with open(self.pkl_file, 'rb') as f:
                self.state = pickle.load(f)
        except:
            self.state = PlannerClientState()
            self.state.id_lookup = {self.projectId:self.planId}

    def persist_project_metadata(self, data, subentityid):
       plannerId = data["id"]
       etag = data["@odata.etag"]
       self.state.id_lookup[subentityid] = plannerId
       self.state.etag_lookup[subentityid] = etag

    def get_headers(self):
       return {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "authorization": self.aad_token,
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
            }

    def create_plan(self):
       jsonfile = self.work_dir.joinpath('planner-project.json')
       jsondata = json.load(open(jsonfile))
       assert jsondata['owner']
       x = requests.post("https://graph.microsoft.com/v1.0/planner/plans",
            data=json.dumps(jsondata),
            headers=self.get_headers()
       )
       x.raise_for_status()
       data = x.json()
       print(data)
       self.persist_project_metadata(data, self.projectId)
       return data

    def create_subentity(self, jsonfile, suffix, replace_ids):
       jsonfile = self.work_dir.joinpath(jsonfile)
       jsondata = json.load(open(jsonfile))
       for k, v in jsondata.items():
           postdata = v
           for key in replace_ids:
               postdata[key] = self.state.id_lookup[postdata[key]]
           x = requests.post(f"https://graph.microsoft.com/v1.0/planner/{suffix}",
                data=json.dumps(postdata),
                headers=self.get_headers()
           )
           x.raise_for_status()
           data = x.json()
           self.persist_project_metadata(data, k)

    def create_tasks(self):
        self.create_subentity('planner-tasks.json', 'tasks', ['planId', 'bucketId'])

    def create_buckets(self):
        self.create_subentity('planner-buckets.json', f'buckets', ['planId'])

    def __del__(self):
        with open(self.pkl_file, 'wb') as f:
            self.state = pickle.dump(self.state, f)

    def set_last_saved_revision(self, revId):
        self.state.last_saved_revision = revId
        

def create_tasks_in_existing_plan():
    p = PlannerClient('7575F8B2-3989-4878-86E2-D65C434C4562', 'NVDIDs-RrUC_EGPQZD44c5UAE6ud')
    p.create_buckets()
    p.create_tasks()
    p.set_last_saved_revision('msxrm_msdefault.crm.dynamics.com_7575f8b2-3989-4878-86e2-d65c434c4562_0000000034')
    p = None


def create_plan_and_tasks():
    p = PlannerClient('b9238313-9e29-4cde-88cc-2fb4673fc4b9')
    p.create_plan()
    p.create_buckets()
    p.create_tasks()
    p = None

def dump_state():
    p = PlannerClient('b9238313-9e29-4cde-88cc-2fb4673fc4b9')
    print(json.dumps(p.state.id_lookup, indent=4))
    print(json.dumps(p.state.etag_lookup, indent=4))

dump_state()
