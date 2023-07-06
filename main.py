from tkinter import *
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from enum import Enum



class ShGame:
    class ShQuestion:

        def __init__(self, ref_game, new_text):
            self.Text = new_text
            self.Groups= []
            self._Game = ref_game


        @property
        def GameIndex(self):
            return self._Game.Questions.index(self)

        @property
        def Game(self):
            return self._Game

        def StartNewGroup(self, new_text):
            newGrp = ShGroup(self, new_text)
            self.Groups.append(newGrp)
            return newGrp

        def SyncGroups(self):
            self.Groups = [shg for shg in self.Groups if shg.Answers]

        def GetAllAnswers(self):
            all_answers = []
            for grp in self.Groups:
                all_answers.extend(grp.Answers)
            return all_answers

            # returns list of scores for this question
            # SCORING METHODS
            # Sheep:    each player gets total answers in his group as his score
            # Peehs1:   incorrects = 1.5 * highest correct score
            # Peehs2:   incorrects = highest correct score + 0.5 * number of distinct
            #          correct answers
            # Heep:     highest score gets 0, 2nd highest get doubled
            # Kangaroo: must be incorrect; correct answers get 0

        def Scores(include_bonus):
            curScore = {}
            for plr in _Game.Players:
                curScore[plr] = 0
            if len(_Game.Players) == 0 or len(_Game.Questions) == 0:
                return curScore
            highest_score = 0
            second_highest_score = 0
            num_distinct_correct = 0
            for grp in self.Groups:
                for ans in grp.Answers:
                    if ans.Player not in curScore:
                        continue
                    curScore[ans.Player] = len(grp.Answers)
                return curScore
                # for peehs/heep
                if grp.Correct:
                    num_distinct_correct += 1
                    if len(grp.Answers) > highest_score:
                        second_highest_score = highest_score
                        highest_score = len(grp.Answers)
                    elif len(grp.Answers) > second_highest_score and len(grp.Answers) < highest_score:
                        second_highest_score = len(grp.Answers)

            # apply special scores depending on scoring method
            for grp in self.Groups:
                for ans in grp.Answers:
                    if ans.Player not in curScore:
                        continue
                    if self._Game.Method == ShMethod.Sheep:
                        if not grp.Correct:
                            curScore[ans.Player] = 0
                        # incorrect means invalid for sheep
                    elif self._Game.Method == ShMethod.PeehsDM:
                        # incorrect -> 1.5*sheep
                        if not grp.Correct:
                            curScore[ans.Player] = 1.5 * highest_score
                    elif self._Game.Method == ShMethod.PeehsFB:
                        # incorrect -> sheep + 0.5*distinct
                        if not grp.Correct:
                            curScore[ans.Player] = highest_score + 0.5 * num_distinct_correct
                    elif self._Game.Method == ShMethod.PeehsHybrid:
                        # incorrect -> sheep + 0.5*distinct
                        if not grp.Correct:
                            curScore[ans.Player] = 1.25 * highest_score + 0.25 * num_distinct_correct
                    elif _Game.Method == ShMethod.Heep or _Game.Method == ShMethod.Heep15 or _Game.Method == ShMethod.Heep2:
                        if curScore[ans.Player] == highest_score or not grp.Correct:
                            curScore[ans.Player] = 0
                        elif curScore[ans.Player] == second_highest_score:
                            if _Game.Method == ShMethod.Heep15:
                                curScore[ans.Player] *= 1.5
                            elif _Game.Method == ShMethod.Heep2:
                                curScore[ans.Player] *= 2
                    elif _Game.Method == ShMethod.Kangaroo:
                        if grp.Correct:
                            curScore[ans.Player] = 0
                    elif _Game.Method == ShMethod.Manual:
                        curScore[ans.Player] = 0
                    # apply rounding
                    if _Game.Rounding == ShRoundingType.Up:
                        curScore[ans.Player] = math.ceil(curScore[ans.Player])
                    elif _Game.Rounding == ShRoundingType.Down:
                        curScore[ans.Player] = math.floor(curScore[ans.Player])
                    elif _Game.Rounding == ShRoundingType.Nearest:
                        curScore[ans.Player] = round(curScore[ans.Player])

                    # apply player & group bonuses
                    if include_bonus:
                        temp_score = cur_score[ans.Player]
                        if grp.BonusType == ShBonusType.Override:
                            temp_score = grp.GroupBonus
                        elif grp.BonusType == ShBonusType.Add:
                            temp_score += grp.GroupBonus
                        if ans.BonusType == ShBonusType.Override:
                            temp_score = ans.AnswerBonus
                        elif ans.BonusType == ShBonusType.Add:
                            temp_score += ans.AnswerBonus
                        cur_score[ans.Player] = temp_score

                    def score_up_to(include_bonus):
                        cur_score = {}
                        next_score = {}
                        for plr in _Game.Players:
                            cur_score[plr] = 0
                        for que in _Game.Questions:
                            if que.GameIndex <= self.GameIndex:
                                next_score = que.scores(include_bonus)
                                for k, v in next_score.items():
                                    if k in cur_score:
                                        cur_score[k] += v
            return cur_score
    class ShPlayer:
        counter = 0
        def __init__(self, ref_game, player_name, start_score=0):
            self._Game = ref_game
            self.Name = player_name
            self.Answers = []
            self.StartScore = start_score
            ShGame.ShPlayer.counter += 1
    class ShGroup:
        def __init__(self, ref_question, new_text):
            self.Text = new_text
            self.Correct = True
            self.GroupBonus = 0
            self.BonusType = NONE
            self.Answers = []  # actual answers
            self._Question = ref_question  # reference to question
            # constructor
            # declares with an empty list for Answers
            #self.Answers = [ShAnswer() for _ in range(len(ref_question.Game.Players))]
            #self.Answers = [ShGame.ShAnswer(len(ref_question.Game.Players)) for _ in range(len(ref_question.Game.Players))]

        @property
        def Question(self):
            return self._Question

        # moves all answers to ref_group and deletes itself
        def MergeToGroup(self, ref_group):
            if ref_group == self:
                # throw new Exception("Trying to merge a group to itself")
                return
            while len(self.Answers) != 0:
                self.Answers[0].ChangeGroup(ref_group)
            self._Question.Groups.remove(self)
        def GetScore(self, include_bonus):
            if len(self.Answers) == 0:
                return 0
            else:
                try:
                    baseScore = _Question.Scores(False)[self.Answers[0].Player]
                    if include_bonus:
                        if self.BonusType == ShBonusType.Override:
                            return self.GroupBonus
                        elif self.BonusType == ShBonusType.Add:
                            return self.GroupBonus + baseScore
                        else:
                            return baseScore
                    else:
                        return baseScore
                except:
                    return 0

        def __del__(self):
            for ans in self.Answers:
                ans.Player.Answers.remove(ans)
    class ShAnswer:
        def __init__(self, ref_group, ref_player, new_text):
            self.Text = new_text
            self.AnswerBonus = 0
            self._Group = ref_group
            self._Player = ref_player

        @property
        def Group(self):
            return self._Group

        @property
        def Player(self):
            return self._Player

        def ChangeGroup(self, ref_group):
            if ref_group == self._Group:
                return
            if self._Group.Question != ref_group.Question:
                raise Exception("Moving an answer to a group in a different question.")
            oldGroup = self._Group
            self._Group = ref_group
            ref_group.Answers.append(self)
            oldGroup.Answers.remove(self)
            if len(oldGroup.Answers) == 0:
                oldGroup.Question.Groups.remove(oldGroup)
        def StartNewGroup(self):
            oldGroup = self._Group
            newGroup = ShGroup(_Group.Question, self.Text)
            oldGroup.Question.Groups.append(newGroup)
            self._Group = newGroup
            newGroup.Answers.append(self)
            oldGroup.Answers.remove(self)
            if len(oldGroup.Answers) == 0:
                oldGroup.Question.Groups.remove(oldGroup)

    class ShMethod(Enum):
        Sheep = 1
        PeehsDM = 2
        PeehsFB = 3
        PeehsHybrid = 4
        Heep = 5
        Heep15 = 6
        Heep2 = 7
        Kangaroo = 8
        Manual = 9
    class ShBonusType(Enum):
        NONE = 0
        Add = 1
        Override = 2
    class ShRoundingType(Enum):
        NONE = 0
        Up = 1
        Down = 2
        Nearest = 3



        @property
        def Count(self):
            return self.counter

        @property
        def GameIndex(self):
            return self._Game.Players.index(self)

        @property
        def Game(self):
            return self._Game

        def __del__(self):
            for ans in self.Answers:
                self.counter -= 1
                ans.Group.Answers.remove(ans)


    def __init__(self,*args):
        if len(args)==0:
            self.Questions = []
            self.Players = []
            self.Method = self.ShMethod.Sheep
            self.Rounding = self.ShRoundingType.NONE
        elif len(args)==3:
            new_questions=args[0]
            new_players=args[1]
            new_answers=args[2]
            if len(new_answers) != len(new_questions) or len(new_answers[0]) != len(new_players):
                raise Exception("Answer list must be size [num questions, num players]")

            self.Questions = [ShQuestion(self, txt) for txt in new_questions]
            self.Players = [ShPlayer(self, txt) for txt in new_players]

            for iques in range(len(new_questions)):
                for iplayer in range(len(new_players)):
                    new_group = ShGroup(self.Questions[iques], new_answers[iques][iplayer])
                    self.Questions[iques].Groups.append(new_group)

                    new_answer = ShAnswer(new_group, self.Players[iplayer], new_answers[iques][iplayer])
                    new_group.Answers.append(new_answer)
                    self.Players[iplayer].Answers.append(new_answer)
    def __str__():
        return 'This is a Game'



    def loadReveal(self):
        #print (sg.__dict__)
        global myLabel2, Roundtype
        # filename = "C:/Users/keith/Desktop/sheep/80s2023.sheep17"
        filename = filedialog.askopenfilename(title="Load Sheep Scoring File", filetypes=[("Sheep Score 2017 File", "*.sheep17")])
        tree = ET.parse(filename)
        root = tree.getroot()
        #print(root.tag)
        if root.tag == "SheepScore2012Game":
            for child in root:
                if child.tag == "ScoringMethod":
                    self.Method = self.ShMethod[child.text]
                    #Gametype.set(gt[child.text])
                elif child.tag == "Rounding":
                    if child.text =="None":
                        child.text = "NONE"
                    self.Rounding = self.ShRoundingType[child.text]
                    #Roundtype.set(rt[child.text])
                elif child.tag == "Question":
                    #print(child.attrib['GameIndex'], child.text)
                    qindex = int(child.attrib['GameIndex'])
                    while len(self.Questions) < qindex + 1:
                        self.Questions.append(self.ShQuestion(self, "(blank)"))
                    self.Questions[qindex].Text = child.text
                elif child.tag == "Player":
                    pindex = int(child.attrib['GameIndex'])
                    start_score = child.attrib['StartScore']
                    while len(self.Players) < pindex + 1:
                        self.Players.append(self.ShPlayer(self, "(blank)", start_score))
                    self.Players[pindex].Name = child.text
                elif child.tag == "Group":
                    group_q_index = int(child.attrib['QuestionIndex'])
                    tempcorrect = child.attrib['Correct']
                    tempgroupbonus = child.attrib['GroupBonus']
                    tempgroupbonustype = child.attrib['BonusType']
                    newGroup = self.ShGroup(self.Questions[group_q_index], "")
                    newGroup.Correct = tempcorrect
                    newGroup.GroupBonus = tempgroupbonus
                    newGroup.BonusType = tempgroupbonustype
                    self.Questions[group_q_index].Groups.append(newGroup)
                    #print(child.tag, child.text)
                    for item in child:
                        if item.tag == "Text":
                            newGroup.Text = item.text
                        elif item.tag == "Answer":

                            ans_p_index = int(item.attrib['PlayerIndex'])
                            tempansbonus = int(item.attrib["AnswerBonus"])
                            tempansbonustype = item.attrib['BonusType']
                            anstext = item.text
                            newAns = ShGame.ShAnswer(newGroup, self.Players[ans_p_index], anstext)
                            newGroup.Answers.append(newAns)
                            self.Players[ans_p_index].Answers.append(newAns)


            if len(self.Questions) >= curQ:
                myLabel2.grid_forget()
                myLabel2 = Label(window, text=self.Questions[curQ - 1].Text)
                myLabel2.grid(row=0, column=4)
            else:
                qdown()
        else:
            messagebox.showinfo(title="Greetings", message="This is not a recognized sheep file!")

