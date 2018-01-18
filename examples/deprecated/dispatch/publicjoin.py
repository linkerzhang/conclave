import conclave.lang as sal
from conclave.comp import dag_only
from conclave.utils import *
import conclave.partition as part
from conclave.codegen.scotch import ScotchCodeGen
from conclave.codegen.sharemind import SharemindCodeGen, SharemindCodeGenConfig
from conclave.codegen.spark import SparkCodeGen
from conclave.codegen.python import PythonCodeGen
from conclave import generate_code, CodeGenConfig
from conclave.dispatch import dispatch_all
from conclave.net import setup_peer
import sys
import exampleutils


def testPublicJoinWorkflow():

    @dag_only
    def protocol():

        # define inputs
        colsInA = [
            defCol("a", "INTEGER", [1]),
            defCol("b", "INTEGER", [1]),
        ]
        in1 = sal.create("in1", colsInA, set([1]))
        in1.isMPC = False

        proja = sal.project(in1, "proja", ["a", "b"])
        proja.isMPC = False
        proja.out_rel.storedWith = set([1])

        colsInB = [
            defCol("c", "INTEGER", [1], [2]),
            defCol("d", "INTEGER", [2])
        ]
        in2 = sal.create("in2", colsInB, set([2]))
        in2.isMPC = False

        projb = sal.project(in2, "projb", ["c", "d"])
        projb.isMPC = False
        projb.out_rel.storedWith = set([2])

        clA = sal._close(proja, "clA", set([1, 2, 3]))
        clA.isMPC = True
        clB = sal._close(projb, "clB", set([1, 2, 3]))
        clB.isMPC = True

        persistedA = sal._persist(clA, "persistedA")
        persistedB = sal._persist(clB, "persistedB")

        keysaclosed = sal.project(clA, "keysaclosed", ["a"])
        keysaclosed.out_rel.storedWith = set([1, 2, 3])
        keysaclosed.isMPC = True
        keysbclosed = sal.project(clB, "keysbclosed", ["c"])
        keysbclosed.isMPC = True
        keysbclosed.out_rel.storedWith = set([1, 2, 3])

        keysa = sal._open(keysaclosed, "keysa", 1)
        keysa.isMPC = True
        keysb = sal._open(keysbclosed, "keysb", 1)
        keysb.isMPC = True

        indexedA = sal.index(keysa, "indexedA", "indexA")
        indexedA.isMPC = False
        indexedA.out_rel.storedWith = set([1])
        indexedB = sal.index(keysb, "indexedB", "indexB")
        indexedB.isMPC = False
        indexedB.out_rel.storedWith = set([1])

        joinedindeces = sal.join(
            indexedA, indexedB, "joinedindeces", ["a"], ["c"])
        joinedindeces.isMPC = False
        joinedindeces.out_rel.storedWith = set([1])

        indecesonly = sal.project(
            joinedindeces, "indecesonly", ["indexA", "indexB"])
        indecesonly.isMPC = False
        indecesonly.out_rel.storedWith = set([1])

        indecesclosed = sal._close(
            indecesonly, "indecesclosed", set([1, 2, 3]))
        indecesclosed.isMPC = True

        joined = sal._index_join(persistedA, persistedB, "joined",
                                 ["a"], ["c"], indecesclosed)
        joined.isMPC = True

        sal._open(joined, "opened", 1)

        # create condag
        return set([in1, in2])

    pid = int(sys.argv[1])
    workflow_name = "hybrid-join-" + str(pid)
    sm_cg_config = SharemindCodeGenConfig(
        workflow_name, "/mnt/shared", use_hdfs=False)
    codegen_config = CodeGenConfig(
        workflow_name).with_sharemind_config(sm_cg_config)
    codegen_config.code_path = "/mnt/shared/" + workflow_name
    codegen_config.input_path = "/mnt/shared"
    codegen_config.output_path = "/mnt/shared"

    exampleutils.generate_data(pid, codegen_config.output_path)

    dag = protocol()
    mapping = part.heupart(dag, ["sharemind"], ["python"])
    job_queue = []
    for idx, (fmwk, subdag, storedWith) in enumerate(mapping):
        if fmwk == "sharemind":
            job = SharemindCodeGen(codegen_config, subdag, pid).generate(
                "sharemind-" + str(idx), None)
        else:
            job = PythonCodeGen(codegen_config, subdag).generate(
                "python-" + str(idx), None)
        # TODO: this probably doesn't belong here
        if not pid in storedWith:
            job.skip = True
        job_queue.append(job)

    sharemind_config = exampleutils.get_sharemind_config(pid, True)
    sm_peer = setup_peer(sharemind_config)
    dispatch_all(None, sm_peer, job_queue)
    if pid == 1:
        expected = ['', '2,200,2001', '3,300,3001', '4,400,4001', '42,42,1001', '5,500,5001',
                    '6,600,6001', '7,700,7001', '7,800,7001', '7,900,7001', '8,1000,8001', '9,1100,9001']
        exampleutils.check_res(expected, "/mnt/shared/opened.csv")
        print("Success")

if __name__ == "__main__":

    testPublicJoinWorkflow()
