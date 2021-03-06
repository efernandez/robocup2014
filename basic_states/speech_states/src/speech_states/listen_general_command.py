#! /usr/bin/env python

import roslib
import rospy
import smach
from smach import *

from util_states.global_common import *
from std_msgs.msg import *
from speech_states.activate_asr import ActivateASR
from speech_states.read_asr import ReadASR
from speech_states.deactivate_asr import DeactivateASR

from pal_interaction_msgs.msg import *
from pal_interaction_msgs.srv import *

from speech_states.say import text_to_say
from speech_states.say_yes_or_no import SayYesOrNoSM

from pal_interaction_msgs.msg._ASREvent import ASREvent

MOVE_BASE_ACTION_NAME = 'move_base'


class ProcessCommandState(smach.State):

        def __init__(self):
                smach.State.__init__(self,
                                     outcomes=['succeeded', 'preempted', 'aborted'],
                                     input_keys=['in_heard'],
                                     output_keys=['value_heard_out'])

        def execute(self, userdata):
            userdata.value_heard_out = userdata.in_heard.tags[0].value
            return 'succeeded'


class SleepState(smach.State):

        def __init__(self,time):
                smach.State.__init__(self,
                                     outcomes=['succeeded', 'preempted', 'aborted'])

        def execute(self, userdata):
            rospy.sleep(self.time)
            return 'succeeded'


class PrintUserData(smach.State):

        '''
        This State Prints whatever you want.
        input_keys =    'userSaidData' , is the data that you want to print
        intro text =    is what you want as intro before the data.
                        Default message is '@@@@ This is the Message '
        use --> smach.StateMachine.add( 'PRINT_MESSAGE',
                                         PrintUserData('what you want as intro'),
                                         transitions = { succeeded:succeeded,
                                                         preempted:preempted},
                                         remapping = {'userSaidData':'nave_state_read'}
        '''

        def __init__(self, intro_text='@@@@ This is the Message '):
                smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], input_keys=['userSaidData'])
                self._intro_text = intro_text

        def execute(self, userdata):
                rospy.loginfo('%s: %s', self._intro_text, str(userdata.userSaidData))
                return 'succeeded'


class RecognizeCommand(smach.State):
        def __init__(self,  command_a='jacke', command_b='angy'):
            smach.State.__init__(self, outcomes=['valid_command', 'notvalid_command', 'preempted', 'aborted'], input_keys=['speechData'])
            self._command_a = command_a
            self._command_b = command_b

        def execute(self, userdata):

                # TODO: add confidence check before returning valid recognition (confirmation dialogue)
                goto_tags = [tag for tag in userdata.speechData.tags if tag.key == self._command_a]
                if goto_tags:
                    if self._command_b == goto_tags[0].value:
                        return 'valid_command'
                return 'notvalid_command'


class RecogCommand(smach.StateMachine):

        def __init__(self, GRAMMAR_NAME, command_key='finn', command_value='xxx', ask_for_confirmation=False):
                smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'])
                with self:

                        smach.StateMachine.add('ENABLE_GRAMMAR',
                                               ActivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'HEAR_COMMAND'})
 
                        smach.StateMachine.add('HEAR_COMMAND',
                                               ReadASR(),
                                               transitions={'aborted': 'HEAR_COMMAND', 'succeeded': 'PROCESS_COMMAND', 'preempted': 'preempted'},
                                               remapping={'asr_userSaid': 'userSaidData', 'asr_userSaid_tags':'userSaidTags'})
                        
                        smach.StateMachine.add('PROCESS_COMMAND',
                                               ProcessCommandState(),
                                               transitions={'succeeded': 'ASK_COMMAND_CONFIRMATION' if ask_for_confirmation else 'PRINT_MESSAGE',
                                                            'preempted': 'preempted',
                                                            'aborted': 'aborted'},
                                               remapping={'in_heard': 'userSaidData',
                                                          'value_heard_out': 'word_heard'})

                        if ask_for_confirmation:
                            smach.StateMachine.add('ASK_COMMAND_CONFIRMATION',
                                                   text_to_say('Did you say ' + userdata.word_heard + '?'),
                                                   transitions={'succeeded': 'LISTEN_COMMAND_CONFIRMATION',
                                                                'aborted': 'SLEEP_STATE',
                                                                'preempted': 'preempted'})
                            
                            smach.StateMachine.add('LISTEN_COMMAND_CONFIRMATION',
                                                   SayYesOrNoSM(),
                                                   transitions={'succeeded': 'DISABLE_GRAMMAR',
                                                                'aborted': 'SLEEP_STATE',
                                                                'preempted': 'preempted'},
                                                   remapping={'in_message_heard': 'word_heard'})

                            smach.StateMachine.add('SLEEP_STATE',
                                                   SleepState(0.5),
                                                   transitions={'succeeded': 'HEAR_COMMAND',
                                                                'preempted': 'preempted'})

                        smach.StateMachine.add('PRINT_MESSAGE',
                                               PrintUserData(),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR', 'preempted': 'preempted'})

                        smach.StateMachine.add('DISABLE_GRAMMAR',
                                               DeactivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'succeeded'})

