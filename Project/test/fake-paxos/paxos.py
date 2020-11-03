#!/usr/bin/env python
import sys
import socket
import struct
import math
import pickle
from threading import Thread


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

class message_class():

    def __init__(self, instance = None, phase = None, content = None):

        self.message = {'instance': instance, 'phase': phase,
                        'content': content}

    def convert_to_bytes(self):
        return pickle.dumps(self.message)

    def convert_to_dict(self, message_in_bytes):
        self.message = pickle.loads(message_in_bytes)
        return self.message



class client_class(Thread):

    def __init__(self, config, id):

        self.config = config
        self.id = id
        self.instance = 0

    def run(self):
        print('-> client ', id)
        s = mcast_sender()
        while True:
            for value in sys.stdin:
              value = value.strip()
              msg = message_class(-1, 'CLIENT REQUEST', {'value': value})
              client_msg = msg.convert_to_bytes()
              s.sendto(client_msg, config['proposers'])
              print('client done.')


class proposer_class(Thread):

    #Proposer with id=1 is leader

    def __init__(self, config, id):
        self.states ={}
        self.instance = -1
        self.id = id
        self.instance_number = 0
        self.num_acceptors = 3
        self.instance_updated = False
        self.catch_up_counter = 0
        self.max_proposers = 1000
        if self.id == 1:
            self.leader = True
        else:
            self.leader = False

        self.val_buffer = []


    def run(self):

        print('-> proposer', id)
        r = mcast_receiver(config['proposers'])
        while True:
            msg = message_class()
            m = r.recv(2**16)
            msg.convert_to_dict(m)
            self.process_message(msg)


    def process_message(self, message):

        s = mcast_sender()
        instance = int(message.message['instance'])
        phase = message.message['phase']
        content = message.message['content']




        if phase == 'CLIENT REQUEST':
            #Update States if the phase is client request
            self.instance_number += 1
            self.states[self.instance_number] = {'c-rnd': self.id, 'c-val': None,
                                                    'v': content['value'], 'v-rnd': 0,
                                                    'v-val': 0, 'quorum1B': 0,
                                                    'quorum2B': 0, 'decided': False}

            #self.form_consensus()
            if self.leader == True:
                message_1A = message_class(instance = self.instance_number,phase = '1A' , content = {'c-rnd': self.states[self.instance_number]['c-rnd']})
                message_1A = message_1A.convert_to_bytes()
                s.sendto(message_1A, config['acceptors'])


        if phase == '1B':
            #Send Phase 2A message
            if self.leader == True:
                if content != 'FAIL!':

                    rnd = content['rnd']
                    v_rnd = content['v-rnd']
                    v_val = content['v-val']
                    c_rnd = self.states[int(instance)]['c-rnd']
                    c_val = self.states[int(instance)]['c-val']
                    print(instance, rnd, self.states[instance]['c-rnd'])
                    if rnd == self.states[instance]['c-rnd']:
                        self.states[instance]['quorum1B'] += 1
                    if v_rnd >= self.states[instance]['v-rnd']:
                        self.states[instance]['v-rnd'] = v_rnd
                        self.states[instance]['v-val'] = v_val

                    print(instance, self.states[instance]['quorum1B'])
                    if self.states[instance]['quorum1B'] >= math.ceil((self.num_acceptors+1) / 2):
                        print('quorum 1B')
                        self.states[instance]['quorum1B'] = 0
                        if self.states[instance]['v-rnd'] == 0:
                            self.states[instance]['c-val'] = self.states[instance]['v']
                            c_val = self.states[instance]['c-val']
                        else:
                            self.states[instance]['c-val'] = self.states[instance]['v-val']
                            c_val = self.states[instance]['c-val']
                        message_2A = message_class(instance, '2A', {'c-rnd': c_rnd, 'c-val': c_val})
                        message_2A = message_2A.convert_to_bytes()
                        s.sendto(message_2A, config['acceptors'])
                else:
                    self.states[instance]['c-rnd'] += self.max_proposers
                    #print(self.states[instance]['c-rnd'])
                    message_1A = message_class(instance = instance ,phase = '1A' , content = {'c-rnd': self.states[instance]['c-rnd']})
                    message_1A = message_1A.convert_to_bytes()
                    s.sendto(message_1A, config['acceptors'])
                    #print('1B Fail')


        if phase == '2B':
            #Send Phase 3 message
            if self.leader == True:
                print('recieved 2b sending 3')
                if content != 'FAIL!':
                    rnd = content['rnd']
                    v_rnd = content['v-rnd']
                    v_val = content['v-val']
                    c_rnd = self.states[int(instance)]['c-rnd']
                    c_val = self.states[int(instance)]['c-val']
                    if v_rnd == c_rnd:
                        self.states[instance]['quorum2B'] += 1
                    if self.states[instance]['quorum2B'] >= math.ceil((self.num_acceptors+1) / 2):
                        print('Consenseus!')
                        self.states[instance]['quorum2B'] = 0
                        self.val_buffer.append(c_val)
                        message_3 = message_class(instance, '3', {'c-rnd': c_rnd, 'c-val': c_val, 'val_buffer':self.val_buffer})
                        message_3 = message_3.convert_to_bytes()
                        print('sending phase 3 message')
                        s.sendto(message_3, config['acceptors'])
                        s.sendto(message_3, config['learners'])
                else:
                    self.states[instance]['c-rnd'] += self.max_proposers
                    print(self.states[instance]['c-rnd'])
                    message_1A = message_class(instance = instance ,phase = '1A' , content = {'c-rnd': self.states[instance]['c-rnd']})
                    message_1A = message_1A.convert_to_bytes()
                    s.sendto(message_1A, config['acceptors'])
                    #print('2B fail')


        if phase == '3':
            if instance not in self.states:
                self.states[instance] = {'c-rnd': self.id, 'c-val': None,
                                              'v': None, 'v-rnd': 0,
                                              'v-val': 0, 'quorum1B': 0,
                                              'quorum2B': 0}



