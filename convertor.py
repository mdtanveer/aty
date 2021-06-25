import jmespath
import json
from mergedeep import merge
import os
from pathlib import Path

class ProjectToPlannerConvertor:
    def __init__(self, projectId):
        self.projectId = projectId
        self.work_dir = Path.cwd().joinpath('json', self.projectId)

    def get_tasks_dict(self, jsonfile, conversionfile):
       jsonfile = os.path.join(self.work_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       convertor = open(conversionfile).readlines() 
       query = f"[].[id, {{planId:'{self.projectId}'" + ",".join(map(lambda l: "{0}:{1}".format(*l.strip().split(',')), convertor)) + "}]"
       return dict(jmespath.search(query, jsondata))

    def get_resources(self, jsonfile):
       jsonfile = os.path.join(self.work_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = "[].[id, aadId]"
       return dict(jmespath.search(query, jsondata))

    def get_assignments(self, jsonfile):
       jsonfile = os.path.join(self.work_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = "[].[taskId, resourceId]"
       return jmespath.search(query, jsondata)

    def get_project(self, jsonfile):
       jsonfile = os.path.join(self.work_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = "{owner:project.officeGroupId, title:project.name}"
       return jmespath.search(query, jsondata)

    def get_buckets(self, jsonfile):
       jsonfile = os.path.join(self.work_dir, jsonfile)
       jsondata = json.loads(open(jsonfile).read())
       query = f"[].[id, {{name:name, planId:'{self.projectId}', orderHint:' !'}}]"
       return dict(jmespath.search(query, jsondata))

    def get_tasks(self):
       # get dict with id as key and json as key
       tasks_dict = self.get_tasks_dict("tasks.json", "convertors/task.csv")
       resid2aadid_dict = self.get_resources("resources.json")
       taskid2resid_kv = self.get_assignments("assignments.json")

       taskid2aadid_kv = [{k:{'assignments':{resid2aadid_dict[v]:{"@odata.type":"#microsoft.graph.plannerAssignment","orderHint":" !"}}}} for k,v in taskid2resid_kv]
       if len(taskid2aadid_kv) > 1:
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
        with open(f"{self.work_dir}/planner-project.json", "w") as fout:
            fout.write(json.dumps(data, indent=4))
        data = self.get_buckets("buckets.json")
        with open(f"{self.work_dir}/planner-buckets.json", "w") as fout:
            fout.write(json.dumps(data, indent=4))
        data = self.get_tasks()
        with open(f"{self.work_dir}/planner-tasks.json", "w") as fout:
            fout.write(json.dumps(data, indent=4))

projectId = "b9238313-9e29-4cde-88cc-2fb4673fc4b9"
convertor = ProjectToPlannerConvertor(projectId.upper())
convertor.write_to_files()
