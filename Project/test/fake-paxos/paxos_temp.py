#!/usr/bin/env python
import sys
import socket
import struct
import math


def mcast_receiver(hostport):
  """create a multicast socket listening to the address"""
  recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  recv_sock.bind(hostport)

  mcast_group = struct.pack("4sl", socket.inet_aton(hostport[0]), socket.INADDR_ANY)
  recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_group)
  return recv_sock


def mcast_sender():
  """create a udp socket"""
  send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  return send_sock


def parse_cfg(cfgpath):
  cfg = {}
  with open(cfgpath, 'r') as cfgfile:
    for line in cfgfile:
      (role, host, port) = line.split()
      cfg[role] = (host, int(port))
  return cfg


# ----------------------------------------------------

class message():

    def __init__(self, instance, phase, content):

        self.message = {'instance': instance, 'phase': phase,
                        'content': content}

    def convert_to_bytes(self):
        return pickle.dumps(self.message)

    def convert_to_dict(self, message_in_bytes):
        self.message = pickle.loads(message_in_bytes)
        return self.message



class client():

    def __init(self, config, id):

        self.config = config
        self.id = id
        self.instance = 0

    def run(self):
        print('-> client ', id)
        s = mcast_sender()
        while True:
            for value in sys.stdin:
              value = value.strip()
              print("client: sending %s to proposers" % (value))
              msg = message()
              msg.message['instance'] = 'NOT KNOWN' #Keep a counter with for loop
              msg.message['phase'] = 'CLIENT REQUEST'
              msg.message['content'] = {'value': value}
              client_msg = msg.convert_to_bytes()
              s.sendto(client_msg, config['proposers'])
              print('client done.')


