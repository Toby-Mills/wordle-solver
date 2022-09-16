'''given an input dataset of guesses and results so far, suggest the best next guess'''
import string
import random
import pandas

def split_words_into_letters(words:pandas.DataFrame):
    '''add 5 new columns 'letter_1 to letter_5
     populated with the individual letters of each value in the 'word' column'''
    for position in [1, 2, 3, 4, 5]:
        words['letter_' + str(position)] \
             = words['word'].str.slice(start = position - 1, stop = position)

    return words

def add_unique_letter_count(words:pandas.DataFrame, positions:list = None):
    '''adds a new columns 'unique_letter_count'
     populated with the number of unique letters for each value in the 'word' column'''
    if positions is None:
        positions = [1,2,3,4,5]
    words['unique_letter_count'] = words['word']\
        .apply(lambda word: (unique_letter_count(word, positions)))
    return words

def unique_letter_count(word:string, positions_to_use:list):
    '''returns the number of unique letters in the word, only checking the positions specified'''
    letters_in_positions = ''
    for position in positions_to_use:
        letters_in_positions += word[position - 1]

    return len(set(letters_in_positions))

def generate_letter_frequencies(words:pandas.DataFrame, positions:list = None):
    '''returns a new dataframe with a row per letter and a column per position, with a 'count' value
    of the total number of occurrences of that letter in that position, in the provided word list'''
    if positions is None:
        positions = [1, 2, 3, 4, 5]

    #generate a table of all lowercase letters of the alphabet
    all_letters = list(string.ascii_lowercase)
    letter_position_counts = pandas.DataFrame(all_letters)
    #set the first column to be named 'letter', and use as the index
    letter_position_counts.rename(columns={0: 'letter'},inplace = True)
    letter_position_counts.set_index('letter', inplace = True)
    #add a column called 'total'
    letter_position_counts['total'] = 0

    #loop through every remaining position
    for position in positions:
        #create a 'counts' a list to store the frequency of each letter in this position
        counts = []
        #loop through each letter
        for letter in all_letters:
            #find all words that have this letter in the current position
            word_filter = words['letter_' + str(position)] == letter
            words_with_letter = words.loc[word_filter]
            #record the number in the 'counts' list
            counts.append(words_with_letter.shape[0])

        #add a column for the current position counts
        letter_position_counts[str(position)] = counts
        #update the 'total' column with the counts for the current position
        letter_position_counts['total'] = letter_position_counts['total'] + counts

    #calculate an average frequency for each letter across all remaining positions
    letter_position_counts['average'] = letter_position_counts['total'] / len(positions)

    #add a count of words that have the letter in any unsolved position,
    # (counting one regardless of how many repeats of the letter the word has)
    counts = []
    for letter in all_letters:
        for position in positions:
            word_filter = words['word'].str.contains(letter)
        words_with_letter = words.loc[word_filter]
        counts.append(words_with_letter.shape[0])
    letter_position_counts['word_count'] = counts

    return letter_position_counts

