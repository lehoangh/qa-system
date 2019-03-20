from collections import namedtuple

# Conditions

Condition = namedtuple('Condition', ['target', 'operator', 'value'])

# Example 1: what is the most popular device type?
c1 = Condition(target="device_type", operator="max", value=None)
# Example 2: how many people use a blackberry?
c2 = Condition(target="device_type", operator="equals", value="blackberry")

Time = namedtuple('Time', ['operator', 'value'])

t1 = Time(operator="before", value="2018-09-19")


# Frames

class Frame:

    def __init__(self):
        # Possible question types are QUANTity, PERCentage, CATegory
        # People always inquire about their visitors.
        self.question_type = None
        self.date = None
        self.conditions = []

    def print_frame(self):
        return self.question_type, self.date, self.conditions

    def map_target_values(self):
        dicto = {}
        for condition in self.conditions:
            dicto[condition.target] = condition.value

        return dicto


# Frame Constructor
# Simple questions have a frame with one condition
# Complex questions have a single frame with several conditions
# Yes-no Questions are simple/complex questions that are wrapped in an assert

class FrameConstructor:

    def __init__(self, language):

        self.language == language
        if self.language == "en":
            self.condition_identifier = ConditionIdentifier(self.language)
            self.time_extractor = TimeExtractor(self.language)
        elif self.language == "nl":
            self.condition_identifier = ConditionIdentifier(self.language)
            self.time_extractor = TimeExtractor(self.language)
        else:
            raise ValueError("No FrameConstructor for language", language)

    def construct_frame(self, text):
        frame = Frame()

        condition = self.condition_identifier.get_condition(text)
        frame.conditions.append(condition)

        date = self.time_extractor.extract_date(text)
        frame.time = date
        return frame