def qdown():
    global curQ
    global myLabel2
    if curQ>len(sg.Questions): curQ =  len(sg.Questions)

    if curQ>1:
        curQ=curQ-1
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    if curQ == 0: return
    if len(sg.Questions) >= curQ:
        myLabel2.grid_forget()
        myLabel2 = Label(window, text=sg.Questions[curQ-1].Text)
        myLabel2.grid(row=0, column=4)
def qup():
    global curQ
    global myLabel2
    if curQ > len(sg.Questions): curQ = len(sg.Questions)
    if curQ < len(sg.Questions):
        curQ = curQ + 1
    else:
        curQ == 1
    myTextbox1.delete(0,END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    if curQ == 0: return
    if len(sg.Questions) >= curQ:
        myLabel2.grid_forget()
        myLabel2 = Label(window, text=sg.Questions[curQ-1].Text)
        myLabel2.grid(row=0, column=4)
def resetProgram():
    global myTextbox1, myLabel2,  myAnswers, players, curQ, current_var
    sg.Questions = []
    sg.Players = []
    players=[]
    curQ = 1
    current_var.set("")
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    myLabel2.grid_forget()
    myLabel2 = Label(window, text="Click Sheep > Edit Questions... to begin.")
    myLabel2.grid(row=0, column=4)
    return

def edQL(edQText):
    edQL.filename = filedialog.askopenfilename(title="Load Questions from File", filetypes=[("txt files", "*.txt")]  )
    #print(edQL.filename) #debug code
    file1 = open(edQL.filename, 'r')
    strvar=file1.read()
    edQText.delete(1.0,END)
    edQText.insert(INSERT, strvar)
    return(edQText)

def edSave(edQW,edQText):
    global myLabel2
    global curQ
    sg.Questions = []
    questions = edQText.get("1.0",END).splitlines()
    qindex=0
    for item in questions:
        sg.Questions.append(ShGame.ShQuestion(qindex,questions[qindex]))
        qindex+=1

    window.deiconify()
    if curQ==0:curQ=1
    if curQ>len(sg.Questions): curQ=len(sg.Questions)
    myTextbox1.delete(0, END)
    myTextbox1.insert(INSERT, curQ)
    myTextbox1.grid_forget()
    myTextbox1.grid(row=0, column=2)
    if len(sg.Questions) >= curQ:
        myLabel2.grid_forget()
        myLabel2 = Label(window, text=sg.Questions[curQ - 1].Text)
        myLabel2.grid(row=0, column=4)
    edQW.destroy()
def edPSave(edAW,edAText):
    global players, score, myPlayers
    sg.Players=[]
    x=0
    for item in players:
        sg.Players.append(item)
        x=x+1
    window.deiconify()
    edAW.destroy()

def edPCancel(parent,child):
    parent.deiconify()
    child.destroy()

def edCancel(child):
    window.deiconify()
    child.destroy()

def edPOK(edAText,combo, edAW, newPW, newplayer, x=''):
    global players, score, curP
    players.append(ShGame.ShPlayer(sg,newplayer,0))
    combo['values'] = [item.Name for item in players]
    curP+=1
    combo.current(curP)
    PAnswers = []
    answers = ""
    for x in players[curP].Answers: PAnswers.append(x.Text)
    for item in PAnswers: answers = answers + item + "\n"
    edAText.delete(1.0, END)
    edAText.insert(INSERT, answers)
    edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
    edAW.deiconify()
    newPW.destroy()

def newPlayer(edAText,combo, edAW):
    edAW.withdraw()
    newPW = Toplevel(edAW)
    newPW.bind('<Return>', lambda x: edPOK(edAText,combo, edAW, newPW, newPEntry.get()))
    newPW.title("New Player")
    newPLabel = Label(newPW, text="Enter new player name:", padx=10, font=20).grid(row=0, column=0)
    newPEntry = Entry(newPW, font=20)
    newPEntry.grid(row=1, column=0)
    newPOK = Button(newPW, text='OK', command=lambda: edPOK(edAText,combo, edAW, newPW, newPEntry.get())).grid(row=2,
                                                                                                       column=3)
    newPCancel = Button(newPW, text='Cancel', command=lambda: edPCancel(edAW, newPW)).grid(row=2, column=4)
def TextBoxUpdate(edAText,combo):
    global curP, current_var, players
    #print("old player was : "+players[curP].Name)
    #Do save answers here.
    current_value = current_var.get()
    index=0
    for item in players:
        if item.Name==current_value:
            curP=index
        else: index+=1
    #Get answers for new slot
    if len(players) != 0:
        combo.current(curP)
        PAnswers=[]
        answers = ""
        for x in players[curP].Answers: PAnswers.append(x.Text)
        for item in PAnswers: answers=answers+item+"\n"
        edAText.delete(1.0, END)
        edAText.insert(INSERT, answers)
        edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)

