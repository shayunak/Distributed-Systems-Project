#!/usr/bin/python3
import sys
import random

from world import log, world, HELLO_MSG

got_hello_from = []
echo_round = -1
isActive = True
leaderSelected = False
sub_tree_size = 1
parent = 0
got_announce_from = []
got_echo_message_from = []
echo_round_wave_member = 0

def generate_echo_id():
    return random.randint(1, world.network_size)

def initialize_parameters_for_each_round():
    global echo_round, sub_tree_size, parent, got_echo_message_from, echo_round_wave_member
    echo_round = echo_round + 1
    echo_round_wave_member = generate_echo_id()
    sub_tree_size = 1
    parent = 0
    got_echo_message_from = []

def exit_program():
    world.send_message(to=world.current_node, msg='exit')

def create_echo_message_to_children():
    return f"echo-{echo_round_wave_member}-{echo_round}-0"

def create_echo_message_to_parent(tree_size):
    return f"echo-{echo_round_wave_member}-{echo_round}-{tree_size}"

def create_announce_message(leader):
    return f"announce-{leader}"

def broadcast_message_to_neighbors_except_parent(message):
    for neighbor in world.neighbors:
        if neighbor != world.current_node and neighbor != parent:
            world.send_message(to= neighbor, msg= message)

def start_new_round():
    initialize_parameters_for_each_round()
    log(f"started round {echo_round} with id {echo_round_wave_member}")
    broadcast_message_to_neighbors_except_parent(message= create_echo_message_to_children())

def handle_hello_message(src):
    got_hello_from.append(src)
    if set(got_hello_from) == set(world.neighbors):
        start_new_round()

def announce_leader(leader):
    global parent
    parent = world.current_node
    print(f"The leader is node with physical name {announced_leader}")
    broadcast_message_to_neighbors_except_parent(message= create_announce_message(leader))

def decide():
    if sub_tree_size == world.network_size:
        announce_leader(world.current_node)
    else:
        start_new_round()

def check_round_completeness():
    if set(got_echo_message_from) == (set(world.neighbors) - set([world.current_node, parent])):
        if parent != 0:
            log("sending message to parent!")
            world.send_message(to=parent, msg=create_echo_message_to_parent(tree_size=sub_tree_size))
        else:
            log("Deciding!")
            decide()

def manage_echo_message_typically(from_node, hit_sub_tree_size):
    global sub_tree_size
    if from_node == parent:
        log(f"message from parent with id {parent} -> broadcasting to neighbors")
        broadcast_message_to_neighbors_except_parent(message= create_echo_message_to_children())
    else:
        got_echo_message_from.append(from_node)
        sub_tree_size = sub_tree_size + hit_sub_tree_size
        log(f"got echo message from child with id {from_node} and sub tree size is {sub_tree_size}")
    check_round_completeness()

def adopt_new_wave(from_node, hit_wave_id, hit_round):
    global echo_round, sub_tree_size, parent, got_echo_message_from, echo_round_wave_member, isActive
    echo_round = hit_round
    echo_round_wave_member = hit_wave_id
    sub_tree_size = 1
    parent = from_node
    got_echo_message_from = []
    isActive = False
    manage_echo_message_typically(parent, sub_tree_size)

def handle_echo_message(from_node, msg, hit_wave_id, hit_round, hit_sub_tree_size):
    if echo_round == -1:
        log(f"purged message ({msg}) -> echo before hello!")
        return
    if hit_round < echo_round or (hit_round == echo_round and hit_wave_id < echo_round_wave_member):
        log(f"purged message ({msg}) -> old round or smaller wave number condition!")
        return
    if hit_round == echo_round and hit_wave_id == echo_round_wave_member:
        log(f"hit by wave with id {hit_wave_id} from round {hit_round} -> same round and wave id, simple echo")
        manage_echo_message_typically(from_node, hit_sub_tree_size)
    elif hit_round > echo_round or (hit_round == echo_round and hit_wave_id > echo_round_wave_member):
        log(f"hit by wave with id {hit_wave_id} from round {hit_round} -> adopted the new wave!")
        adopt_new_wave(from_node, hit_wave_id, hit_round)

def check_announce_completeness(announced_leader):
    if set(got_announce_from) == (set(world.neighbors) - set([world.current_node, parent])):
        world.send_message(to=parent, msg=create_echo_message_to_parent(tree_size=sub_tree_size))

def handle_announce_message_from_parent(from_node, announced_leader):
    global leaderSelected, parent
    print(f"The leader is node with physical name {announced_leader}")
    leaderSelected = True
    parent = from_node
    broadcast_message_to_neighbors_except_parent(message= create_announce_message(announced_leader))
    check_announce_completeness(announced_leader)

def handle_announce_message_from_children(from_node, announced_leader):
    got_announce_from.append(from_node)
    world.send_message(to=from_node, msg= "ack")
    check_announce_completeness(announced_leader)      

def process_msg(src, msg):
    log(f"message from {src}: {msg}")

    if msg == "exit":
        sys.exit()
    elif msg == HELLO_MSG:
        handle_hello_message(src)
    elif msg == "ack" and src == parent:
        sys.exit()
    else:
        splitted_message = msg.split("-")
        if leaderSelected is False:
            if len(splitted_message) == 4 and splitted_message[0] == 'echo':
                handle_echo_message(from_node= src, msg= msg, hit_wave_id= int(splitted_message[1]), hit_round= int(splitted_message[2]), hit_sub_tree_size= int(splitted_message[3]))
            elif len(splitted_message) == 2 and splitted_message[0] == 'announce':
                handle_announce_message_from_parent(from_node= src, announced_leader= int(splitted_message[1]))
        else:
            if len(splitted_message) == 2 and splitted_message[0] == 'announce':
                handle_announce_message_from_children(from_node= src, announced_leader= int(splitted_message[1]))
