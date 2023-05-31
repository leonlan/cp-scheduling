# Distributed flow shop problem

In the distributed flow shop problem (DFSP), there are $J$ jobs and $L$ production lines. 
Each line $l \in L$ consists of $|M|$ units.
Each job $j$ must be assigned to one line in $L$, on which the job
is processed on each unit $u \in M$ in sequence. The processing time
of job $j$ on unit $u$ of line $l$ is denoted by $p_{jul}$.
The objective is to minimize the makespan of the schedule, i.e., the
completion time of the last job.

The following problem characteristics are also included:

- sequence-dependent setup times
- line eligibility constraints

::: src.cp.distributed_flow_shop
