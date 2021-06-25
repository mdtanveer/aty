import requests
import os
import json
import pickle
import logging
import pyperclip

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
    def __init__(self, projectId, planId, rel_dir):
        self.pkl_file = projectId + '.pkl'
        self.rel_dir = rel_dir
        clip = pyperclip.paste()
        if clip.startswith('Bearer '):
            os.environ["PLANNER_BEARER_TOKEN"] = pyperclip.paste()
        
        self.aad_token = os.environ["PLANNER_BEARER_TOKEN"]
        self.projectId = projectId
        self.planId = planId
        try:
            with open(self.pkl_file, 'rb') as f:
                self.state = pickle.load(f)
        except:
            self.state = PlannerClientState()
            self.state.id_lookup = {self.projectId:self.planId}

    def persist_project_metadata(json):
       plannerId = data["id"]
       etag = data["@odata.etag"]
       if projectId not in self.state.id_lookup.keys():
           self.state.id_lookup[self.projectId] = {'project':{'plannerId':'', 'plannerEtag':''}, 'tasks':{}, 'buckets':{}} 
       self.state.id_lookup[self.projectId] = plannerId
       self.state.etag_lookup[self.projectId] = etag

    def persist_project_submetadata(self, data, subentityid):
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

    def create_plan(self, jsonfile):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
       jsondata = json.load(open(jsonfile))
       x = requests.post("https://graph.microsoft.com/v1.0/planner/plans",
            data=jsondata,
            headers=self.get_headers()
       )
       x.raise_for_status()
       data = x.json()
       self.persist_project_metadata(data)
       return data

    def create_subentity(self, jsonfile, suffix, replace_ids):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
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
           self.persist_project_submetadata(data, k)

    def create_tasks(self, jsonfile):
        self.create_subentity(jsonfile, 'tasks', ['planId', 'bucketId'])

    def create_buckets(self, jsonfile):
        self.create_subentity(jsonfile, f'buckets', ['planId'])

    def __del__(self):
        with open(self.pkl_file, 'wb') as f:
            self.state = pickle.dump(self.state, f)

    def set_last_saved_revision(self, revId):
        self.state.last_saved_revision = revId
        

p = PlannerClient('7575F8B2-3989-4878-86E2-D65C434C4562', 'NVDIDs-RrUC_EGPQZD44c5UAE6ud', 'json')
p.create_buckets('planner-buckets.json')
p.create_tasks('planner-tasks.json')
p.set_last_saved_revision('msxrm_msdefault.crm.dynamics.com_7575f8b2-3989-4878-86e2-d65c434c4562_0000000034')
p = None
