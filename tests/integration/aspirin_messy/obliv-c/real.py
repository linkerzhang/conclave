import os
import sys

import conclave.lang as cc
from conclave import generate_code, dispatch_jobs, workflow
from conclave.utils import defCol
from conclave.config import CodeGenConfig, OblivcConfig


def protocol_mpc():
    pid_col_meds = "0"
    med_col_meds = "4"
    date_col_meds = "7"

    pid_col_diags = "8"
    diag_col_diags = "16"
    date_col_diags = "18"

    num_med_cols = 8
    num_diag_cols = 13

    left_medication_cols = [defCol(str(i), "INTEGER", [1]) for i in range(num_med_cols)]
    left_medication = cc.create("left_medication", left_medication_cols, {1})
    left_diagnosis_cols = [defCol(str(i + num_med_cols), "INTEGER", [1]) for i in range(num_diag_cols)]
    left_diagnosis = cc.create("left_diagnosis", left_diagnosis_cols, {1})
    left_keys = cc.union(left_medication, left_diagnosis, "left_pids", pid_col_meds, pid_col_diags)

    right_medication_cols = [defCol(str(i), "INTEGER", [2]) for i in range(num_med_cols)]
    right_medication = cc.create("right_medication", right_medication_cols, {2})
    right_diagnosis_cols = [defCol(str(i + num_med_cols), "INTEGER", [2]) for i in range(num_diag_cols)]
    right_diagnosis = cc.create("right_diagnosis", right_diagnosis_cols, {2})
    right_keys = cc.union(right_medication, right_diagnosis, "right_pids", pid_col_meds, pid_col_diags)

    left_shared_pids = cc._pub_intersect(
        left_keys, "a_left_shared_pids", pid_col_meds, host='10.10.10.17')
    cc._persist(left_shared_pids, "a_left_shared_pids")
    right_shared_pids = cc._pub_intersect(
        right_keys, "a_right_shared_pids", pid_col_meds, is_server=False, host='10.10.10.17')
    cc._persist(right_shared_pids, "a_right_shared_pids")

    left_medication_proj = cc.project(left_medication, "left_medication_proj",
                                      [pid_col_meds, med_col_meds, date_col_meds])
    left_medication_shared = cc.filter_by(left_medication_proj, "left_medication_shared", pid_col_meds,
                                          left_shared_pids)

    left_diagnosis_proj = cc.project(left_diagnosis, "left_diagnosis_proj",
                                     [pid_col_diags, diag_col_diags, date_col_diags])
    left_diagnosis_shared = cc.filter_by(left_diagnosis_proj, "left_diagnosis_shared", pid_col_diags, left_shared_pids)

    right_medication_proj = cc.project(right_medication, "right_medication_proj",
                                       [pid_col_meds, med_col_meds, date_col_meds])
    right_medication_shared = cc.filter_by(right_medication_proj, "right_medication_shared", pid_col_meds,
                                           right_shared_pids)

    right_diagnosis_proj = cc.project(right_diagnosis, "right_diagnosis_proj",
                                      [pid_col_diags, diag_col_diags, date_col_diags])
    right_diagnosis_shared = cc.filter_by(right_diagnosis_proj, "right_diagnosis_shared", pid_col_diags,
                                          right_shared_pids)

    left_join = cc._pub_join(left_medication_shared, "left_join", pid_col_meds,
                             other_op_node=left_diagnosis_shared, host='10.10.10.17')
    right_join = cc._pub_join(right_medication_shared, "right_join", pid_col_meds, is_server=False,
                              other_op_node=right_diagnosis_shared, host='10.10.10.17')
    joined = cc.concat_cols([left_join, right_join], "joined", use_mult=True)

    # do filters after the join
    cases = cc.cc_filter(joined, "cases", date_col_diags, "<", other_col_name=date_col_meds)
    aspirin = cc.cc_filter(cases, "aspirin", med_col_meds, "==", scalar=1)
    heart_patients = cc.cc_filter(aspirin, "heart_patients", diag_col_diags, "==", scalar=1)

    cc.collect(cc.distinct_count(heart_patients, "actual_mpc", pid_col_meds, use_sort=False), 1)

    return {
        left_medication,
        left_diagnosis,
        right_medication,
        right_diagnosis
    }