class proposer():

    def __init__(self, config, id):
        self.state ={}
        self.instance = -1
        self.id = id
        self.instance_number = 0
        self.num_acceptors = 3
        self.instance_updated = False
        self.catch_up_counter = 0



    def run(self):

        print('-> proposer', id)
        r = mcast_receiver(config['proposers'])
        while True:
            msg = message()
            m = r.recv(2**16)
            msg.convert_to_dict(m)
            self.process_message(msg)

    def catch_up_instance(self, instance):

        s = mcast_sender()
        message_catchup = message()
        message_catchup['instance'] = instance
        message_catchup['phase'] = 'catch up'
        message_catchup['content'] = {'role': 'proposer'}
        message_catchup = message_catchup.convert_to_bytes()
        s.sendto(message_catchup, config['acceptors'])




    def process_message(self, message):

        s = mcast_sender()
        s2 = mcast_sender()
        instance = int(message.message['instance'])
        phase = message.message['phase']
        content = message.message['content']

        #Update state for a generic message
        if instance > 0 and instance not in self.state:
            self.state[int(message.message['instance'])] = {'c-rnd': self.id, 'c-val': None,
                                          'v': None, 'v-rnd': 0,
                                          'v-val': 0, 'quorum1B': 0,
                                          'quorum2B': 0}

        if phase == 'CLIENT REQUEST':
            #Update State if the phase is client request
            self.instance_number += 1
            if self.instance_number not in self.states:
                self.state[self.instance_number] = {'c-rnd': self.id, 'c-val': None,
                                                        'v': None, 'v-rnd': 0,
                                                        'v-val': 0, 'quorum1B': 0,
                                                        'quorum2B': 0}
            # Request for an old instance: Not clear yet ---

            if not self.instance_updated:
                self.catch_up_instance(self.instance_number)


            self.state[self.instance_number]['v'] = message.message['content']['value']

            #Update instance ---

            self.states[self.instance_number]['c-rnd'] = self.states[num_instance]['c-rnd'] + self.max_proposers

            #Send Phase 1A message
            #shouldn't be instance but something else
            c_rnd = self.state[int(instance)]['c-rnd']
            message_1A = message()

            # Figure out how to handle the instance
            # message_1A['instance'] = instance

            message_1A['phase'] = '1A'
            message_1A['instance'] = self.instance_number
            message_1A['content'] = {'c-rnd': c_rnd}
            message_1A = message_1A.convert_to_bytes()
            s.sendto(message_1A, config['acceptors'])

        if phase == 'catch up':
            sender_instance = content['instance number']
            if self.instance_updated:
                if sender_instance > self.instance_number:
                    self.instance_number = sender_instance
            else:
                self.catch_up_counter += 1
                if sender_instance > self.instance_number:
                    self.instance_number = sender_instance
                if self.catch_up_counter == math.ceil((self.num_acceptors + 1) / 2):
                    self.catch_up_counter = 0
                    self.instance_updated = True
                    print_stuff("Instance updated")

    """        for i in range(0, self.instance_number + 1):
                if i not in self.states:
                    message_catchup = message()
                    message_catchup['instance'] = i
                    message_catchup['phase'] = 'proposer request'
                    message_catchup['content'] = {}
                    message_catchup = message_catchup.convert_to_bytes()
                    s2.sendto(message_catchup, config['proposers'])

        if phase == 'proposer request':
            if instance in self.states:
                message_proposer_update = message()
                message_proposer_update['phase'] = 'proposer update'
                message_proposer_update['instance']"""





        if phase == '1B':
            #Send Phase 2A message
            rnd = content['rnd']
            v_rnd = content['v-rnd']
            v_val = content['v-val']
            c_rnd = self.states[int(instance)]['c-rnd']
            c_val = self.states[int(instance)]['c-val']
            if rnd == self.states[instance]['c-rnd']:
                self.states[instance]['quorum1B'] += 1
            if v_rnd >= self.states[instance]['v_rnd']:
                self.states[instance]['v-rnd'] = v_rnd
                self.states[instance]['v-val'] = v_val

            if self.states[instance]['quorum1B'] >= math.ceil((self.num_acceptors+1) / 2):
                self.states[instance]['quorum1B'] = 0
                if self.states[instance]['v-rnd'] == 0:
                    self.states[instance]['c-val'] = self.states[instance]['v']
                    c_val = self.states[instance]['c-val']
                else:
                    self.states[instance]['c-val'] = self.states[instance]['v-val']
                    c_val = self.states[instance]['c-val']
                message_2A = message()
                message_2A['instance'] = instance
                message_2A['phase'] = '2A'
                message_2A['content'] = {'c-rnd': c_rnd, 'c-val': c_val}
                message_2A = message_2A.convert_to_bytes()
                s.sendto(message_2A, config['acceptors'])


        if phase == '2B':
            #Send Phase 3 message
            rnd = content['rnd']
            v_rnd = content['v-rnd']
            v_val = content['v-val']
            c_rnd = self.states[int(instance)]['c-rnd']
            c_val = self.states[int(instance)]['c-val']
            if v_rnd == c_rnd:
                self.states[instance]['quorum2B'] += 1
            if self.states[instance]['quorum2B'] >= math.ceil((self.num_acceptors+1) / 2):
                self.states[instance]['quorum2B'] = 0
                message_3 = message()
                message_3['instance'] = instance
                message_3['phase'] = '3'
                message_3['content'] = {'c-rnd': c_rnd, 'c-val': c_val}
                message_3 = message_3.convert_to_bytes()
                s.sendto(message_3, config['acceptors'])
                s.sendto(message_3, config['learners'])




        if phase == 'DECISION':



        #if phase == 'catch_up':

            #Catch up Learners


