from plannerclient import PlannerClient

def test_create_plan():
    p = PlannerClient('7575F8B2-3989-4878-86E2-D65C434C4562')
    p.create_buckets('planner-buckets.json')

def test_create_tasks_in_existing_plan():
    p = PlannerClient('7575F8B2-3989-4878-86E2-D65C434C4562', 'NVDIDs-RrUC_EGPQZD44c5UAE6ud', 'json')
    p.create_buckets('planner-buckets.json')
    p.create_tasks('planner-tasks.json')
    p.set_last_saved_revision('msxrm_msdefault.crm.dynamics.com_7575f8b2-3989-4878-86e2-d65c434c4562_0000000034')