def protocol_local(suffix: str, pid: int):
    pid_col_meds = "0"
    med_col_meds = "4"
    date_col_meds = "7"

    pid_col_diags = "8"
    diag_col_diags = "16"
    date_col_diags = "18"

    num_med_cols = 8
    num_diag_cols = 13

    left_medication_cols = [defCol(str(i), "INTEGER", pid) for i in range(num_med_cols)]
    medication = cc.create(suffix + "_medication", left_medication_cols, {pid})
    left_diagnosis_cols = [defCol(str(i + num_med_cols), "INTEGER", pid) for i in range(num_diag_cols)]
    diagnosis = cc.create(suffix + "_diagnosis", left_diagnosis_cols, {pid})

    shared_pids = cc.create("a_{}_shared_pids".format(suffix), [defCol(pid_col_meds, "INTEGER", pid)], {pid})

    # only keep relevant columns
    medication_proj = cc.project(medication, "medication_proj", [pid_col_meds, med_col_meds, date_col_meds])
    medication_mine = cc.filter_by(medication_proj, "medication_mine", pid_col_meds, shared_pids, use_not_in=True)

    diagnosis_proj = cc.project(diagnosis, "diagnosis_proj", [pid_col_diags, diag_col_diags, date_col_diags])
    diagnosis_mine = cc.filter_by(diagnosis_proj, "diagnosis_mine", pid_col_diags, shared_pids, use_not_in=True)

    joined = cc.join(medication_mine, diagnosis_mine, "joined", [pid_col_meds], [pid_col_diags])

    cases = cc.cc_filter(joined, "cases", date_col_diags, "<", other_col_name=date_col_meds)
    aspirin = cc.cc_filter(cases, "aspirin", med_col_meds, "==", scalar=1)
    heart_patients = cc.cc_filter(aspirin, "heart_patients", diag_col_diags, "==", scalar=1)

    cc.distinct_count(heart_patients, "actual_" + suffix, pid_col_meds)

    return {medication, diagnosis}


def write_rel(job_dir, rel_name, rel, schema_header):
    print("Will write to {}/{}".format(job_dir, rel_name))
    path = "{}/{}".format(job_dir, rel_name)
    with open(path, "w") as f:
        # hack header
        f.write(schema_header + "\n")
        for row in rel:
            f.write(",".join([str(val) for val in row]) + "\n")


def read_rel(path_to_rel):
    rows = []
    with open(path_to_rel, "r") as f:
        it = iter(f.readlines())
        for raw_row in it:
            # TODO: only need to do this for first row
            try:
                split_row = [int(val) for val in raw_row.split(",")]
                rows.append([int(val) for val in split_row])
            except ValueError:
                print("skipped header")
    return rows


def local_main():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data_path = os.path.join(current_dir, "data")
    for pid in {"1", "2"}:
        # define name for the workflow
        workflow_name = "aspirin-local-test-" + pid
        # configure conclave
        conclave_config = CodeGenConfig(workflow_name, int(pid))
        conclave_config.all_pids = [int(pid)]
        oc_conf = OblivcConfig("/home/ubuntu/obliv-c/bin/oblivcc", "localhost:9000")
        conclave_config.with_oc_config(oc_conf)

        conclave_config.code_path = os.path.join("/tmp", workflow_name)
        conclave_config.input_path = data_path
        conclave_config.output_path = data_path
        suffix = "left" if pid == "1" else "right"
        # define this party's unique ID (in this demo there is only one party)
        job_queue = generate_code(lambda: protocol_local(suffix, int(pid)), conclave_config, ["obliv-c"], ["python"],
                                  apply_optimizations=False)
        dispatch_jobs(job_queue, conclave_config)

    res_mpc = read_rel(data_path + "/" + "actual_mpc_open_1.csv")
    res_left = read_rel(data_path + "/" + "actual_left.csv")
    res_right = read_rel(data_path + "/" + "actual_right.csv")
    assert len(res_mpc) == 1
    assert len(res_left) == 1
    assert len(res_right) == 1
    res = [[res_mpc[0][0] + res_left[0][0] + res_right[0][0]]]
    write_rel(data_path, "actual_open.csv", res, "1")


if __name__ == "__main__":
    workflow.run(protocol_mpc, mpc_framework="obliv-c", local_framework="python", apply_optimisations=True)

    top_pid = sys.argv[1]
    if top_pid == "1":
        local_main()