class BringOrderObject(smach.State):

        def __init__(self):
                smach.State.__init__(self,
                                     outcomes=['succeeded', 'preempted', 'aborted'],
                                     input_keys=['userSaidTags'],
                                     output_keys=['object_name'])

        def execute(self, userdata):
            try: 
                  for tag in userdata.userSaidTags :
                    if tag.key == 'object':
                      userdata.object_name = tag.value
                  return 'succeeded'
            except:
                  print 'faaaail object'
                  return 'aborted'
              
class BringOrderLoc(smach.State):

        def __init__(self):
                smach.State.__init__(self,
                                     outcomes=['succeeded', 'preempted', 'aborted'],
                                     input_keys=['userSaidTags', 'userSaidData','location_name'],
                                     output_keys=['location_name'])

        def execute(self, userdata):
            try: 
                  for tag in userdata.userSaidTags :
                    if tag.key == 'location':
                      userdata.location_name = tag.value
                      return 'succeeded'
                  if userdata.location_name == '':
                    if 'kitchen' in userdata.userSaidData: # TODO: recorrer la lista de locations para cogerlo
                        userdata.location_name = 'kitchen'
                        return 'succeeded'
                  return 'aborted'
            except:
                  print 'faaaail location'
                  return 'aborted'
              
class askMissingInfo(smach.StateMachine):

        def __init__(self, Type, objectName, GRAMMAR_NAME='robocup/locations', command_key='finn', command_value='xxx'):
                smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'])
                
                self.userdata.dataType = Type
                self.userdata.object_name = objectName
                self.userdata.location_name = ''
                self.userdata.grammar_name = GRAMMAR_NAME
                self.userdata.tts_wait_before_speaking = 0
                self.userdata.tts_text = ''
                self.userdata.tts_lang = ''
                
                with self:

                        smach.StateMachine.add('ENABLE_GRAMMAR',
                                               ActivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'ASK_LOCATION'})
                        
                        smach.StateMachine.add('ASK_LOCATION',
                                                text_to_say("I don't know where the " + self.userdata.object_name + ' is. Do you know where could I find it?'),
                                                transitions={'succeeded': 'HEAR_COMMAND', 'aborted': 'aborted'})

                        smach.StateMachine.add('HEAR_COMMAND',
                                               ReadASR(),
                                               transitions={'aborted': 'HEAR_COMMAND', 'succeeded': 'BRING_LOCATION', 'preempted': 'preempted'},
                                               remapping={'asr_userSaid': 'userSaidData', 'asr_userSaid_tags':'userSaidTags'})
                        
                        smach.StateMachine.add('BRING_LOCATION',
                                               BringOrderLoc(),
                                               transitions={'aborted': 'HEAR_COMMAND', 'succeeded': 'PREPARATION_CONFIRM_OBJECT', 'preempted': 'preempted'},
                                               remapping={'location_name': 'location_name'})

                        smach.StateMachine.add('PREPARATION_CONFIRM_OBJECT',
                                               prepare_confirm_info(),
                                               transitions={'succeeded': 'CONFIRM_OBJECT'},
                                               remapping={'tosay':'tts_text'})
                        
                        smach.StateMachine.add('CONFIRM_OBJECT', 
                                               text_to_say(),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR', 'aborted': 'DISABLE_GRAMMAR'})     
                         
                        smach.StateMachine.add('RECOGNIZE_COMMAND', 
                                                RecognizeCommand(command_key, command_value),
                                                transitions={'notvalid_command': 'NOT_VALID_COMMAND',
                                                'valid_command': 'VALID_COMMAND', 'preempted': 'preempted', 'aborted': 'aborted'},
                                                remapping={'speechData': 'userSaidData'})
 
                        smach.StateMachine.add('VALID_COMMAND',
                                               text_to_say("Ok, understood."),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR'})
 
                        smach.StateMachine.add('NOT_VALID_COMMAND',
                                               text_to_say("I couldn't understand what you said. Can you repeat?"),
                                               transitions={'succeeded': 'HEAR_COMMAND'})
 
                        smach.StateMachine.add('DISABLE_GRAMMAR',
                                               DeactivateASR(),
                                               transitions={'succeeded': 'succeeded'})

            
class config_question(smach.State):
         
        def __init__(self):
          smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], input_keys=['cat'], output_keys=['objectList'])
 
        def execute(self, userdata):
          from translator import get_category_list
          userdata.objectList = get_category_list(Category=userdata.cat)
          print get_category_list(Category=userdata.cat)
          return 'succeeded'

