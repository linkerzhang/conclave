import salmon.comp as comp
import salmon.dag as saldag
import salmon.partition as part
from salmon.codegen.python import PythonCodeGen
from salmon.codegen.sharemind import SharemindCodeGen
from salmon.codegen.spark import SparkCodeGen
from salmon.config import CodeGenConfig
from salmon.dispatch import dispatch_all
from salmon.net import SalmonPeer
from salmon.net import setup_peer


def generate_code(protocol, conclave_config, mpc_frameworks, local_frameworks):
    """
    Applies optimization rewrite passes to protocol, partitions resulting dag, and generates backend specific code for
    each sub-dag.
    :param protocol: protocol to compile
    :param conclave_config: conclave configuration
    :param mpc_frameworks: available mpc backend frameworks
    :param local_frameworks: available local-processing backend frameworks
    :return: queue of job objects to be executed by dispatcher
    """
    # currently only allow one local and one mpc framework
    assert len(mpc_frameworks) == 1 and len(local_frameworks) == 1

    # set up code gen config object
    if isinstance(conclave_config, CodeGenConfig):
        cfg = conclave_config
    else:
        cfg = CodeGenConfig.from_dict(conclave_config)

    # apply optimizations
    dag = comp.rewriteDag(saldag.OpDag(protocol()))
    # partition into subdags that will run in specific frameworks
    mapping = part.heupart(dag, mpc_frameworks, local_frameworks)
    # for each sub dag run code gen and add resulting job to job queue
    job_queue = []
    for job_num, (framework, sub_dag, stored_with) in enumerate(mapping):
        print(job_num, framework)
        if framework == "sharemind":
            name = "{}-sharemind-job-{}".format(cfg.name, job_num)
            job = SharemindCodeGen(cfg, sub_dag, cfg.pid).generate(
                name, cfg.output_path)
            job_queue.append(job)
        elif framework == "spark":
            name = "{}-spark-job-{}".format(cfg.name, job_num)
            job = SparkCodeGen(cfg, sub_dag).generate(name,
                                                      cfg.output_path)
            job_queue.append(job)
        elif framework == "python":
            name = "{}-python-job-{}".format(cfg.name, job_num)
            job = PythonCodeGen(cfg, sub_dag).generate(name,
                                                       cfg.output_path)
            job_queue.append(job)
        else:
            raise Exception("Unknown framework: " + framework)

        # TODO: this probably doesn't belong here
        if conclave_config.pid not in stored_with:
            job.skip = True
    # return job
    return job_queue


def dispatch_jobs(job_queue: list, conclave_config: CodeGenConfig) -> None:
    """
    Dispatches jobs to respective backends.
    :param job_queue: jobs to dispatch
    :param conclave_config: conclave configuration
    """
    # if more than one party is involved in the protocol, we need a networked peer
    networked_peer = None
    if len(conclave_config.network_config["parties"].keys()) > 1:
        networked_peer = _setup_networked_peer(conclave_config.network_config)
    dispatch_all(None, networked_peer, job_queue)


def generate_and_dispatch(protocol: function, conclave_config: CodeGenConfig, mpc_frameworks: list,
                          local_frameworks: list) -> None:
    """
    Calls generate_code to generate code from protocol and :func:`~salmon.__init__.dispatch_jobs` to
    dispatch it.
    """
    job_queue = generate_code(protocol, conclave_config, mpc_frameworks, local_frameworks)
    dispatch_jobs(job_queue)


def _setup_networked_peer(network_config: CodeGenConfig) -> SalmonPeer:
    return setup_peer(network_config)
