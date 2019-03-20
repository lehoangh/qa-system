import os
import time
import warnings
from answer_generation import generate_answer, read_answers_from_file
from frame import Condition, Frame
from get_date import get_date
from get_operator import find_operator, map_operator
from get_questiontype import get_questiontype
from get_target_and_value import identify_named_entities
from pipeline_picker import pipeline_picker
from postprocess import get_postprocess, connect_db
from modules.text import Text
from modules.trend_question_type import get_trend_result

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

db_v = connect_db()


def choose_pipeline(question):
    """making text object and doing preprocessing. all from Text file"""
    question = Text(question, "en")
    question.preprocess()
    pipeline = pipeline_picker(question.raw)

    if pipeline == "analytics":
        analytics(db_v, question)

    elif pipeline == "advice":
        advice(db_v, question)

    else:
        print("Pipeline selection failed.")


def analytics(db_v, question):
    answer_api = ""

    frame = Frame()
    """getting the question type"""
    frame.question_type = get_questiontype(question)
    # print("Question type:", frame.question_type)

    """getting the dates"""
    date_string, dates, _ = get_date(question.raw)
    frame.date = dates

    print("Date:", dates)
    print("Date string: ", date_string)

    """getting the target(s)"""
    model_path = os.path.join("..", "models/CRF_model_december.crfsuite")
    entities_default_value, entities = identify_named_entities(question,
                                                               model_path)
    print("Entities before value mapping: ", entities_default_value)
    print("Entities:", entities)

    """getting the condition value and operator"""
    found_operators = find_operator(question.raw)
    # print(found_operators)
    target2operator = {}
    try:
        for found_operator in found_operators:
            predicted_operator_dict = map_operator(question.raw,
                                                   found_operator, entities,
                                                   frame.question_type)
            print("predicted:", predicted_operator_dict)
            for found_target in predicted_operator_dict:
                target2operator[found_target] = predicted_operator_dict[
                    found_target]

    except TypeError:
        pass

    for target in entities:
        operator = target2operator.get(target)
        value = entities[target]
        condition = Condition(target=target, operator=operator, value=value)
        frame.conditions.append(condition)

    """printing the frame"""
    print("\n", frame.print_frame())

    """postprocess frame"""
    if frame.question_type in ['QUANTITY', 'PERC', 'yes/no', 'CATEGORY',
                               'AVERAGE', 'MEDIAN']:
        res, go_to_answer_generation = get_postprocess(db_v, question.raw,
                                                       entities_default_value,
                                                       frame)

    elif frame.question_type == 'COMPARISON':
        if len(frame.date) < 2:
            res, go_to_answer_generation = get_postprocess(db_v, question.raw,
                                                           entities_default_value,
                                                           frame)
        else:
            frame1, frame2 = Frame(), Frame()
            frame1.question_type, frame2.question_type = frame.question_type, frame.question_type
            frame1.date, frame2.date = [frame.date[0]], [frame.date[1]]
            frame1.conditions, frame2.conditions = frame.conditions, frame.conditions
            res1, go_to_answer_generation1 = get_postprocess(db_v, question.raw,
                                                             entities_default_value,
                                                             frame1)
            res2, go_to_answer_generation2 = get_postprocess(db_v, question.raw,
                                                             entities_default_value,
                                                             frame2)
            res = (res1, res2)
            go_to_answer_generation = (
            go_to_answer_generation1, go_to_answer_generation2)

    elif frame.question_type == "TREND":
        get_trend_result(frame, entities_default_value, question.raw)
        return

    else:
        print('Something went wrong with processing the question type.')

    """generating the answer"""
    if (isinstance(go_to_answer_generation, tuple) and (
            any(not i for i in go_to_answer_generation) or all(
        i for i in go_to_answer_generation))) or \
            (isinstance(go_to_answer_generation,
                        bool) and go_to_answer_generation):

        print(res)
        answers = read_answers_from_file()
        answer, memory = generate_answer(answers, frame, res, date_string,
                                         question.raw)

        if memory:
            trigger(memory, answer)
        else:
            print(answer)

    else:
        print(res)

    """ for front-end....probably not working perfectly
    if memory:
        obj = {
        'message': answer,
        'memory': memory}
        return obj
    else:
        obj = {'message': answer}
        return obj

    # return answer_api
    """


def trigger(memory, answer):
    if memory[0] == "full value list":
        print(answer)
        time.sleep(2)
        user_answer = input("Would you like to see the full list?\n")
        if user_answer.startswith("y"):
            time.sleep(2)
            print("Here you go... \n")
            time.sleep(1.5)
            print(memory[1])
            # answer_api += " " + memory
        else:
            print("Alright.")

    if memory[0] == "visittime period clarification":
        user_answer = input("Do you mean in total or per session?\n")
        if "session" in user_answer:
            time.sleep(2)
            print("Per session, they visited for", memory[1][1]['session'])
        elif "total" in user_answer:
            time.sleep(2)
            print("In total, they visited for", memory[1][0]['total'])


def advice(db_v, question):
    print('working on these questions')


if __name__ == "__main__":
    print("Hi my name is Ipa. Ask me something!")
    question = input()
    while question != 'no':
        choose_pipeline(question)
        # main(db_v, question)
        question = input("\n")

    # question = "what is the average visit time per visitor to my guests per session"
    # question = "what is the average pages per visitor to my guests per session"
    # question = "what is the average pages per visitor to my guests"

    # question = "is more users in september or october"
    # question = "overview monthly"
    # print("\n", question, "\n\n")
    # choose_pipeline(question)