class prepare_ask_info(smach.State):
         
        def __init__(self):
          smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], 
                               input_keys=['cat', 'objectList'], output_keys=['objectList', 'tosay'])
 
        def execute(self, userdata):
          userdata.tosay = ('You asked me for a ' + userdata.cat + '. I could bring you ' + 
                            str(userdata.objectList) + '. which ' + userdata.cat + ' do you prefer?')
          return 'succeeded'

class prepare_confirm_info(smach.State):
         
        def __init__(self):
          smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], 
                               input_keys=['location_name'], output_keys=['tosay'])
 
        def execute(self, userdata):
          userdata.tosay = ("Okay! I'll go to " + userdata.location_name)
          return 'succeeded'

class askCategory(smach.StateMachine):

        def __init__(self, GRAMMAR_NAME='categories', command_key='finn', command_value='xxx'):
                smach.StateMachine.__init__(self, outcomes = ['succeeded', 'preempted', 'aborted'])
                
                GRAMMAR_NAME='gpsr/' + GRAMMAR_NAME
                
                self.userdata.cat = GRAMMAR_NAME
                self.userdata.objectList = []
                self.userdata.location_name = ''
                self.userdata.grammar_name = GRAMMAR_NAME
                self.userdata.tts_wait_before_speaking = 0
                self.userdata.tts_text = ''
                self.userdata.tts_lang = ''
                
                with self:

                        smach.StateMachine.add('CONFG_QUESTION',
                                                config_question(),
                                                transitions={'succeeded': 'ENABLE_GRAMMAR'},
                                                remapping={'cat': 'cat', 'objectList': 'objectList'})

                        smach.StateMachine.add('ENABLE_GRAMMAR',
                                               ActivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'PREPARATION_ASK_INFO'})

                        smach.StateMachine.add('PREPARATION_ASK_INFO',
                                               prepare_ask_info(),
                                               transitions={'succeeded': 'ASK_INFO'},
                                               remapping={'tosay':'tts_text'})
                        
                        smach.StateMachine.add('ASK_INFO',
                                               text_to_say(),
                                               transitions={'succeeded': 'HEAR_COMMAND_OBJECT',
                                                            'aborted': 'aborted'})
                     
                        smach.StateMachine.add('HEAR_COMMAND_OBJECT',
                                               ReadASR(),
                                               transitions={'aborted': 'HEAR_COMMAND_OBJECT', 'succeeded': 'BRING_ORDER', 'preempted': 'preempted'},
                                               remapping={'asr_userSaid': 'userSaidData', 'asr_userSaid_tags':'userSaidTags'})

                        smach.StateMachine.add('BRING_ORDER',
                                               BringOrderObject(),
                                               transitions={'aborted': 'HEAR_COMMAND_OBJECT', 'succeeded': 'PREPARATION_CONFIRM_OBJECT', 'preempted': 'preempted'})
                                               
                        smach.StateMachine.add('PREPARATION_CONFIRM_OBJECT',
                                               prepare_confirm_info(),
                                               transitions={'succeeded': 'CONFIRM_OBJECT'},
                                               remapping={'tosay':'tts_text'})
                        
                        smach.StateMachine.add('CONFIRM_OBJECT', 
                                               text_to_say(),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR', 'aborted': 'DISABLE_GRAMMAR'})


                        smach.StateMachine.add('RECOGNIZE_COMMAND', 
                                               RecognizeCommand(command_key, command_value),
                                               transitions={'notvalid_command': 'NOT_VALID_COMMAND',
                                                            'valid_command': 'VALID_COMMAND',
                                                            'preempted': 'preempted',
                                                            'aborted': 'aborted'},
                                               remapping={'speechData': 'userSaidData'})

                        smach.StateMachine.add('VALID_COMMAND',
                                               text_to_say("Ok, understood."),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR'})

                        smach.StateMachine.add('NOT_VALID_COMMAND',
                                               text_to_say("Sorry, I couldn't understand what you said. Can you repeat?"),
                                               transitions={'succeeded': 'HEAR_COMMAND_OBJECT'})

                        smach.StateMachine.add('DISABLE_GRAMMAR',
                                               DeactivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'succeeded' })
                        

class prepare_ask_info_loc(smach.State):
         
        def __init__(self):
          smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], 
                               input_keys=['cat', 'locList'], output_keys=['locList', 'tosay'])
 
        def execute(self, userdata):
          userdata.tosay = ('You said a ' + userdata.cat + '. I could go to ' + 
                                       ', '.join(userdata.locList) + '. Which ' + userdata.cat + ' do you prefer?')
                                               
          return 'succeeded'
                        
