#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat March 16 11:30:00 2013

@author: Chang Long Zhu
@email: changlongzj@gmail.com
"""


import rospy
import smach
from navigation_states.get_current_robot_pose import get_current_robot_pose
from navigation_states.nav_to_coord import nav_to_coord
from navigation_states.nav_to_poi import nav_to_poi
from navigation_states.enter_room import EnterRoomSM
from speech_states.say import text_to_say
from manipulation_states.play_motion_sm import play_motion_sm
from util_states.topic_reader import topic_reader
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from emergency_situation.GeneratePDF_State import GeneratePDF_State
from util_states.image_to_cv import image_converter

#from emergency_situation.GeneratePDF_State import GeneratePDF_State

# Some color codes for prints, from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
ENDC = '\033[0m'
FAIL = '\033[91m'
OKGREEN = '\033[92m'

import random

class DummyStateMachine(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
            input_keys=[]) #todo: i have to delate de output_key

    def execute(self, userdata):
        print "Dummy state just to change to other state"  # Don't use prints, use rospy.logXXXX

        rospy.sleep(3)
        return 'succeeded'

# Class that prepare the value need for nav_to_poi
class prepare_coord_person_emergency(smach.State):
    def __init__(self):
         smach.State.__init__(self, outcomes=['succeeded','aborted', 'preempted'], 
            input_keys=['person_location'], 
            output_keys=['nav_to_coord_goal']) 

    def execute(self,userdata):
        roll, pitch, yaw = euler_from_quaternion([userdata.person_location.orientation.x,
                                userdata.person_location.orientation.y,
                                userdata.person_location.orientation.z,
                                userdata.person_location.orientation.w])
        userdata.nav_to_coord_goal = [userdata.person_location.position.x, userdata.person_location.position.y, yaw]

        return 'succeeded'

class prepare_tts(smach.State):
    def __init__(self, tts_text_phrase):
        smach.State.__init__(self, 
            outcomes=['succeeded','aborted', 'preempted'], 
            output_keys=['tts_text']) 
        self.tts_text_phrase_in = tts_text_phrase
    def execute(self, userdata):
        userdata.tts_text = self.tts_text_phrase_in

        return 'succeeded'


class Save_People_Emergency(smach.StateMachine):
    """
    Executes a SM that does the Emergency Situation's Save People SM.
    It is a SuperStateMachine (contains submachines) with these functionalities (draft):
    1. Go to Person location
    2. Ask Status
    3. Register position
    4. Save info
    What to do if fail?

    Required parameters:
    No parameters.

    Optional parameters:
    No optional parameters

    Input_keys:
    @key: person_location: person's location (Pose or PoseStamped)

    Output Keys:
        none
    No io_keys.

    Nothing must be taken into account to use this SM.
    """
    def __init__(self):
        smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'],
                                    input_keys=['person_location'])

        with self:           
            self.userdata.emergency_location = []
            self.userdata.tts_lang = 'en_US'
            self.userdata.tts_wait_before_speaking = 0

            #It should be Speech Recognition: ListenTo(?)
#             smach.StateMachine.add(
#                 'Prepare_Ask_Status',
#                 prepare_tts('Are you Ok?'),
#                 transitions={'succeeded':'Ask_Status', 'aborted':'Ask_Status', 'preempted':'Ask_Status'})
            smach.StateMachine.add(
                'Ask_Status',
                text_to_say('Are you Ok?'),
                transitions={'succeeded':'Save_Info', 'aborted':'Save_Info', 'preempted':'Save_Info'})
            #TODO: Do we have to add an SayYesOrNoSM?
            # smach.StateMachine.add(
            #     'Yes_No',
            #     SayYesOrNoSM(),
            #     transitions={'succeeded':'Register_Position', 'aborted':'Register_Position', 'preempted':'Register_Position'})
            
            #TODO: Actually Generate the PDF (TODO: Look for USB/Path...)
            #Save_Info(): Saves the emergency info and generates a pdf file
            #input_keys: emergency_location
            smach.StateMachine.add(
                'Save_Info',
                DummyStateMachine(),
                #GeneratePDF_State(),
                transitions={'succeeded':'Say_Save', 'aborted':'aborted', 'preempted':'preempted'})
             
            smach.StateMachine.add(
                'Say_Save',
                text_to_say('Information Saved, p d f is left to do REMEMBER'),
                transitions={'succeeded':'succeeded', 'aborted':'aborted', 'preempted':'preempted'})
            