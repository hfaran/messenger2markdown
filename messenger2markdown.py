#!/usr/bin/env python

import re
import string

import click
import clipboard


class Conversation(object):
    def __init__(self, time, monologues):
        self.time = time
        self.monologues = monologues

    def __str__(self):
        return "### {}\n{}".format(
            self.time,
            "\n".join("* {}".format(str(m)) for m in self.monologues)
        )


class Monologue(object):
    def __init__(self, author, messages):
        self.author = author
        self.messages = messages

    def __str__(self):
        return "{}\n{}".format(
            self.author,
            "\n".join("    * {}".format(str(m)) for m in self.messages)
        )


class MessengerParse(object):

    def __init__(self, text, my_name):
        self.lines = text.strip().splitlines()
        self.my_name = my_name
        self.names = {my_name}
        self.first_names = [my_name.split()[0]]
        self.index = 0

    @property
    def line(self):
        try:
            return self.lines[self.index]
        except IndexError:
            return None

    @property
    def next_line(self):
        try:
            return self.lines[self.index+1]
        except IndexError:
            return None

    def parse_text(self):
        conversations = []
        while self.index < len(self.lines):
            conversation = self.capture_conversation()
            conversations.append(conversation)
        return conversations

    def is_time(self):
        if self.line is None:
            return False

        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        time_regex = re.compile(r"^\d+:\d+(AM|PM)$")

        # Could have day and time
        if len(self.line.split()) == 2:
            day, time = self.line.strip().split()
            if day in days and time_regex.match(time):
                # Next line should be empty
                if self.next_line == "":
                    return True

        # Or only time
        if len(self.line.split()) == 1:
            time = self.line
            if time_regex.match(time):
                # Next line should be empty
                if self.next_line == "":
                    return True

        # Or a date
        date_regex = re.compile(r"^\w+ \d+(ND|TH), \d+:\d+(AM|PM)$")
        if date_regex.match(self.line):
            return True

        return False

    def capture_conversation(self):
        if self.is_time():
            time = self.line
            self.index += 2
        else:
            time = None
        monologues = self.capture_monologues()
        return Conversation(time, monologues)

    @staticmethod
    def is_full_name(s):
        return re.match(r"^\w+ \w+$", s)

    def peek_next_two_names(self):
        if self.line is None or self.next_line is None:
            return False
        # If author is me
        if self.line == self.my_name.split()[0]:
            return True
        # If author is someone else
        if (
            self.is_full_name(self.line) and
            self.next_line == self.line.split()[0]
        ):
            return True
        return False

    def capture_monologues(self):
        monologues = []
        while not self.is_time() and self.line is not None:
            monologues.append(self.capture_monologue())
        return monologues

    def _capture_name(self):
        # Handle the case where you are the one talking and there is only one
        #  name and not two
        if self.line == self.my_name.split()[0]:
            self.index += 1
            name = self.my_name
        else:
            if not self.is_full_name(self.line):
                return None
            if self.line not in self.names:
                self.names.add(self.line)
                self.first_names.append(self.line.split()[0])
            name = self.line
            self.index += 1
            assert self.line == name.split()[0], \
                "{} != {}".format(self.line, name.split()[0])
            self.index += 1

        return name

    def capture_monologue(self):
        name = self._capture_name()

        msgs = []
        while not self.peek_next_two_names() and not self.is_time() \
                and not self.line is None:
            msgs.append(self.line)
            self.index += 1

        return Monologue(name, msgs)


@click.command()
@click.option("--debug", is_flag=True)
def main(debug):
    raw_input("Copy the conversation you want to parse to clipboard, then "
              "press RETURN to continue...")
    my_name = raw_input("What is your full name in the Facebook "
                        "conversation? ")
    text = filter(lambda x: x in string.printable,
                  clipboard.paste().strip())
    if debug:
        print("Parsing the following conversation:\n<<=====>>{}\n<<=====>>"
            .format(text))
    mp = MessengerParse(text, my_name)

    if debug:
        try:
            conversations = mp.parse_text()
        except:
            print mp.lines[:mp.index+1]
            raise
    else:
        conversations = mp.parse_text()

    for c in conversations:
        print("\n")
        print(c)


if __name__ == "__main__":
    main()
