#! /usr/bin/env python
'''
Created on 08/03/2014

@author: Cristina De Saint Germain
@email: crsaintc8@gmail.com

'''
import rospy
import smach
from face_states.learn_face import learn_face
from speech_states.say_sm import text_to_say
from speech_states.listen_to import ListenToSM

# Some color codes for prints, from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
ENDC = '\033[0m'
FAIL = '\033[91m'
OKGREEN = '\033[92m'

class prepare_ask_name(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
                                input_keys=[],
                                output_keys=['tts_text','tts_wait_before_speaking'])

    def execute(self, userdata):

        userdata.tts_text = "Hi, what's your name?"
        userdata.tts_wait_before_speaking = 0

        return 'succeeded'
    
class prepare_say_name(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
                                input_keys=['name'],
                                output_keys=['tts_text','tts_wait_before_speaking'])

    def execute(self, userdata):

        userdata.tts_text = "Nice to meet you " + userdata.name
        userdata.tts_wait_before_speaking = 0

        return 'succeeded'
    
class SaveFaceSM(smach.StateMachine):
    """
    Executes a SM that learns one face. 
    The robot listen the name from the person and then learns his face. 

    Required parameters:
    No parameters.

    Optional parameters:
    No optional parameters

    No input keys.
    No output keys.
    No io_keys.

    Nothing must be taken into account to use this SM.
    """
    def __init__(self):
        smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'])

        with self:
            self.userdata.name = ''
            self.userdata.userSaid = ''
            self.userdata.grammar_name = ''
            
            # Ask for name
            smach.StateMachine.add(
                'prepare_ask_name',
                prepare_ask_name(),
                transitions={'succeeded': 'ask_name', 'aborted': 'aborted', 
                'preempted': 'preempted'})  
                        
            smach.StateMachine.add(
                'ask_name',
                text_to_say(),
                transitions={'succeeded': 'listen_name', 'aborted': 'aborted', 
                'preempted': 'preempted'}) 
            
            # Listen the name
            smach.StateMachine.add(
                'listen_name',
                ListenToSM(),
                transitions={'succeeded': 'learn_face', 'aborted': 'aborted', 
                'preempted': 'preempted'}) 
            
            # Depen que em retorni s'ha de fer un canvi de nom
          #  self.userdata.name = self.userdata.userSaid
           
            self.userdata.name = "cris"
             
            # Start learning
            smach.StateMachine.add(
                'learn_face',
                learn_face(),
                transitions={'succeeded': 'prepare_say_name', 'aborted': 'aborted', 
                'preempted': 'preempted'}) 
            
            # Say learn name
            smach.StateMachine.add(
                'prepare_say_name',
                prepare_say_name(),
                transitions={'succeeded': 'say_name', 'aborted': 'aborted', 
                'preempted': 'preempted'}) 
            
            smach.StateMachine.add(
                'say_name',
                text_to_say(),
                transitions={'succeeded': 'succeeded', 'aborted': 'aborted', 
                'preempted': 'preempted'}) 
            
           