def edAnswers(window):
    global players, curP, current_var
    players = []

    for item in sg.Players:
        players.append(item)
    curP = len(players)-1
    #print([item.Name for item in players])
    window.withdraw()
    #myfile = "\n".join(item.Name.lsplit() for item in sg.Answers)
    edAW = Toplevel(window)
    edAW.bind("<<ComboboxSelected>>", lambda x: TextBoxUpdate(edAText,combo))

    edAW.title("Edit Entries")
    edALabel = Label(edAW, text="Player:")
    edALabel.grid(row=0, column=0)
    combo = ttk.Combobox(edAW,textvariable=current_var, state="readonly", values=[item.Name for item in players])
    if len(players) != 0:
        combo.current(curP)
        PAnswers=[]
        answers = ""
        for x in players[curP].Answers: PAnswers.append(x.Text)
        for item in PAnswers: answers=answers+item+"\n"

    combo.grid(row=0, column=1)
    spacer = Label(edAW).grid(row=0, column=2)
    edALabel = Label(edAW, text="Starting Score:", padx=10)
    edALabel.grid(row=1, column=0)

    edAText = Text(edAW)
    if len(players)==0:
        edAText.insert(INSERT,
                       'Click Load... to load players and answers\nfrom a PM text file, or click New Player\nto add players manually.')
    else:
        edAText.insert(INSERT,answers)
    edAText.grid(column=0, columnspan=3, rowspan=10, padx=5, pady=5)
    edALoad = Button(edAW, text="Load", padx=20, command=lambda: edQL(edAText)).grid(row=0, column=3, padx=10,
                                                                                     pady=5)
    edANP = Button(edAW, text="New Player", padx=4, command=lambda: newPlayer(edAText,combo, edAW)).grid(row=1,
                                                                                                 column=3,
                                                                                                 padx=10,
                                                                                                 pady=5)
    edACN = Button(edAW, text="Change Name", padx=0).grid(row=2, column=3, padx=10, pady=5)
    edADP = Button(edAW, text="Delete Player", padx=0).grid(row=3, column=3, padx=10, pady=5)
    edASave = Button(edAW, text="Save Changes", command=lambda: edPSave(edAW, edAText)).grid(row=9, column=3,
                                                                                             padx=10, pady=5)
    edACancel = Button(edAW, text="Cancel", padx=20, command=lambda: edCancel(edAW)).grid(row=10, column=3,
                                                                                          padx=10, pady=5)
    edAW.rowconfigure(4, weight=1)
    edAW.columnconfigure(2, weight=1)
    return