class acceptor():
    def __init__(self, config, id):
        self.state ={}
        self.instance = -1
        self.id = id
        self.instance_number = 0

    def run(self):

        print('-> acceptor', id)
        r = mcast_receiver(config['acceptors'])
        while True:
            msg = message()
            m = r.recv(2**16)
            msg.convert_to_dict(m)
            self.process_message(msg)

    def process_message(self, message):

        s = mcast_sender()
        instance = int(message.message['instance'])
        phase = message.message['phase']
        content = message.message['content']

        if instance > 0 and instance not in self.states:
            self.states[instance] = {"rnd": 0, "v-rnd": 0, "v-val": None}

        if instance > 0 and instance > self.instance_number:
            self.instance_number = instances

        if phase == '1A':
            c_rnd = content['c-rnd']
            rnd = self.states[instance]['rnd']
            v_rnd = self.states[instance]['v-rnd']
            v_val = self.states[instance]['v-val']
            if c_rnd >= self.states[instance]['rnd']:
                self.states[instance]['rnd'] = c_rnd
                message_1B = message()
                message_1B['instance'] = instance
                message_1B['phase'] = '1B'
                message_1B['content'] = {'rnd': rnd, 'v-rnd': v_rnd, 'v-val': v_val}
                message_1B = message_1B.convert_to_bytes()
                s.sendto(message_1B, config['proposers'])
        if phase == '2A':
            c_rnd = content['c-rnd']
            c_val = content['c-val']
            rnd = self.states[instance]['rnd']

            if c_rnd >= rnd:
                self.states[instance]['v-rnd'] = c_rnd
                self.states[instance]['v-val'] = c_val
                v_rnd = self.states[instance]['v-rnd']
                v_val = self.states[instance]['v-val']
                message_2B = message()
                message_2B['instance'] = instance
                message_2B['phase'] = '2B'
                message_2B['content'] = {'rnd': rnd, 'v-rnd': v_rnd, 'v-val': v_val}
                message_2B = message_2B.convert_to_bytes()
                s.sendto(message_2B, config['proposers'])

        if phase == 'catch up':

            role = content['role']
            message_catchup = message()
            message_catchup['instance'] = instance
            message_catchup['phase'] = 'catch up'
            message_2B['content'] = {'instance number': instance_number}
            message_catchup = message_catchup.convert_to_bytes()
            if role == 'proposer':
                s.sendto(message_catchup, config['proposers'])
            elif role == 'learner':
                s.sendto(message_catchup, config['learners'])


       #if phase == '3'


class learner():

    def __init__(self, config, id):
        self.state ={}
        self.instance = -1
        self.id = id
        self.instance_number = 0


    def run(self):

        print('-> learner', id)
        r = mcast_receiver(config['learners'])
        while True:
            msg = message()
            m = r.recv(2**16)
            msg.convert_to_dict(m)
            self.process_message(msg)

    def process_message(self, message):

        s = mcast_sender()
        instance = int(message.message['instance'])
        phase = message.message['phase']
        content = message.message['content']

        if phase == '3':
            if instance > 0 and instance > self.instance_number:
                self.instance_number = instance

            if instance not in self.states:
                self.states[instance] = {'v': None}

            self.states[instance]['v'] = content['c-val']
            print(content['c-val'])
            sys.stdout.flush()




# ----------------------------------------------------


def acceptor(config, id):
    print ('-> acceptor', id)
    state = {}
    r = mcast_receiver(config['acceptors'])
    s = mcast_sender()
    while True:
      msg = r.recv(2**16)
      # fake acceptor! just forwards messages to the learner
      if id == 1:
        # print "acceptor: sending %s to learners" % (msg)
        s.sendto(msg, config['learners'])


def proposer(config, id):
  print('-> proposer', id)
  r = mcast_receiver(config['proposers'])
  s = mcast_sender()
  while True:
    msg = r.recv(2**16)
    # fake proposer! just forwards message to the acceptor
    if id == 1:
      # print "proposer: sending %s to acceptors" % (msg)
      s.sendto(msg, config['acceptors'])


def learner(config, id):
  r = mcast_receiver(config['learners'])
  while True:
    msg = r.recv(2**16)
    print(msg)
    sys.stdout.flush()


def client(config, id):
  print('-> client ', id)
  s = mcast_sender()
  for value in sys.stdin:
    value = value.strip()
    print("client: sending %s to proposers" % (value))
    s.sendto(value, config['proposers'])
  print('client done.')


if __name__ == '__main__':
  cfgpath = sys.argv[1]
  config = parse_cfg(cfgpath)
  role = sys.argv[2]
  id = int(sys.argv[3])
  if role == 'acceptor':
    rolefunc = acceptor
  elif role == 'proposer':
    rolefunc = proposer
  elif role == 'learner':
    rolefunc = learner
  elif role == 'client':
    rolefunc = client
  rolefunc(config, id)
