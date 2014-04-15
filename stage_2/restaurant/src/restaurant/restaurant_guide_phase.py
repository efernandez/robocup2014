#! /usr/bin/env python
"""
@author: Roger Boldu
"""
import rospy
import smach




from follow_me.follow_me_init import FollowMeInit
from follow_me.follow_operator import FollowOperator

"""
RESTAURANT_guide.PY

"""


SAY_FINISH_FOLLOWING= "i have finished following you"
SAY_LETS_GO=" i'M READY, WHEN YOU WANT WE CAN START"

import roslib


DISTANCE_TO_FOLLOW = 1.0
LEARN_PERSON_FLAG = True






ENDC = '\033[0m'
FAIL = '\033[91m'
OKGREEN = '\033[92m'



from speech_states.say import text_to_say
from speech_states.say_yes_or_no import SayYesOrNoSM
from speech_states.listen_and_check_word import ListenWordSM
            
SAY_OUT_FRASE= "OK IM GOING OUT"
COMPROVATE_GO_OUT="DO YOU WANT TO GO OUT?"




class init_var(smach.State):

    def __init__(self):
        smach.State.__init__(
            self,
            outcomes=['succeeded', 'aborted','preempted'],input_keys=['standard_error'],output_keys=['standard_error'])

    def execute(self, userdata):
        rospy.loginfo(OKGREEN+"I'M in the second part of the follow_me"+ENDC)
        rospy.sleep(2)
        userdata.standard_error="Dummy"
        return 'succeeded'
     

class dummy_listen(smach.State):
    def __init__(self):
        smach.State.__init__(
                            self,
                            outcomes=['succeeded', 'aborted','preempted'],input_keys=[],output_keys=[])

    def execute(self, userdata):
        while (1):
            if self.preempt_requested():
                return 'preempted'
            
        return 'succeeded'
    

class learn_person (smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','preempted','aborted'])
    def execute(self):
        rospy.loginfo("im learning a face")
        return 'succeeded'
        
        
        
        
class ListenOperator_dummy(smach.State):
    # gets called when ANY child state terminates
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','preempted','aborted'])
    def execute(self):
        rospy.loginfo("im dummy listen the operator")
        return 'succeeded'
        
def child_term_cb(outcome_map):

    # terminate all running states if walk_to_poi finished with outcome succeeded
    if outcome_map['CHECK_DOOR'] == 'succeeded':
        rospy.loginfo(OKGREEN + "the door its open" + ENDC)
        return True
    
    if outcome_map['LISTEN_OPERATOR_FOR_EXIT'] == 'succeeded':
        rospy.loginfo(OKGREEN + "the operator say me go out" + ENDC)
        return True

    # in all other case, just keep running, don't terminate anything
    return False

def out_cb(outcome_map):
    if outcome_map['LISTEN_OPERATOR_FOR_EXIT'] == 'succeeded':
        return 'DOOR_OPEN'    
    elif outcome_map['CHECK_DOOR'] == 'succeeded':
        return 'OPERATOR'    

    return 'aborted'


#I will be hear waiting for the instruction to go out
class restaurantGuide(smach.StateMachine):



    def __init__(self):
        smach.StateMachine.__init__(self,
                                    outcomes=['succeeded', 'preempted', 'aborted'],
                                    output_keys=['standard_error'])
        
        with self:
            self.userdata.tts_wait_before_speaking=0
            self.userdata.tts_text=None
            self.userdata.tts_lang=None
            self.userdata.standar_error="ok"
            
            smach.StateMachine.add('INIT_VAR',
                                   init_var(),
                                   transitions={'succeeded': 'LEARN_PERSON',
                                                'aborted': 'aborted','preempted':'preempted'})
            
            smach.StateMachine.add('LEARN_PERSON',
                       learn_person(),
                       transitions={'succeeded': 'CONCURRENCE',
                                    'aborted': 'LEARN_PERSON','preempted':'preempted'})
            
            
                        # it says i'm STARTING FOLLOWING YOU
            smach.StateMachine.add('Finished',
                                   text_to_say(SAY_LETS_GO),
                                   transitions={'succeeded': 'succeeded',
                                    'aborted': 'aborted','preempted':'preempted'})
            
            
            sm=smach.Concurrence(outcomes=['succeeded', 'Lost'],
                                   default_outcome='Lost',
                                   child_termination_cb = child_term_cb, outcome_cb=out_cb)
                
             
            with sm:
                # it follow the person infinit
                sm.add('FOLLOW_ME',
                                FollowOperator())
                # here it have to listen and put pois in the map
                sm.add('LISTEN_OPERATOR',
                                ListenOperator_dummy())
                
            smach.StateMachine.add('CONCURRENCE', sm, transitions={'succeeded': 'Finished',
                                                                   'Lost':'CONCURRENCE','preempted':'preempted'})
            
            
            # it says i'm going out
            smach.StateMachine.add('Finished',
                                   text_to_say(SAY_FINISH_FOLLOWING),
                                   transitions={'succeeded': 'succeeded',
                                    'aborted': 'aborted','preempted':'preempted'})
    

            
            
            
            
            
            
            