def edQuestions(window):
    window.withdraw()
    myfile = "\n".join(item.Text.lstrip() for item in sg.Questions)
    print(myfile)
    edQW = Toplevel(window)
    edQW.title("Edit Questions")
    edQLabel = Label(edQW,
                     text="Click Load... to load the questions from a text file, or just type them in here one per line")
    edQLabel.grid(row=0, columnspan=2)
    edQText = Text(edQW)
    edQText.insert(INSERT, myfile)
    edQText.grid(column=0, rowspan=10, padx=5, pady=5)
    edQLoad = Button(edQW, text="Load", padx=20, command=lambda: edQL(edQText)).grid(row=1, column=1)
    edQSave = Button(edQW, text="Save Changes", command=lambda: edSave(edQW, edQText)).grid(row=9, column=1)
    edQCancel = Button(edQW, text="Cancel", padx=20, command=lambda: edCancel(edQW)).grid(row=10, column=1)
    return

def validate_entry(text):
    return text.isdecimal()

def outPlayerscore():
    print("[", end="")
    for i in myPlayers:
        if i != myPlayers[-1]:
            print(i.score, end=",")
        else:
            print(i.score, end="")
    print("]")
def dothis():
    print(sg.__dict__)
    print(sg.Questions[0].__dict__)

    # for x in sg.Players[0].Answers:
    #     print(x.Text)

