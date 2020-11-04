# Paxos

## Distributed Algorithms Project

## Running the code

### Test 1: 

In the first test each client proposes 100 values(We have 2 clients, 2 proposers, 3 acceptors, 2 learners). We would like to check that learners learn values in total order. We repeat this for cases when client proposes 1000 and 10000 values respectively.

To test the correctness in these cases we need to run from the directory "Paxos/Project/test/" the shell file: "./run.sh ./fake-paxos num_values wait_time". In our num_values are 100, 1000 and 10000. To prevent a termination before consensus protocol concludes we need to vary the sleep time between starting of clients and the execution of $KILLCMD. The wait_time variable is the number of seconds we wait before $KILLCMD. For 100 values we find that a wait_time = 5 is sufficient, for 1000 values a wait_time = 10 is sufficient and for 10000 a wait_time = 80 is sufficient.

### Test 2, 3:

In the second and third tests we wish to repeat the first test but with 2 and 1 acceptors, respectively.

 We repeat test 1 with 2 and 1 acceptors respectively. Go to the directory "Paxos/Project/test/". For test 2 run "./run_2acceptor.sh ./fake-paxos num_values wait_time" with the same wait times as in test 1. For test 3 run "./run_1acceptor.sh ./fake-paxos num_values wait_time" with the same wait times as in test 1. There is a global variable in paxos.py file in the directory  "Paxos/Project/test/fake-paxos" called num_acceptors_global. It has been set to 3 by default. For these tests this variable needs to be changed to 2 and 1, respectively, for tests 2 and 3.
 
 ### Test 4:
 
 In the fourth test we wish to repeat test 1 with % of message loss.
 
 On Ubuntu this can be done simply by running the command "./run_loss.sh ./fake-paxos num_values wait_time". We also provide the docker files to run this on Mac.
 
 ### Test 5:
 
 In test fifth test we wish to kill 1 or 2 acceptors while the values are being proposed. 
 
  Test 5 is also performed by altering global variables in the paxos.py file in the directory "Paxos/Project/test/fake-paxos". We have two global variables kill_acceptor_at_instance and kill_acceptor_id.kill_acceptor_at_instance is the variable that tells us at what instance the acceptors should be killed. This variable is set to None by default(meaning none of the acceptors will be killed). kill_acceptor_id in a list of all the ids of acceptors we wish to kill. For example if kill_acceptor_id = [2, 3], and ,kill_acceptor_at_instance = 50, then acceptors with id 2 and 3 will be killed once they receive 50 messages. So to perform test 5 vary these variables according to your preferences. Then run the shell scripts similar to test 1.



