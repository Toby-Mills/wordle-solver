'''given an input dataset of legal guesses and possible answers run a game of wordle,
 receiving guesses, and returning a result for each guess'''
import string
import random
import pandas
import wordle_solver as ws

def update_game_state(game_state: pandas.DataFrame, guess:string, answer:string):
    '''update the supplied game_state with a new row for the result of the new guess'''
    new_row = []
    result = ['','','','','']

    #first find all the '+' hits
    for answer_position in [1,2,3,4,5]:
        letter = answer[answer_position - 1]
        if guess[answer_position - 1] == letter:
            result[answer_position - 1] = '+'

    #now find any remaining '~' hits
    for answer_position in [1,2,3,4,5]:
        letter = answer[answer_position - 1]
        if result[answer_position - 1] != '+':
            marked = False
            for guess_position in [1,2,3,4,5]:
                if marked is False and result[guess_position - 1] == '' \
                and guess[guess_position - 1] == letter:
                    result[guess_position - 1] = '~'
                    marked = True

    #now fill in '-' for any remaining guess positions
    for guess_position in [1,2,3,4,5]:
        if result[guess_position - 1] == '':
            result[guess_position - 1] = '-'

    for result_position in [1,2,3,4,5]:
        new_row.append(result[result_position -1] + guess[result_position - 1])

    game_state.loc[len(game_state.index)] = new_row

    return game_state

def main():
    '''Iterates over all valid answers in the csv file,
    and uses the WordleSolver to attempt to solve each puzzle.
    Prints out the stats for number of guesses '''

    print('running...')

    #initialise the results table
    results = pandas.DataFrame(columns = ['word', 'count'])

    #load every possible answer, and every valid guess
    all_valid_guesses = pandas.read_csv('All Valid Guesses.csv',names=['word'])
    all_possible_answers = pandas.read_csv('All Valid Answers.csv',names=['word'])

    #loop through random answers from the list, \
    # and use WordleSover to see how many guesses it takes to solve
    game_count = 0
    while game_count < 200:
        #start with a blank game state
        game_state = pandas.DataFrame(columns=['1','2','3','4','5'])
        completed = False
        #load the answer
        answer_number = random.randrange(0,all_possible_answers.shape[0] - 1)
        the_answer = all_possible_answers.iloc[answer_number]['word']
        #the_answer = answer['word']
        print(str(game_count + 1) + ': ' + the_answer)
        #keep asking WordleSover for its next guess until it is correct or it returns ''
        while completed is False:
            next_guess = ws.make_guess(all_valid_guesses, all_possible_answers, game_state)
            if next_guess != '':
                game_state = update_game_state(game_state, next_guess, the_answer)
                if next_guess == the_answer:
                    completed = True
                    results.loc[len(results.index)] = [the_answer, game_state.shape[0]]
            else:
                completed = True
                results.loc[len(results.index)] = [the_answer, -1]

        game_count += 1

    #Print out the final stats:
    for count in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        print(str(count) +':'+ str(results.loc[results['count'] == count].shape[0]))
    print(results['count'].describe())

    #Save the results to a csv file
    results.to_csv("results.csv")

if __name__ == '__main__':
    main()