gt= {'Sheep':1,'PeehsDM':2, 'PeehsFB':3, 'PeehsHybrid':4, 'Heep':5, 'Heep15':6, 'Heep2':7, 'Kangaroo':8, 'Manual':9}
gtl=['filler','Sheep','PeehsDM','PeehsFB','PeehsHybrid','Heep','Heep15','Heep2','Kangaroo','Manual']

rt= {'None':0,'Up':1,'Down':2,'Nearest':3}
rtl=['None','Up','Down','Nearest']

bt= {'None':1, 'Add':2, 'Override':3}
btl=['filler','None', 'Add', 'Override']

sg = ShGame()
players=[]
score=[]
curQ=1
curP=1

window = Tk()

window.geometry("680x450")
window.title("Sheep Score Foggies Edition")
Outputtype = IntVar()
Outputtype.set(1)
Gametype = IntVar()
Gametype.set(1)
Roundtype = IntVar()
Roundtype.set(0)
current_var = StringVar()
menubar = Menu(window)

window.config(menu=menubar)

fileMenu=Menu(menubar,tearoff=0)
menubar.add_cascade(label="File",menu=fileMenu)




fileMenu.add_command(label="New Reveal", command=resetProgram)
fileMenu.add_command(label="Load Reveal...", command=sg.loadReveal)
fileMenu.add_command(label="Save Reveal...")
fileMenu.add_command(label="Debug", command=dothis)
fileMenu.add_separator()
fileMenu.add_command(label="Exit",command=quit)