def add_word_scores(words: pandas.DataFrame, letter_frequencies: pandas.DataFrame, \
    guesses_made: int, unsolved_positions:list):
    '''Adds a 'word_score' column with a calculated score for every word.
    The score is the sum of letter frequencies for each letter in the word
    multiply by the number of unique letters in the word / 5
    '''
    #add 'word_score' and 'word_average' columns to the word table
    words['word_score'] = 0
    words['word_average'] = 0

    #get individual letter scores for each unsolved position in each word
    #both the frequencies in the specific positions, \
    # and the average frequencies across all unsolved positions

    #get the count of remaining unsolved positons
    unsolved_position_count = len(unsolved_positions)
    #get the count of remaining possible answers
    possible_answer_count = words.loc[words['possible_answer'] == 1].shape[0]

    #loop through all the remaining unsolved positions
    for position in unsolved_positions:
        #join the words table to the letter frequencies table
        #where the letters match in the current position
        words = words.merge(\
            letter_frequencies[[str(position), 'average','word_count']], how = 'inner', \
                left_on = 'letter_' + str(position), right_on = 'letter')
        #add the frequency of the letter in the current position to the 'word_score'
        words['word_score'] = words['word_score'] + words[str(position)]

        #add the average frequency of the letter in all unsolved positions to the 'word_average'
        words['word_average'] = words['word_average'] + words['average']

        #G
        #add the count of words that have the letter (in any unsolved position)
        #words['word_score'] = words['word_score'] + (words['word_count'] / unsolved_position_count)

        #remove the 'average' & 'word_count' columns from the word table
        words = words.drop(columns=['average', 'word_count'])

    #A
    #add average letter frequency scores
    #words['word_score'] = words['word_score'] + words['word_average']

    #B
    #adjust for repeated letters (decreasing penalty with each guess for repeated letters)
    # * (1 - ((5 - guesses_made) / 5) * ((5 - words['unique_letter_count']) / 5))

    #C
    #adjust for guesses being possible answers
    # (increasing penalty with each guess for not being a valid answer)
    #words['word_score'] = words['word_score'] \
    # * (1 - ((guesses_made / 5) * (1 - words['possible_answer'])))

    #D
    #adjust for guesses being possible answers
    # (increasing penalty on non-answers with decreasing remaining answers)
    if possible_answer_count > 0:
        words['word_score'] = words['word_score'] \
            * (1 - (10 / (possible_answer_count))*(1 - words['possible_answer']))

    #H
    #no non-answer guesses allowed
    #if possible_answer_count > 0:
    #    if guesses_made >=2:
    #        words['word_score'] = words['word_score'] \
    #            *(words['possible_answer'])

    #E
    #adjust for repeated letters
    # (decreasing penalty with decreasing remaining answers)
    #words['word_score'] = words['word_score'] \
    # * (1 - (10 / (possible_answer_count))* ((5 - words['unique_letter_count']) / 5))

    #F
    #adjust for repeated letters
    # (decreasing penalty with each guess for repeated letters, unsolved positions only)
    words['word_score'] = words['word_score'] \
        * (1 - ((5 - guesses_made) / 5) \
            * ((unsolved_position_count - words['unique_letter_count']) / unsolved_position_count))

    return words

def list_posible_words(all_words:pandas.DataFrame, game_state:pandas.DataFrame):
    '''Filters the all_answers dataframe,
    removing any words that are disqualified by the game state'''
    possible_words = all_words

    for row in game_state.iterrows():
        guess = row[1]
        for position in [1, 2, 3, 4, 5]:
            column_name = 'letter_' + str(position)
            value = guess[position - 1]
            if isinstance(value, str):
                value = value.strip()
                letter = value[1:2]
                result = value[0:1]
                match(result):
                    case '+':
                        mask = possible_words[column_name] == letter
                        possible_words = possible_words[mask]
                    case '~':
                        mask = possible_words[column_name] == letter
                        possible_words = possible_words[~mask]
                    case '-':
                        mask = possible_words[column_name] == letter
                        possible_words = possible_words[~mask]

                positive_hits = count_positive_hits(guess, letter)
                negative_hits = count_negative_hits(guess, letter)

                if positive_hits > 0:
                    if negative_hits > 0:
                        mask = (possible_words['word'].str.count(letter) == positive_hits)
                    else:
                        mask = possible_words['word'].str.count(letter) >= positive_hits
                    possible_words = possible_words[mask]
                else:
                    mask = possible_words['word'].str.contains(letter)
                    possible_words = possible_words[~mask]

    return possible_words

def answer_contains_letter(guess:pandas.Series,letter:string):
    '''checks the result of a guess to determine if the answer contains a specific letter'''
    for position in [1, 2, 3, 4, 5]:
        if (guess[position - 1] == '+' + letter) or (guess[position - 1] == letter):
            return True
    return False

def count_positive_hits(guess:pandas.Series,letter:string):
    '''checks the result of a guess to determine how many of a specific letter \
        are known to be in the answer'''
    count = 0
    for position in [1, 2, 3, 4, 5]:
        if (guess[position - 1] == '+' + letter) or (guess[position - 1] == '~' + letter):
            count += 1
    return count

def count_negative_hits(guess:pandas.Series,letter:string):
    '''checks the result of a guess to determine how many \
        negative results were found for a specific letter'''
    count = 0
    for position in [1, 2, 3, 4, 5]:
        if guess[position - 1] == '-' + letter:
            count += 1
    return count