class acceptor_class(Thread):
    def __init__(self, config, id):
        self.states ={}
        self.instance = -1
        self.id = id
        self.instance_number = 0

    def run(self):

        print('-> acceptor', id)
        r = mcast_receiver(config['acceptors'])
        while True:
            msg = message_class()
            m = r.recv(2**16)
            msg.convert_to_dict(m)
            self.process_message(msg)

    def process_message(self, message):

        s = mcast_sender()
        instance = int(message.message['instance'])
        phase = message.message['phase']
        content = message.message['content']

        if instance not in self.states:
            self.states[instance] = {"rnd": 0, "v-rnd": 0, "v-val": None}

        if instance > self.instance_number:
            self.instance_number = instance

        if phase == '1A':
            c_rnd = content['c-rnd']

            #print('c_rnd, rnd:', (c_rnd, rnd))
            if c_rnd >= self.states[instance]['rnd']:
                self.states[instance]['rnd'] = c_rnd
                message_1B = message_class(instance, '1B', {'rnd': self.states[instance]['rnd'], 'v-rnd': self.states[instance]['v-rnd'], 'v-val': self.states[instance]['v-val']})

                message_1B = message_1B.convert_to_bytes()
                s.sendto(message_1B, config['proposers'])
            else:
                message_1B = message_class(instance, '1B', 'FAIL!')
                message_1B = message_1B.convert_to_bytes()
                s.sendto(message_1B, config['proposers'])

        if phase == '2A':

            c_rnd = content['c-rnd']
            c_val = content['c-val']
            rnd = self.states[instance]['rnd']
            print('2A, rnd, c-rnd:', (self.id, rnd, c_rnd))
            if c_rnd >= rnd:
                print('recieved 2a - send 2B')
                self.states[instance]['v-rnd'] = c_rnd
                self.states[instance]['v-val'] = c_val
                v_rnd = self.states[instance]['v-rnd']
                v_val = self.states[instance]['v-val']
                message_2B = message_class(instance, '2B', {'rnd': rnd, 'v-rnd': v_rnd, 'v-val': v_val})
                message_2B = message_2B.convert_to_bytes()
                s.sendto(message_2B, config['proposers'])
            else:
                message_2B = message_class(instance, '2B', 'FAIL!')
                message_2B = message_2B.convert_to_bytes()
                s.sendto(message_2B, config['proposers'])


       #if phase == '3'


class learner_class(Thread):

    def __init__(self, config, id):
        self.states ={}
        self.instance = -1
        self.id = id
        self.instance_number = 0

        self.val_buffer = []


    def run(self):

        #print('-> learner', id)
        r = mcast_receiver(config['learners'])
        while True:
            #print('learner received')
            msg = message_class()
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
                self.states[instance] = {'val_buffer': []}

            val_buffer_recieved = content['val_buffer']

            self.states[instance]['val_buffer'] = list(set(val_buffer_recieved) - set(self.val_buffer))
            self.val_buffer = val_buffer_recieved
            for val in self.states[instance]['val_buffer']:
                print(val)
                sys.stdout.flush()





# ----------------------------------------------------


def acceptor(config, id):
    acceptor = acceptor_class(config, id)
    acceptor.run()


def proposer(config, id):
    proposer = proposer_class(config, id)
    proposer.run()


def learner(config, id):
    learner = learner_class(config, id)
    learner.run()


def client(config, id):
    client = client_class(config, id)
    client.run()


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