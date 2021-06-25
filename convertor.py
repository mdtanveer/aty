import jmespath
import json
from mergedeep import merge
import os

class ProjectToPlannerConvertor:
    def __init__(self, projectId, rel_dir):
        self.rel_dir = rel_dir
        self.projectId = projectId

    def get_tasks_dict(self, jsonfile, conversionfile):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       convertor = open(conversionfile).readlines() 
       query = f"[].[id, {{planId:'{self.projectId}'" + ",".join(map(lambda l: "{0}:{1}".format(*l.strip().split(',')), convertor)) + "}]"
       return dict(jmespath.search(query, jsondata))

    def get_resources(self, jsonfile):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = "[].[id, aadId]"
       return dict(jmespath.search(query, jsondata))

    def get_assignments(self, jsonfile):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = "[].[taskId, resourceId]"
       return jmespath.search(query, jsondata)

    def get_project(self, jsonfile):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = "{owner:project.projectManagerAadId, title:project.name}"
       return jmespath.search(query, jsondata)

    def get_buckets(self, jsonfile):
       jsonfile = os.path.join(self.rel_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = f"[].[id, {{name:name, planId:'{self.projectId}', orderHint:' !'}}]"
       return dict(jmespath.search(query, jsondata))

    def get_tasks(self):
       # get dict with id as key and json as key
       tasks_dict = self.get_tasks_dict("tasks.json", "convertors/task.csv")
       resid2aadid_dict = self.get_resources("resources.json")
       taskid2resid_kv = self.get_assignments("assignments.json")

       taskid2aadid_kv = [{k:{'assignments':{resid2aadid_dict[v]:{"@odata.type":"#microsoft.graph.plannerAssignment","orderHint":" !"}}}} for k,v in taskid2resid_kv]
       taskid2aadid_kv = merge(*taskid2aadid_kv)
       tasks_final = merge(tasks_dict, taskid2aadid_kv)
       for k,v in tasks_final.items():
           mod = False
           newv = dict(v)
           for k1,v1 in v.items():
               if v1 == "" or v1 == None:
                   del newv[k1]
                   mod = True
           if mod:
               tasks_final[k] = newv
       return tasks_final

    def write_to_files(self):
        data = self.get_project("project.json")
        with open(f"{self.rel_dir}/planner-project.json", "w") as fout:
            fout.write(json.dumps(data, indent=4))
        data = self.get_buckets("buckets.json")
        with open(f"{self.rel_dir}/planner-buckets.json", "w") as fout:
            fout.write(json.dumps(data, indent=4))
        data = self.get_tasks()
        with open(f"{self.rel_dir}/planner-tasks.json", "w") as fout:
            fout.write(json.dumps(data, indent=4))

rel_dir = "json"
projectId = "7575f8b2-3989-4878-86e2-d65c434c4562"
convertor = ProjectToPlannerConvertor(projectId.upper(), rel_dir)
convertor.write_to_files()
