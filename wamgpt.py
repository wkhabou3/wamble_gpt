import os
import random
import numpy as np

# constants
# TODO: There are special combinations of characters like ellipsiseses. What's the best way to track these
punctuation = ['.', '!', '?']
punctuation_ignore = ['\"', '\'']
sentence_length = 4

# logistic function used to calculated whether a word should end a sentence in rollDiceEnder
# thanks desmos
# TODO: keep finetuning this function
def logistic_f(x):
    return 1/(1 + np.exp(-(x/sentence_length - 4))) * 0.88 + 0.12

# Decide which word to pick from markov model given weights of some current word.
def rollDice(word):
    sumWeights = weights[word]
    dice = random.random() * sumWeights
    for i in markovModel[word]:
        currWeight = markovModel[word][i]
        if currWeight > dice:
            return i
        else:
            dice -= currWeight

# Decide which word to pick from starter model given weights of all starter words.
def rollDiceStarter():
    dice = random.random() * starterWeight
    for i in sentenceStarters:
        currWeight = sentenceStarters[i]
        if currWeight > dice:
            return i
        else:
            dice -= currWeight

# Decide whether to pick word from ender model, then what punctuation to use (if picked) given weight and current sentence length.
def rollDiceEnder(word, sentenceLen):
    pickWeight = logistic_f(sentenceLen)
    dice = random.random()
    if (dice > pickWeight):
        return False, None
    sumWeights = enderWeights[word]
    dice = random.random() * sumWeights
    for i in sentenceEnders[word]:
        currWeight = sentenceEnders[word][i]
        if currWeight > dice:
            return True, i
        else:
            dice -= currWeight

# ask user for file input, store file content
allContent = []
# print('gimme a file')
# filename = input()
# while (filename != '-1'):
#    if not os.path.exists(filename):
#        print('yeah i dont see that one. Try again')
#        filename = input()
#        continue
#    fileContent = open(filename, "r").read()
#    allContent.append(fileContent)
#    print('Gimme another file or enter -1 to continue to wamble-gpt')
#    filename = input()

filename = 'test_files/independence.txt'
fileContent = open(filename, "r").read()
allContent.append(fileContent)

# split each file's text into words delimited by spaces
# TODO: generate POS tags for all words
allWords = []
for i in allContent:
    allWords.append(i.split())

del allContent

# remove unwanted punctuation, and sentence-ending punctuation sound be separate elements
allPunctuated = []
for i in allWords:
    currPunctuated = []
    for j in i:
        if j[-1] in punctuation_ignore:
            j = j[0:-1]
        if j[-1] in punctuation:
            currPunctuated.append(j[0:-1])
            currPunctuated.append(j[-1])
            continue
        currPunctuated.append(j)
    allPunctuated.append(currPunctuated)

del allWords

# Parse all words into Markov model, including sentence starters and enders
# TODO: Create Markov models for n-tuples of words (just start with 2-tuples for now)
markovModel = {}
sentenceStarters = {}
sentenceEnders = {}
weights = {}
starterWeight = 0
enderWeights = {}

# theres probably a better way to manage all these dict keys lol
for i in allPunctuated:
    for j in range(len(i) - 1):
        currWord = i[j]
        nextWord = i[j + 1]
        # Case 1: current word is a punctuation mark. Do nothing
        if currWord in punctuation:
            continue
        # Case 2: current word comes before a punctuation. Then:
        # - add word as a key of sentenceEnders. increase weight of corresponding punctuation by 1
        # - add 1 to total weight of all punctuation associated with the word
        elif nextWord in punctuation:
            if currWord in sentenceEnders:
                if nextWord in sentenceEnders[currWord]:
                    sentenceEnders[currWord][nextWord] += 1
                else:
                    sentenceEnders[currWord][nextWord] = 1
            else:
                sentenceEnders[currWord] = {nextWord: 1}
            if currWord in enderWeights:
                enderWeights[currWord] += 1
            else:
                enderWeights[currWord] = 1
            continue
        # Case 3: current word comes after punctuation. Then:
        # - add word as a key of sentenceStarters. Increase its weight by 1
        # - add 1 to sum total weight of all sentence starters
        elif i[j - 1] in punctuation:
            if currWord in sentenceStarters:
                sentenceStarters[currWord] += 1
            else:
                sentenceStarters[currWord] = 1
            starterWeight += 1
            currWord = currWord.lower()
        # For cases 2 and 3:
        # - add 1 to the weight of the word following curr
        # - add 1 to the sum total of all weights of words following curr
        if currWord in markovModel:
            if nextWord in markovModel[currWord]:
                markovModel[currWord][nextWord] += 1
            else:
                markovModel[currWord][nextWord] = 1
        else:
            markovModel[currWord] = {nextWord: 1}
        if currWord in weights:
            weights[currWord] += 1
        else:
            weights[currWord] = 1

# Use the dict to generate sentences with the following rules:
# When starting a sentence, roll dice to choose a word from sentenceStarters.
# If some word is a sentence ender, roll dice to decide whether to end the sentence there. Roll also influenced by current sentence length
# If for some reaosn word is not in the Markov model, just end the sentence.
# For all other words, roll dice to decide the next word using Markov model.
print('How many words you want')
numWords = int(input())
output = ''
currWordCount = 0
currWord = ''

for i in range(numWords):
    # Starting a sentence
    if currWordCount == 0:
        currWord = rollDiceStarter()
        output += ' ' + currWord
        currWordCount += 1
        currWord = currWord.lower()
        continue
    # Finding a sentence ender
    if currWord in sentenceEnders:
        endSentence, punctuation = rollDiceEnder(currWord, currWordCount)
        if (not endSentence) and (currWord in markovModel):
            currWord = rollDice(currWord)
            output += ' ' + currWord
        else:
            if (not punctuation):
                punctuation = '.'
            output += punctuation
            currWordCount = 0
        continue
    # alien :O
    if currWord not in markovModel:
        output += '.'
        currWordCount = 0
        continue
    # everything else
    currWord = rollDice(currWord)
    output += ' ' + currWord
    currWordCount += 1

print(output)