def flag_possible_answers(guesses:pandas.DataFrame, answers:pandas.DataFrame):
    '''Adds a boolean 'possible_answer' column to the guesses dataframe,
    to indicate that the word exists in the answers dataframe'''
    answers['possible_answer'] = 1
    guesses = guesses.merge(answers[['word','possible_answer']], how='left', on='word')
    guesses.loc[guesses['possible_answer'] != 1,'possible_answer'] = 0
    return guesses

def add_partial_match_operators(game_state:pandas.DataFrame):
    '''modify the guesses in the gamestate to include a ~ for any results that have no operator'''
    for position in [1,2,3,4,5]:
        game_state[str(position)] = game_state[str(position)].apply(add_partial_match_operator)
    return game_state

def add_partial_match_operator(result:string):
    '''prefixes the '~' operator to a result string that has no operator'''
    if isinstance(result, str) and len(result) == 1:
        return '~' + result
    return result

def list_unsolved_positions(game_state:pandas.DataFrame):
    '''return a list of positions that have not yet been solved'''
    positions = []
    guess_count = game_state.shape[0]
    if guess_count > 0:
        last_guess = game_state.iloc[guess_count-1]
        for position in [1, 2, 3, 4, 5]:
            value = last_guess[position - 1]
            if isinstance(value, str):
                value = value.strip()
                result = value[0:1]
                match(result):
                    case '+':
                        pass
                    case _:
                        positions.append(position)
            else:
                positions.append(position)
        return positions
    else:
        return [1, 2, 3, 4, 5]

def make_guess(all_valid_guesses:pandas.DataFrame, all_valid_answers:pandas.DataFrame, \
    game_state:pandas.DataFrame):
    ''' given a list of valid guesses, answers, and current game state, choose a next guess
    '''
    #game_state = pandas.read_csv('Wordle Game State.csv', names = '1 2 3 4 5'.split())
    game_state = add_partial_match_operators(game_state)

    guesses_made = game_state.shape[0]
    remaining_positions = list_unsolved_positions(game_state)

    #all_valid_guesses = pandas.read_csv('All Valid Guesses.csv',names=['word'])
    all_valid_guesses = split_words_into_letters(all_valid_guesses)
    all_valid_guesses = add_unique_letter_count(all_valid_guesses, remaining_positions)
    remaining_guesses = list_posible_words(all_valid_guesses, game_state)

    all_valid_answers = split_words_into_letters(all_valid_answers)
    remaining_answers = list_posible_words(all_valid_answers, game_state)

    letter_frequencies = generate_letter_frequencies(remaining_answers, remaining_positions)

    remaining_guesses = flag_possible_answers(remaining_guesses, all_valid_answers)
    remaining_guesses = add_word_scores(remaining_guesses, letter_frequencies, \
        guesses_made, remaining_positions)
    remaining_guesses.sort_values(by = 'word_score', ascending = False, inplace = True)
    if remaining_guesses.shape[0] > 0:
        best_score = remaining_guesses.iloc[0]['word_score']
        #add some randomness to the first guess
        if guesses_made == 0:
            best_score = best_score * 0.95
        best_guesses = remaining_guesses.loc[remaining_guesses['word_score'] >= best_score]
    else:
        return ''

    best_guess_count = best_guesses.shape[0]
    if best_guess_count == 1:
        chosen_guess = 0
    else:
        chosen_guess = random.randrange(0, best_guess_count)

    return best_guesses.iloc[chosen_guess]['word']

def main():
    '''load game state from a CSV file, and suggest the next guess to make'''

    #load every possible answer, and every valid guess
    all_valid_guesses = pandas.read_csv('All Valid Guesses.csv',names=['word'])
    all_possible_answers = pandas.read_csv('All Valid Answers.csv',names=['word'])
    #load the game state from csv file
    game_state = pandas.read_csv('Wordle Game State.csv', names = ['1','2','3','4','5'])

    next_guess = make_guess(all_valid_guesses, all_possible_answers,game_state)

    print('next guess: ' + next_guess)

if __name__ == '__main__':
    main()
