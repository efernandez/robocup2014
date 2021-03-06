import stparser as par
import readFiles
# import exceptionsjy as ex
from newUnderstanding import parseSentence
# a = par.StanfordParser(8)
# sentences = "bring a cold coke to john/NN and exit"

class dependency():
    def __init__(self):
        self.relation = ''
        self.mainVal = ''
        self.mainDepth = ''
        self.compVal = ''
        self.compDepth = ''

    def set_dependency(self, relation, mainval, maindepth, compval, compdepth):
        self.relation = relation
        self.mainVal = mainval.lower()
        self.mainDepth = maindepth
        self.compVal = compval.lower()
        self.compDepth = compdepth
        return self


class dependencies(list):
    def __init__(self):
        self = []

    def add_dependency(self, dep):
        self.append(dep)


class complement():
    def __init__(self):
        self.relation = ''
        self.value = ''

    def extract_complement(self, dep):
        self.relation = dep.relation
        self.value = dep.compVal
        return self


class verb():
    def __init__(self):
        self.verb = ' '
        self.complements = []

    def set_verb(self, v):
        self.verb = v
        return self

    def add_complement(self, dep):
        comp = complement()
        self.complements.append(comp.extract_complement(dep))



class verbList(dict):
    def __init__(self):
        self = {}

    def add_newverb(self, newverb):
        v = verb()
        self[newverb] = v.set_verb(newverb)

    def add_verb(self, newverb):
        self[newverb.verb] = newverb

    def add_complement(self, verb, dep):
        self[verb].add_complement(dep)


class orders():
    def __init__(self):
        self.action = ''
        self.item = ''
        self.person = ''
        self.location = ''
        self.others = []

    def kind_of_object(self, x):
        dictionary = {
            'dobj': ['item'],
            'prep_to': ['to', 'person'],
            'iobj': ['person'],
            'prep_from': ['from', 'location'],
            'prep_at': ['at', 'location']
            }
        try:
            return dictionary[x]
        except:
            return 'ignore'

    def define_order(self, action1, item1, person1, location1):
        self.action = action1
        self.item = item1
        self.location = location1
        self.person = person1
        return self

    def set_order(self, v, acts):
        # print v
        # print 'verb'
        # print v.verb
        # print 'compl'
        # print v.complements
        self.action = v.verb.lower()
        # print v.complements
        for com in v.complements:
            # print 'complements'
            # print len(v.complements)
            # print com.relation
            # print com.value
            kind = self.kind_of_object(com.relation)
            
            if kind[0] == 'ignore':
                print 'ignored'
            else:
                if kind[0] == 'item':
                    self.item = com.value
                    # print 'herehere'
                    # print self.item
                elif kind[0] == 'person':
                    self.person = com.value
                else:
                    try:
                        if kind[1] == 'location':
                            try:
                                self.location = com.value.split('_')[0]
                            except:
                                self.location = com.value
                        elif kind[1] == 'person':
                            try:
                                self.person = com.value.split('_')[0]
                            except:
                                self.person = com.value
                        else:
                            self.others.append(com.value)
                        self.action = self.action + '_' + kind[0]
                        self.action = acts[self.action]
                    except:
                        self.others.append(com.value)

        # self.clean_words()
    #     print 'blabla'
    #     print self.action
    #     print self.person

    # def clean_words(self):
    #     # print 'cleaning'
    #     # print self.action
    #     self.action = ex.clean_word(self.action)
    #     # print self.action
    #     self.item = ex.clean_word(self.action)
    #     self.location = ex.clean_word(self.location)
    #     self.person = ex.clean_word(self.person)
    


