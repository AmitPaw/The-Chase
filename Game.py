import random
import json
import urllib
import requests
import urllib.request

QUESTION_COUNT = 50
CATEGORY = 17
ANSWER_COUNT = 4
SCORE_PER_QUESTION = 5000
LAST_STEP = 7
ENTER_INPUT_STR = "Enter a number from 1-"
INITIAL_QUESTION_COUNT = 3
SEPARATOR = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
HELP_WHEEL_KEY = 0
END_GAME = "!ENDGAME"

# Downloads or opens local JSON file which contains all the questions and answers
def getQuestionJson():
    # Uncomment the next line to download from questions database
    # questions = urllib.request.urlretrieve(f'https://opentdb.com/api.php?amount=20&category=20&difficulty=medium&type=multiple','Questions.json')
    questions = urllib.request.urlretrieve(f'https://opentdb.com/api.php?amount={QUESTION_COUNT}&category={CATEGORY}&difficulty=medium&type=multiple','Questions.json')

    with open("Questions.json") as QuestionsFile:
        QuestionsObject = json.load(QuestionsFile)
        QuestionsFile.close()

    return QuestionsObject

class Game:
    def __init__(self, sendCb, recCb):
        self.chaserPos = 0          # initial position of the chaser
        self.playerPos = 3          # initial position of the player
        self.helpWheel = 1          # amount of help wheels
        self.playerScore = 0        # initial player score
        self.questionLog = []       # log of the questions asked to avoid duplicates
        self.sendCb = sendCb        # send message call back method
        self.recCb = recCb          # receive message call back method
        self.stage = 0              # tracks the stage of the game that the client is at

    # uses call back method to send the game text to the client
    def sendToClient(self, msg='\n'):
        self.sendCb(msg)

    # get and validate user input
    def userInputAndValidation(self, till):
        self.sendToClient(f"{ENTER_INPUT_STR}{till}")
        while True:
            try:
                #userInput = int(input())
                userInput = int(self.recCb())
            except ValueError:
                self.sendToClient(f"NO LETTERS! {ENTER_INPUT_STR}{till}")
            else:
                #if (not self.helpWheel) <= userInput <= till:
                if userInput == 0 and till != 3 and self.stage:
                    self.helpWheelAction()
                if 1 <= userInput <= till:
                    break
                else:
                    self.sendToClient(f"{ENTER_INPUT_STR}{till}")
        return userInput

    # preform the help wheel action
    def helpWheelAction(self):
        if self.helpWheel == 1:
            questionNumber = self.questionLog[-1]
            wrongAns = questions['results'][questionNumber]['incorrect_answers']
            self.sendToClient(f'"{wrongAns[0]}" and "{wrongAns[1]}" are wrong answers!')
            self.helpWheel = 0
        else:
            self.sendToClient("No more help wheels for you")

    # ask question and return number of correct answer
    def askQuestion(self):
        # make sure no duplicate questions are asked
        while True:
            q = random.randint(0, QUESTION_COUNT - 1)
            try:
                self.questionLog.index(q)
            except ValueError:  # only if the number is not in the list, break, else keep randomizing
                break
        self.questionLog.append(q)

        # get question and ask it
        currQ = questions['results'][q]['question'].replace('&quot;', '"').replace('&#039;', '\'').replace('&lt;', '<').replace('&gt;', '>')
        self.sendToClient(currQ + '\n')
        correctAnsNum = random.randint(0, ANSWER_COUNT - 1)
        correctAns = questions['results'][q]['correct_answer'].replace('&quot;', '"').replace('&#039;', '@').replace('&lt;', '<').replace('&gt;', '>')
        wrongAns = questions['results'][q]['incorrect_answers']  # this is a list

        # randomize answers order
        for i in range(0, ANSWER_COUNT):
            if i == correctAnsNum:
                self.sendToClient(f'{i + 1}. {correctAns}')  # remove @@@
            else:
                wrongAns[i - 1] = wrongAns[i - 1].replace('&quot;', '"').replace('&#039;', '\'').replace('&lt;', '<').replace('&gt;', '>')
                self.sendToClient(f'{i + 1}. {wrongAns[i - 1]}')
        self.sendToClient()
        if self.stage:
            self.sendToClient(f"(Press 0 for help wheel - you have {self.helpWheel} wheels left)")
        return correctAnsNum

    # check correct answer and allocate points
    def checkAnswer(self, userInput, correctAnsNum):
        if userInput - 1 == correctAnsNum:
            self.sendToClient('Correct! :)')
            return True
        else:
            self.sendToClient('Wrong! :(')
            return False

    # ask, get input, and return correct or not all in one
    def Question(self):
        # ask question and return number of correct answer
        correctAnsNum = self.askQuestion()
        # get input
        userInput = self.userInputAndValidation(ANSWER_COUNT)
        # check correct answer and allocate points
        answer = self.checkAnswer(userInput, correctAnsNum)
        return answer

    # self.sendToClient updated board with player and chaser
    def printBoard(self):
        self.sendToClient("Current board: ")
        for i in range(LAST_STEP+1):
            if i == self.chaserPos:
                self.sendToClient(f"{i}\tChaser")
            elif i == self.playerPos:
                self.sendToClient(f"{i}\tYou\t{self.playerScore}")
            else:
                self.sendToClient(f"{i}")

    # randomize chaser actions and advance accordingly
    def randChaserMove(self):
        r = random.randint(0, 100)
        if r < 75:
            self.chaserPos += 1
            return True
        return False

    # send winning message
    def gameWinner(self):
        self.sendToClient(SEPARATOR)
        self.sendToClient(f"Congratulations! You beat the chaser and won the game with a score of: {self.playerScore}")
        self.sendToClient(SEPARATOR)

    # send loser message
    def gameLoser(self):
        self.sendToClient(SEPARATOR)
        self.sendToClient(f"Loser! The chaser caught you, you lost all your money and your dignity")
        self.sendToClient(SEPARATOR)

    # the initial {INITIAL_QUESTION_COUNT} questions before the board
    def initialRound(self):
        for rounds in range(INITIAL_QUESTION_COUNT):
            self.sendToClient(f'Question {rounds+1}/3:')
            answer = self.Question()
            if answer:
                self.playerScore += SCORE_PER_QUESTION
            self.sendToClient(f'Current score: {self.playerScore}\n')
            self.sendToClient(SEPARATOR)

    # ask question till player wins or loses
    def actualGame(self):
        self.stage = 1
        endGame = False
        if self.playerScore == 0:
            self.sendToClient(SEPARATOR)
            self.sendToClient("You did not get past the initial round, a true loser... Better luck next time")
            endGame = True
            self.sendToClient(SEPARATOR)
        else:
            self.sendToClient(SEPARATOR)
            self.sendToClient(f"Your current score is: {self.playerScore}")
            self.printBoard()
            self.sendToClient("Choose from the following options: ")
            self.sendToClient(f"1. Stay in the current spot. Score: {self.playerScore}")
            self.sendToClient(f"2. Move to spot #2. Score: {self.playerScore * 2}")
            self.sendToClient(f"3. Move to spot #4. Score: {int(self.playerScore / 2)}")
            self.sendToClient(SEPARATOR)
            userInput = self.userInputAndValidation(3)
            if userInput == 2:
                self.playerScore = self.playerScore * 2
                self.playerPos += -1
            if userInput == 3:
                self.playerScore = int(self.playerScore / 2)
                self.playerPos += 1
            self.sendToClient(SEPARATOR)
            self.printBoard()
        while not endGame:
            answer = self.Question()
            if answer:
                self.playerPos += 1

            chaserMove = self.randChaserMove()
            if chaserMove:
                self.sendToClient("The chaser answered the answer correctly, he moves 1 step closer!")
            else:
                self.sendToClient("The chaser answered wrong! Lucky you")
            self.sendToClient(SEPARATOR)
            if self.playerPos == self.chaserPos:
                endGame = True
                self.gameLoser()
                break
            if self.playerPos == LAST_STEP:
                endGame = True
                self.gameWinner()
                break
            self.printBoard()



questions = getQuestionJson()

# testGame = Game()
# testGame.initialRound()
# for _ in range(10):
#     self.sendToClient(SEPARATOR)
# #testGame.playerScore = 10000
# testGame.actualGame()

# clear screen
# Help wheel - done
# sockets - done
# multi user
# intro screen