class config_loc_question(smach.State):
        
        def __init__(self):
          smach.State.__init__(self, outcomes=['succeeded', 'preempted', 'aborted'], input_keys=['cat'], output_keys=['locList'])

        def execute(self, userdata):
          from translator import get_loc_category_list
          userdata.locList = get_loc_category_list(Category=userdata.cat)
          return 'succeeded'

class askCategoryLoc(smach.StateMachine):

        def __init__(self, GRAMMAR_NAME='categories', command_key='finn', command_value='xxx'):
                smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'])
                
                GRAMMAR_NAME='gpsr/' + GRAMMAR_NAME
                
                self.userdata.cat = GRAMMAR_NAME
                self.userdata.objectList = []
                self.userdata.locList = []
                self.userdata.location_name = ''
                self.userdata.grammar_name = GRAMMAR_NAME
                self.userdata.tts_wait_before_speaking = 0
                self.userdata.tts_text = ''
                self.userdata.tts_lang = ''
                
                with self:

                        smach.StateMachine.add('CONFG_QUESTION',
                                                config_loc_question(),
                                                transitions={'succeeded': 'ENABLE_GRAMMAR'},
                                                remapping={'DataType': 'DataType', 'locList': 'locList'})

                        smach.StateMachine.add('ENABLE_GRAMMAR',
                                               ActivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'PREPARATION_ASK_INFO'})
                         

                        smach.StateMachine.add('PREPARATION_ASK_INFO',
                                               prepare_ask_info_loc(),
                                               transitions={'succeeded': 'ASK_INFO'},
                                               remapping={'tosay':'tts_text'})

                        smach.StateMachine.add('ASK_INFO',
                                               text_to_say(),
                                               transitions={'succeeded': 'HEAR_COMMAND',
                                                            'aborted': 'aborted'})


                        smach.StateMachine.add('HEAR_COMMAND',
                                               ReadASR(),
                                               transitions={'aborted': 'HEAR_COMMAND', 'succeeded': 'BRING_ORDER', 'preempted': 'preempted'},
                                               remapping={'asr_userSaid': 'userSaidData', 'asr_userSaid_tags':'userSaidTags'})

                        smach.StateMachine.add('BRING_ORDER',
                                               BringOrderLoc(),
                                               transitions={'aborted': 'HEAR_COMMAND', 'succeeded': 'PREPARATION_CONFIRM_OBJECT', 'preempted': 'preempted'})
                                               
                        smach.StateMachine.add('PREPARATION_CONFIRM_OBJECT',
                                               prepare_confirm_info(),
                                               transitions={'succeeded': 'CONFIRM_OBJECT'},
                                               remapping={'tosay':'tts_text'})
                        
                        smach.StateMachine.add('CONFIRM_OBJECT', 
                                               text_to_say(),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR', 'aborted': 'DISABLE_GRAMMAR'})

                        smach.StateMachine.add('RECOGNIZE_COMMAND',
                                               RecognizeCommand(command_key, command_value),
                                               transitions={'notvalid_command': 'NOT_VALID_COMMAND',
                                                            'valid_command': 'VALID_COMMAND',
                                                            'preempted': 'preempted',
                                                            'aborted': 'aborted'},
                                               remapping={'speechData': 'userSaidData'})

                        smach.StateMachine.add('VALID_COMMAND',
                                               text_to_say("Ok, understood."),
                                               transitions={'succeeded': 'DISABLE_GRAMMAR'})

                        smach.StateMachine.add('NOT_VALID_COMMAND',
                                               text_to_say("Sorry, I couldn't understand what you said. Can you repeat?"),
                                               transitions={'succeeded': 'HEAR_COMMAND'})

                        smach.StateMachine.add('DISABLE_GRAMMAR',
                                               DeactivateASR(GRAMMAR_NAME),
                                               transitions={'succeeded': 'succeeded' })
                        