class orderList():
    def __init__(self):
        self.actionSet = []
        self.confidence = 'True'
        self.tree = ''
        self.depends = ''

    def new_order(self, a, i, p, l):
        o = orders()
        self.actionSet.append(o.define_order(action1=a,item1=i,person1=p,location1=l))
        return self
    def extract_dependencies(self, deps):
        # Extract de relations in a structure
        o_deps = dependencies()
        for dep in deps:
            n1 = dep.find('(')
            n2 = dep.find(', ')
            n3 = dep.find(')')
            relation = dep[:n1]
            main = dep[n1 + 1:n2].split('-')
            comp = dep[n2 + 2:n3].split('-')
            o_dep = dependency()
            o_deps.add_dependency(o_dep.set_dependency(
                relation.strip(' '),
                main[0].strip(' '),
                main[1].strip(' '),
                comp[0].strip(' '),
                comp[1].strip(' ')))

        return o_deps

    def parseOrders(self, sentence):

        #read the list of possible actions
        # acts = readFiles.functionList()
        # acts.importFiles()

        # sentence = "bring the coke to John_NN and leave the apartment"

        acts = readFiles.inv_functionList()  #Load VerbCategories.txt
        # c = a.batch_parse(sentence)

        # # c = a.batch_parse(sentence.lower())
        # d = c.strip().split("\n")
        # # d.index('')

        # # Extract parse tree data from Parser
        # tree = d[:d.index('')]
        # tree = '\n'.join(tree)

        # # Extract dependencies data from Parse
        # depends = d[d.index('') + 1:]
        # deps = self.extract_dependencies(depends)

        # s = tokenize_sentence(sentence)
        # n = change_exceptions(s, deps)
        commands = parseSentence(sentence)
        print("----------------comands---------------")
        print commands
        print("----------------fi comands---------------")
        if commands == 'unk':       #if parserSentence couldnt return a thing return self fith confidence = 0 and finish
            self.confidence = '0'
            return self
        
        # not implemented: must be set the list of word topics to find and in which grammar
        # wordlist = grammarFileReader(wordset,path)
        # grammarFileWriter(wordlist)
        pervious_person = ''
        person = ''
        for c in commands:
            o = orders()
            action = ''
            item = ''
            pervious_person = person
            person = ''
            location = ''
            for prod in c.productions():
                s = str(prod.lhs())
                if s == 'VB':
                    action = str(prod.rhs()).strip('(').strip(')').strip(',').strip("'")
                elif s == 'ITEM':
                    item = '_'.join(prod.rhs())
                elif s == 'PERSON':
                    person = str(prod.rhs()).strip('(').strip(')').strip(',').strip("'")     
                elif s == 'LOCATION':
                    location = '_'.join(prod.rhs())
                elif s == 'PRON':
                    r = str(prod.rhs()).strip('(').strip(')').strip(',').strip("'")
                    if r == 'it':
                        item = self.actionSet[len(self.actionSet)-1].item
                    elif r == 'me' or r == 'my':
                        person = 'referee'
                    elif r == 'him':
                        person = pervious_person
                elif s == 'FROM': # could be cleaned
                    if action == 'bring':
                        action = 'bring_from'
                        person = 'referee'
            if action == 'find':
                if person == '':
                    action == 'find_object'
                else:
                    action == 'find_person'
            if action == 'exit' or action == 'leave':
                action = 'go_to'
                location = 'exit'
            
            try:
                action=acts[action]
            except:
                action=action
                
            if action == 'bring' or action == 'bring_from':
                if person == '':
                    person = 'referee'
            print action + person
            try:
                o.define_order(action1=acts[action], item1=item, person1=person, location1=location)
            except KeyError:
                o.define_order(action1=action, item1=item, person1=person, location1=location)
            
            
            self.actionSet.append(o)

        # # Prepare tree to extract verbs (or any other data)
        # t = tree.strip().split(' ')
        # n = True
        # while n:
        #     try:
        #         t.remove('')
        #     except:
        #         n = False

        # tt = []
        # for part in t:
        #     try:
        #         part = part.replace("\n", "")
        #     except:
        #         True
        #     tt.append(part)

        # # Find the verbs (predicates) in the sentence
        # VerbList = []
        # verbs = True
        # ttt = " ".join(tt)

        # while verbs:
        #     try:
        #         verbPos = ttt.find('(VB')
        #         1 / (verbPos + 1)
        #         # print 'aqui'
        #         # print ttt[verbPos + 4:verbPos + ttt[verbPos:].find(')')]
        #         VerbList.append(ttt[verbPos + 4:verbPos + ttt[verbPos:].find(')')])
        #         ttt = ttt[verbPos + 3:]
        #     except:
        #         verbs = False

        # # Ignore determinants, conjunctions and clausal complements
        # rmList = ['det', 'ccomp', 'conj_and', 'root']
        # # print len(deps)
        # for dep in deps:
        #     if dep.relation in rmList:
        #         # print dep.relation
        #         deps.remove(dep)

        # # Add verb complements from dependencies list
        # verbs = verbList()
        # for v in VerbList:
        #     # print v
        #     v = v.strip(' ').lower()
        #     verbs.add_newverb(v)
        #     for dep in deps:
        #         if dep.mainVal == v:
        #             verbs.add_complement(v, dep)
        # # print len(verbs)

        # # Assigns each verb to an order
        # # for v in verbs:
        # #     print v
        # #     try:
        # #         print v.verb
        # #     except:
        # #         print 'no verb'

        # for v in verbs:
        #     o = orders()
        #     o.set_order(verbs[v], acts)
        #     self.actionSet.append(o)

        i = 1
        for order in self.actionSet:
            print 'order #' + str(i) + ' of ' + str(len(self.actionSet))
            print 'action:'
            print order.action
            print 'item:'
            print order.item
            print 'location:'
            print order.location
            print 'person:'
            print order.person
            i += 1

        # O1 = orders()
        # O1.action = 'bring_to'
        # O1.item = 'coke'
        # O1.person = 'John'
        # O2 = orders()
        # O2.action = 'exit'

        # self.actionSet=[]
        # self.actionSet.append(O1)
        # self.actionSet.append(O2)

        return self
