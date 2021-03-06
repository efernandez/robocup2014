#! /usr/bin/env python
# vim: expandtab ts=4 sw=4
### FOLLOW_ME.PY ###
import smach
import rospy
from speech_states.say import text_to_say
"""
@author: Roger Boldu
"""
# Some color codes for prints, from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
ENDC = '\033[0m'
FAIL = '\033[91m'
OKGREEN = '\033[92m'


from speech_states.say import text_to_say
from speech_states.listen_and_check_word import ListenWordSM
from pipol_tracker_pkg.msg import personArray,person
from util_states.topic_reader import topic_reader
from face_states.new_database_and_learn import new_database_and_learn
from std_msgs.msg import Int32

Y_CALIBRARTION=0.5 # it calibrates the person that robot takes
X_CALIBRATION=1.5
TIME_TO_SPECK=5 # this are secons
SAY_GO_MIDLE="Please come in front of me"
SAY_FINISH= "OK, i have finished"
SAY_LEARN="I'm enrolling your face"


# It's only becouse i can't import the file... i can't understand
class select_ID(smach.State):

    def __init__(self, learn_face, pub): 
        smach.State.__init__(self, input_keys=['tracking_msg','in_learn_person'],
                             output_keys=['in_learn_person'],
                             outcomes=['succeeded','aborted', 'preempted','learn_face'])
        self.learn_face=learn_face
        self.pub=pub
    def execute(self, userdata):
        userdata.in_learn_person=None
        person_detect=userdata.tracking_msg
        per_aux=person()
        #per_follow=[]
        minx=X_CALIBRATION
        found =False

        for person_aux in person_detect.peopleSet :
            if (-Y_CALIBRARTION<person_aux.y<Y_CALIBRARTION) and (person_aux.targetStatus & person.VISUALLY_CONFIRMED):
                
                if person_aux.x<minx :
                    minx=person_aux.x
                    userdata.in_learn_person=person_aux
                    found=True

                
                
        
        if found :
            self.pub.publish(userdata.in_learn_person.targetId)
            rospy.loginfo(OKGREEN+"i have learned the person whit  ID  :  " 
                              + str(userdata.in_learn_person)+ENDC)
            if (self.learn_face) :
                return 'learn_face'
            else :
                return 'succeeded'

        
        userdata.in_learn_person=None
        return 'aborted'

class init_var(smach.State):

    def __init__(self): 
        smach.State.__init__(self, input_keys=[],
                             output_keys=['time_init'],
                             outcomes=['succeeded','aborted', 'preempted'])

    def execute(self, userdata):
        userdata.time_init=rospy.get_rostime()
        return 'succeeded'
    

    
class control_time(smach.State):

    def __init__(self): 
        smach.State.__init__(self, input_keys=['time_init'],
                             output_keys=['time_init'],
                             outcomes=['succeeded','lif_time'])

    def execute(self, userdata):
        if (rospy.get_rostime().secs-userdata.time_init.secs)>TIME_TO_SPECK :
            userdata.time_init.secs=rospy.get_rostime().secs
            return 'lif_time'
        return 'succeeded'
        


class LearnPerson(smach.StateMachine):
    '''
       
       Learn Person is a state that will get a ID of the person who have near, if it's in the interest area.
   
       The person have to be visual confirmed and the action service of learn face confirm the face
   '''
    def __init__(self,learn_face=False):
        smach.StateMachine.__init__(self, ['succeeded', 'preempted', 'aborted'],
                                    output_keys=['standard_error','in_learn_person'])
        self.learn_face = learn_face
        self.follow_pub = rospy.Publisher('/follow_me/id', Int32, latch=True)    
        
        with self:
            self.userdata.tts_wait_before_speaking=0
            self.userdata.tts_text=None
            self.userdata.tts_lang=None
            self.userdata.standard_error='OK'
            


            smach.StateMachine.add('INIT_VAR',
                                   init_var(),
                                   transitions={'succeeded': 'READ_TRACKER_TOPIC',
                                                'aborted': 'SAY_LIFTIME'})
            smach.StateMachine.add('SAY_LIFTIME',
                                   text_to_say(SAY_GO_MIDLE),
                                   transitions={'succeeded': 'CONTROL_TIME',
                                                'aborted': 'SAY_LIFTIME'})

            smach.StateMachine.add('CONTROL_TIME',
                                   control_time(),
                                   transitions={'succeeded': 'READ_TRACKER_TOPIC',
                                                'lif_time': 'SAY_LIFTIME'})

#TODO:: aborted->CONTROL_TIME
            smach.StateMachine.add('READ_TRACKER_TOPIC',
                                   topic_reader(topic_name='/pipol_tracker_node/peopleSet',
                                                topic_type=personArray,topic_time_out=60),
                                   transitions={'succeeded':'SELECT_ID',
                                                'aborted':'READ_TRACKER_TOPIC',
                                                'preempted':'preempted'},
                                   remapping={'topic_output_msg': 'tracking_msg'})
           
            
           
            # it learns the person that we have to follow
            smach.StateMachine.add('SELECT_ID',
                                   select_ID(self.learn_face, self.follow_pub),
                                   transitions={'succeeded': 'STOP_LEARNING',
                                                'aborted': 'CONTROL_TIME','learn_face':'FACE_SAY'})
            
            smach.StateMachine.add('FACE_SAY',
                                   text_to_say(SAY_LEARN),
                                   transitions={'succeeded': 'LEARN_FACE','aborted':'LEARN_FACE'})
                        # it learns the person that we have to follow
            smach.StateMachine.add('LEARN_FACE',
                                   new_database_and_learn(learning_time=2, minConfidence=80, 
                                                          name_face="following", name_database="follow"),
                                   transitions={'succeeded': 'STOP_LEARNING',
                                                'aborted': 'CONTROL_TIME'})
            

            smach.StateMachine.add('STOP_LEARNING',
                                   text_to_say(SAY_FINISH),
                                   transitions={'succeeded': 'succeeded','aborted':'STOP_LEARNING'})