sheepMenu = Menu(menubar,tearoff=0)
menubar.add_cascade(label="Sheep",menu=sheepMenu)
sheepMenu.add_command(label="Edit Questions...", command=lambda:edQuestions(window))
sheepMenu.add_command(label="Edit Entries...", command=lambda:edAnswers(window))

scoringMenu=Menu(menubar,tearoff=0)
sheepMenu.add_cascade(label="Scoring",menu=scoringMenu)
scoringMenu.add_radiobutton(label="Sheep",value=1, variable=Gametype)
peehsMenu=Menu(menubar,tearoff=0)
scoringMenu.add_cascade(label="Peehs",menu=peehsMenu)
peehsMenu.add_radiobutton(label="DM Scoring",value=2, variable=Gametype)
peehsMenu.add_radiobutton(label="FB Scoring",value=3, variable=Gametype)
peehsMenu.add_radiobutton(label="Hybrid",value=4, variable=Gametype)
heepsMenu=Menu(menubar,tearoff=0)
scoringMenu.add_cascade(label="Heeps",menu=heepsMenu)
heepsMenu.add_radiobutton(label="2x Heep Bonus",value=7, variable=Gametype)
heepsMenu.add_radiobutton(label="1.5x Heep Bonus",value=6, variable=Gametype)
heepsMenu.add_radiobutton(label="No Heep Bonus",value=5, variable=Gametype)
scoringMenu.add_radiobutton(label="Kangaroo",value=8, variable=Gametype)
scoringMenu.add_radiobutton(label="Manual",value=9, variable=Gametype)
scoringMenu.add_separator()

roundingMenu=Menu(menubar,tearoff=0)
scoringMenu.add_cascade(label="Rounding",menu=roundingMenu)
roundingMenu.add_radiobutton(label="No Rounding",value=0, variable=Roundtype)
roundingMenu.add_radiobutton(label="Round Up",value=1, variable=Roundtype)
roundingMenu.add_radiobutton(label="Round Down",value=2, variable=Roundtype)
roundingMenu.add_radiobutton(label="Round Nearest",value=3, variable=Roundtype)

outputMenu=Menu(menubar,tearoff=0)
menubar.add_cascade(label="Output",menu=outputMenu)
outputMenu.add_command(label="Copy answers for this question")
outputMenu.add_command(label="Copy total scores up to this question")
outputMenu.add_command(label="Copy score table up to this question")
outputMenu.add_command(label="Copy Player list")
outputMenu.add_separator()
styleMenu=Menu(menubar,tearoff=0)
outputMenu.add_cascade(label="Output Style",menu=styleMenu)
styleMenu.add_radiobutton(label="Forum Table",value=1, variable=Outputtype)
styleMenu.add_radiobutton(label="Forum Formatted Text",value=2, variable=Outputtype)
styleMenu.add_radiobutton(label="Unformatted Text",value=3, variable=Outputtype)




qButton1 = Button(window, text="<",command=qdown).grid(row=0,column=1)
qButton2 = Button(window, text=">",command=qup).grid(row=0,column=3)
myLabel1 = Label(window, text="Q #", padx=5).grid(row=0,column=0)
myLabel2 = Label(window, text="Click Sheep > Edit Questions... to begin.")
myLabel2.grid(row=0,column=4)




myTextbox1 = Entry(window,width=4 ,validate="key",
    validatecommand=(window.register(validate_entry), "%S"))

myTextbox1.insert(INSERT,curQ)
myTextbox1.grid(row=0,column=2)


myTextbox2 = Text(window,state=DISABLED,padx=10,pady=5)
myTextbox2.grid(row=1,column=0,columnspan=5)
window.columnconfigure(4, weight=1)




window.mainloop()


